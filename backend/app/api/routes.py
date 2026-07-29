from fastapi import APIRouter, Query, HTTPException
from app.services.demo_repository import load_demo

router=APIRouter()

@router.get("/health")
async def health(): return {"status":"ok","service":"govparcerias-api","version":"0.4.0-alpha"}

@router.get("/meta")
async def meta(): return {"version":"0.4.0-alpha","data_mode":"demonstration","authentication":False}

@router.get("/municipios")
async def municipios(q: str | None=None, status: str | None=None):
    items=load_demo()["municipios"]
    if q: items=[x for x in items if q.casefold() in (x["nome"]+x["ibge"]).casefold()]
    if status: items=[x for x in items if x["status"]==status]
    return {"items":items,"count":len(items)}

@router.get("/municipios/{ibge}")
async def municipio(ibge: str):
    data=load_demo(); item=next((x for x in data["municipios"] if x["ibge"]==ibge),None)
    if not item: raise HTTPException(404,"Município não encontrado")
    return {**item,"instrumentos":[x for x in data["parcerias"] if x["municipio"]==item["nome"]]}

@router.get("/parcerias")
async def parcerias(q: str | None=None, situacao: str | None=None, tema: str | None=None, limit: int=Query(100,ge=1,le=1000)):
    items=load_demo()["parcerias"]
    if q: items=[x for x in items if q.casefold() in " ".join(map(str,x.values())).casefold()]
    if situacao: items=[x for x in items if x["situacao"]==situacao]
    if tema: items=[x for x in items if x["tema"]==tema]
    return {"items":items[:limit],"count":len(items)}

@router.get("/indicadores/resumo")
async def resumo():
    d=load_demo(); ms=d["municipios"]
    return {"municipios":len(ms),"parcerias":sum(x["parcerias"] for x in ms),"valor_global":sum(x["valor"] for x in ms),"vigencias_proximas":sum(x["vigencias"] for x in ms),"updated_at":d["updated_at"]}
