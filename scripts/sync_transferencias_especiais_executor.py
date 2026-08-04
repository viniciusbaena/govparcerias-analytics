#!/usr/bin/env python3
"""Sincroniza finalidades e metas relacionadas aos executores oficiais."""
from __future__ import annotations
import argparse, asyncio, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend'))
from app.connectors.transferegov import TransferegovConnector
BASE='https://api.transferegov.gestao.gov.br/transferenciasespeciais'
SPECS={'purposes':('finalidade_especial','id_executor','id_executor'),'goals':('meta_especial','id_executor','id_meta')}
def read(p,f): return json.loads(p.read_text(encoding='utf-8')) if p.exists() else f
def write(p,v): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def rows(x): return x if isinstance(x,list) else next((x[k] for k in ('data','items','content') if isinstance(x,dict) and isinstance(x.get(k),list)),[])
async def sync(limit=1000):
  roots=sorted({str(x['id_executor']) for x in read(ROOT/'data/published/transferegov/special_executors.json',[]) if x.get('id_executor') is not None}); c=TransferegovConnector(ROOT/'data/raw/transferegov/special_executor_graph',min_delay=.35); result={}; errors=[]
  for entity,(endpoint,parent,key) in SPECS.items():
    out={}
    for start in range(0,len(roots),50):
      batch=roots[start:start+50]
      try:
        r=await c.get_json(f'{BASE}/{endpoint}',{parent:f'in.({",".join(batch)})','limit':limit,'offset':0})
        for row in rows(r.payload):
          official=row.get(key)
          if official is not None: out[str(official)]={'source':'Transferegov - Transferências Especiais','source_record_id':str(official),**row,'source_url':r.url,'fetched_at':r.fetched_at,'sha256':r.sha256}
      except Exception as exc: errors.append({'entity':entity,'batch':batch,'error':str(exc)})
    write(ROOT/f'data/published/transferegov/special_{entity}.json',list(out.values())); write(ROOT/f'data/published/transferegov/special_{entity}_sync_status.json',{'completed':not any(e['entity']==entity for e in errors),'roots_total':len(roots)}); result[entity]={'records':len(out),'errors':sum(e['entity']==entity for e in errors)}
  status={'roots':len(roots),'entities':result,'errors':errors,'status':'completed' if not errors else 'partial'}; write(ROOT/'data/published/transferegov/special_executor_graph.status.json',status); return status
if __name__=='__main__':
  p=argparse.ArgumentParser(); p.add_argument('--limit',type=int,default=1000); print(json.dumps(asyncio.run(sync(p.parse_args().limit)),ensure_ascii=False,indent=2))
