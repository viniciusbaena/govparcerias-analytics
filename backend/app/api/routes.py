from fastapi import APIRouter, HTTPException, Query
from app.services.query_planner import plan
from app.services.sync_engine import compare_records

router=APIRouter()

EMPTY={"items":[],"count":0,"data_mode":"official_only","message":"Nenhum dado oficial sincronizado."}

@router.get('/health')
async def health(): return {"status":"ok","service":"govparcerias-api","version":"0.7.0-alpha"}

@router.get('/meta')
async def meta(): return {"version":"0.7.0-alpha","data_mode":"official_only","authentication":False,"synthetic_data":False}

@router.get('/municipios')
async def municipios(q:str|None=None,status:str|None=None): return EMPTY

@router.get('/municipios/{ibge}')
async def municipio(ibge:str): raise HTTPException(404,"Município não localizado na base oficial sincronizada")

@router.get('/parcerias')
async def parcerias(q:str|None=None,situacao:str|None=None,tema:str|None=None,limit:int=Query(100,ge=1,le=1000)): return EMPTY

@router.get('/parcerias/{numero}/dossie')
async def dossier(numero:str):
    raise HTTPException(404,"Instrumento não localizado na base oficial sincronizada")

@router.get('/parcerias/{numero}/financeiro')
async def financial(numero:str): return {**EMPTY,"instrumento":numero,"sections":["resumo","emendas","empenhos","documentos_habeis","ordens_pagamento","contas","extratos","plano_trabalho"]}

@router.get('/parcerias/{numero}/engenharia')
async def engineering(numero:str): return {**EMPTY,"instrumento":numero,"sections":["obras","documentos_tecnicos","vistorias","medicoes","licitacoes","contratos_execucao","recebimentos"]}

@router.get('/parcerias/{numero}/documentos')
async def documents(numero:str): return {**EMPTY,"instrumento":numero}

@router.get('/indicadores/resumo')
async def resumo(): return {"municipios":0,"parcerias":0,"valor_global":None,"vigencias_proximas":0,"updated_at":None,"data_mode":"official_only"}

@router.get('/alertas')
async def alertas(): return EMPTY

@router.get('/assistente/plano')
async def assistant_plan(q:str=Query(min_length=2,max_length=500)):
    p=plan(q);return {"intent":p.intent,"filters":p.filters,"explanation":p.explanation,"execution":"blocked_without_official_evidence"}

@router.post('/sincronizacao/comparar')
async def compare_snapshots(before:list[dict],after:list[dict],entity:str='parceria',key_field:str='numero'):
    return {"changes":compare_records(entity,key_field,before,after)}

@router.get('/qualidade')
async def quality(): return {"rules":[],"data_mode":"official_only","message":"Sem dados oficiais para auditar."}
