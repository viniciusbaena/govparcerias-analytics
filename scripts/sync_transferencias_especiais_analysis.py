#!/usr/bin/env python3
"""Sincroniza análises oficiais ligadas aos planos de trabalho de Transferências Especiais."""
from __future__ import annotations
import argparse, asyncio, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend'))
from app.connectors.transferegov import TransferegovConnector
BASE='https://api.transferegov.gestao.gov.br/transferenciasespeciais'
SPECS={'work_plan_analyses':('plano_trabalho_analise_especial','id_plano_trabalho_analise','id_plano_trabalho'),'pending_organs':('orgao_analise_pendente_especial','id_analise_pendente','id_plano_trabalho')}
def read(p,f): return json.loads(p.read_text(encoding='utf-8')) if p.exists() else f
def write(p,v): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def rows(x): return x if isinstance(x,list) else next((x[k] for k in ('data','items','content') if isinstance(x,dict) and isinstance(x.get(k),list)),[])
async def sync(limit=1000):
  roots=read(ROOT/'data/published/transferegov/special_work_plans.json',[]); ids=sorted({str(x['id_plano_trabalho']) for x in roots if x.get('id_plano_trabalho') is not None})
  c=TransferegovConnector(ROOT/'data/raw/transferegov/special_action_analysis',min_delay=.35); errors=[]; result={}
  for entity,(endpoint,key,parent_key) in SPECS.items():
    out=ROOT/f'data/published/transferegov/special_{entity}.json'; existing={str(x['source_record_id']):x for x in read(out,[]) if x.get('source_record_id')}
    for start in range(0,len(ids),50):
      batch_ids=ids[start:start+50]; offset=0
      try:
        while True:
          r=await c.get_json(f'{BASE}/{endpoint}',{'id_plano_trabalho':f'in.({",".join(batch_ids)})','limit':limit,'offset':offset}); batch=rows(r.payload)
          for row in batch:
            if row.get(key) is None: raise ValueError(f'registro sem {key}')
            existing[str(row[key])]={'source':'Transferegov - Transferências Especiais','source_record_id':str(row[key]),'id_plano_trabalho':row.get(parent_key),**row,'source_url':r.url,'fetched_at':r.fetched_at,'sha256':r.sha256}
          if len(batch)<limit: break
          offset+=limit
      except Exception as exc: errors.append({'entity':entity,'id_plano_trabalho':','.join(batch_ids),'error':str(exc)})
    write(out,list(existing.values())); result[entity]={'records':len(existing),'errors':sum(e['entity']==entity for e in errors)}
    write(ROOT/f'data/published/transferegov/special_{entity}_sync_status.json',{'completed':result[entity]['errors']==0,'roots_total':len(ids)})
    write(ROOT/f'data/published/transferegov/special_{entity}_errors.json',[e for e in errors if e['entity']==entity])
  write(ROOT/'data/published/transferegov/special_analysis.status.json',{'work_plans':len(ids),'entities':result,'errors':errors,'status':'completed' if not errors else 'partial'}); return result
if __name__=='__main__':
  p=argparse.ArgumentParser(); p.add_argument('--limit',type=int,default=1000); a=p.parse_args(); print(json.dumps(asyncio.run(sync(a.limit)),ensure_ascii=False,indent=2))
