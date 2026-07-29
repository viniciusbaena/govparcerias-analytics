#!/usr/bin/env python3
from __future__ import annotations
import argparse,asyncio,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend'))
from app.connectors.ibge import IBGEConnector
from app.connectors.base import PublicApiConnector
async def discover_openapi(name,base,raw_dir):
    c=PublicApiConnector(name,base,raw_dir); errors=[]
    for path in ('openapi.json','api/openapi.json','v3/api-docs','swagger/v1/swagger.json'):
        try:
            r=await c.get(path); return {"source":name,"base_url":base,"openapi_path":path,"sha256":r.sha256,"paths":sorted(r.payload.get('paths',{}).keys())}
        except Exception as exc: errors.append(f"{path}: {type(exc).__name__}")
    return {"source":name,"base_url":base,"status":"Não informado pela fonte","errors":errors}
async def main(args):
    portfolio=json.loads((ROOT/'site/data/municipalities.json').read_text(encoding='utf-8')); municipalities=portfolio.get('municipalities',[])
    raw_dir=str(ROOT/'data/raw'); published=ROOT/'data/published'; published.mkdir(parents=True,exist_ok=True)
    enriched=[]; ibge=IBGEConnector(raw_dir)
    if not args.skip_ibge:
        for i,m in enumerate(municipalities,1):
            try:
                r=await ibge.municipality(str(m['ibge_code'])); p=r.payload; micro=p.get('microrregiao') or {}; meso=micro.get('mesorregiao') or {}; uf=meso.get('UF') or {}; immediate=p.get('regiao-imediata') or {}; intermediate=immediate.get('regiao-intermediaria') or {}
                enriched.append({"ibge_code":str(m['ibge_code']),"official_name":p.get('nome'),"microregion":micro.get('nome'),"mesoregion":meso.get('nome'),"immediate_region":immediate.get('nome'),"intermediate_region":intermediate.get('nome'),"uf":uf.get('sigla'),"source_url":r.url,"fetched_at":r.fetched_at,"sha256":r.sha256})
                print(f"IBGE {i}/{len(municipalities)} {m['name']}")
            except Exception as exc: enriched.append({"ibge_code":str(m['ibge_code']),"error":type(exc).__name__,"message":"Não informado pela fonte"})
    (published/'municipalities_enriched.json').write_text(json.dumps(enriched,ensure_ascii=False,indent=2),encoding='utf-8')
    catalogs=[]
    for name,base in [('transferegov','https://api-publica.transferegov.gestao.gov.br'),('obrasgov','https://api-publica.obrasgov.gestao.gov.br')]: catalogs.append(await discover_openapi(name,base,raw_dir))
    (published/'connector_catalogs.json').write_text(json.dumps(catalogs,ensure_ascii=False,indent=2),encoding='utf-8')
    contracts=json.loads((published/'contracts.json').read_text()) if (published/'contracts.json').exists() else []
    status={"finished_at":datetime.now(timezone.utc).isoformat(),"municipalities_total":len(municipalities),"municipalities_enriched":sum(1 for x in enriched if not x.get('error')),"contracts":len(contracts),"policy":"official_only"}
    (published/'sync_status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(status,ensure_ascii=False,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--skip-ibge',action='store_true'); asyncio.run(main(p.parse_args()))
