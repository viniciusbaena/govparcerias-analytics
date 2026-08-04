#!/usr/bin/env python3
"""Percorre relações oficiais de Transferências Especiais por id_plano_acao."""
from __future__ import annotations
import argparse, asyncio, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend'))
from app.connectors.transferegov import TransferegovConnector
BASE='https://api.transferegov.gestao.gov.br/transferenciasespeciais'
SPECS={'executors':('executor_especial','id_executor'),'work_plans':('plano_trabalho_especial','id_plano_trabalho'),'commitments':('empenho_especial','id_empenho')}
def read(p,f): return json.loads(p.read_text(encoding='utf-8')) if p.exists() else f
def write(p,v): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def rows(x): return x if isinstance(x,list) else next((x[k] for k in ('data','items','content') if isinstance(x,dict) and isinstance(x.get(k),list)),[])
async def sync(limit=1000,max_plans=None):
  plans=read(ROOT/'data/published/transferegov/special_action_plans.json',[]); ids=sorted({str(x['id_plano_acao']) for x in plans if x.get('id_plano_acao') is not None}); ids=ids[:max_plans] if max_plans else ids
  connector=TransferegovConnector(ROOT/'data/raw/transferegov/special_action_graph',min_delay=.35); result={}; errors=[]
  for entity,(endpoint,key) in SPECS.items():
    out=ROOT/f'data/published/transferegov/special_{entity}.json'; existing={str(x['source_record_id']):x for x in read(out,[]) if x.get('source_record_id')}
    for plan_id in ids:
      offset=0
      try:
        while True:
          response=await connector.get_json(f'{BASE}/{endpoint}',{'id_plano_acao':f'eq.{plan_id}','limit':limit,'offset':offset})
          batch=rows(response.payload)
          for row in batch:
            official=row.get(key)
            if official is None: raise ValueError(f'registro sem {key}')
            existing[str(official)]={'source':'Transferegov - Transferências Especiais','source_record_id':str(official),'id_plano_acao':plan_id,**row,'source_url':response.url,'fetched_at':response.fetched_at,'sha256':response.sha256}
          if len(batch)<limit: break
          offset+=limit
      except Exception as exc: errors.append({'entity':entity,'id_plano_acao':plan_id,'error':str(exc)})
    write(out,list(existing.values())); result[entity]={'records':len(existing),'errors':sum(1 for e in errors if e['entity']==entity)}
  write(ROOT/'data/published/transferegov/special_graph.status.json',{'plans':len(ids),'entities':result,'errors':errors,'status':'completed' if not errors else 'partial'})
  return result
if __name__=='__main__':
  p=argparse.ArgumentParser(); p.add_argument('--limit',type=int,default=1000); p.add_argument('--max-plans',type=int); a=p.parse_args(); print(json.dumps(asyncio.run(sync(a.limit,a.max_plans)),ensure_ascii=False,indent=2))
