from pathlib import Path
import json
from fastapi import APIRouter, HTTPException, Query
from app.connectors.catalog import CONNECTORS
from app.services.query_planner import plan
from app.services.sync_engine import compare_records
router=APIRouter()
PROJECT=Path(__file__).resolve().parents[3]
MUNICIPALITIES=PROJECT/'site'/'data'/'municipalities.json'
PUBLISHED=PROJECT/'data'/'published'
def load_json(path,default):
    try:return json.loads(Path(path).read_text(encoding='utf-8'))
    except FileNotFoundError:return default
def municipalities_data():
    raw=load_json(MUNICIPALITIES,{"municipalities":[]}); return raw.get('municipalities',raw if isinstance(raw,list) else [])
def published(name): return load_json(PUBLISHED/f'{name}.json',[])
@router.get('/health')
async def health(): return {"status":"ok","service":"govparcerias-api","version":"1.0.0-alpha"}
@router.get('/meta')
async def meta(): return {"version":"1.0.0-alpha","data_mode":"official_only","authentication":False,"synthetic_data":False}
@router.get('/conectores')
async def connectors(): return {"items":[c.__dict__ for c in CONNECTORS],"count":len(CONNECTORS)}
@router.get('/municipios')
async def municipios(q:str|None=None):
    items=municipalities_data(); term=(q or '').casefold().strip()
    if term: items=[m for m in items if term in ' '.join(str(m.get(k,'')) for k in ('name','cnpj','ibge_code')).casefold()]
    enrichment={str(x.get('ibge_code')):x for x in published('municipalities_enriched')}
    out=[{**m,"official_enrichment":enrichment.get(str(m.get('ibge_code')))} for m in items]
    return {"items":out,"count":len(out),"data_mode":"official_only"}
@router.get('/municipios/{ibge}')
async def municipio(ibge:str):
    item=next((m for m in municipalities_data() if str(m.get('ibge_code'))==ibge),None)
    if not item: raise HTTPException(404,"Município não localizado na carteira")
    enrichment=next((x for x in published('municipalities_enriched') if str(x.get('ibge_code'))==ibge),None)
    contracts=[x for x in published('contracts') if str(x.get('ibge_code'))==ibge or x.get('municipality_cnpj')==item.get('cnpj')]
    return {**item,"official_enrichment":enrichment,"contracts":contracts,"contract_count":len(contracts),"data_mode":"official_only"}
@router.get('/contratos')
async def contratos(q:str|None=None,limit:int=Query(100,ge=1,le=1000)):
    items=published('contracts'); term=(q or '').casefold().strip()
    if term: items=[x for x in items if term in json.dumps(x,ensure_ascii=False).casefold()]
    return {"items":items[:limit],"count":len(items),"data_mode":"official_only","message":None if items else "Nenhum contrato oficial sincronizado."}
@router.get('/contratos/{numero}')
async def contrato(numero:str):
    item=next((x for x in published('contracts') if str(x.get('numero') or x.get('number'))==numero),None)
    if not item: raise HTTPException(404,"Contrato não localizado na base oficial sincronizada")
    return item
@router.get('/parcerias')
async def parcerias(q:str|None=None,limit:int=Query(100,ge=1,le=1000)): return await contratos(q,limit)
@router.get('/indicadores/resumo')
async def resumo():
    contracts=published('contracts'); status=load_json(PUBLISHED/'sync_status.json',{})
    return {"municipios":len(municipalities_data()),"contratos":len(contracts),"updated_at":status.get('finished_at'),"data_mode":"official_only"}
@router.get('/assistente/plano')
async def assistant_plan(q:str=Query(min_length=2,max_length=500)):
    p=plan(q); return {"intent":p.intent,"filters":p.filters,"explanation":p.explanation,"execution":"requires_official_evidence"}
@router.post('/sincronizacao/comparar')
async def compare_snapshots(before:list[dict],after:list[dict],entity:str='parceria',key_field:str='numero'): return {"changes":compare_records(entity,key_field,before,after)}
