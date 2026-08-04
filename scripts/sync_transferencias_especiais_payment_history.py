#!/usr/bin/env python3
"""Sincroniza histórico oficial de situação das ordens de pagamento especiais."""
from __future__ import annotations
import argparse, asyncio, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend'))
from app.connectors.transferegov import TransferegovConnector
BASE='https://api.transferegov.gestao.gov.br/transferenciasespeciais'
def read(p,f): return json.loads(p.read_text(encoding='utf-8')) if p.exists() else f
def write(p,v): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def rows(x): return x if isinstance(x,list) else next((x[k] for k in ('data','items','content') if isinstance(x,dict) and isinstance(x.get(k),list)),[])
async def sync(limit=1000):
  orders=read(ROOT/'data/published/transferegov/special_orders.json',[]); ids=sorted({str(x['id_op_ob']) for x in orders if x.get('id_op_ob') is not None})
  c=TransferegovConnector(ROOT/'data/raw/transferegov/special_payment_history',min_delay=.35); existing={}; errors=[]
  for start in range(0,len(ids),50):
    batch=ids[start:start+50]; offset=0
    try:
      while True:
        r=await c.get_json(f'{BASE}/historico_pagamento_especial',{'id_op_ob':f'in.({",".join(batch)})','limit':limit,'offset':offset}); part=rows(r.payload)
        for row in part:
          key=row.get('id_historico_op_ob')
          if key is None: raise ValueError('histórico sem id_historico_op_ob')
          existing[str(key)]={'source':'Transferegov - Transferências Especiais','source_record_id':str(key),'id_op_ob':row.get('id_op_ob'),**row,'source_url':r.url,'fetched_at':r.fetched_at,'sha256':r.sha256}
        if len(part)<limit: break
        offset+=limit
    except Exception as exc: errors.append({'id_op_ob':','.join(batch),'error':str(exc)})
  write(ROOT/'data/published/transferegov/special_payment_history.json',list(existing.values()))
  write(ROOT/'data/published/transferegov/special_payment_history_sync_status.json',{'completed':not errors,'roots_total':len(ids),'records':len(existing)})
  write(ROOT/'data/published/transferegov/special_payment_history_errors.json',errors)
  status={'orders':len(ids),'records':len(existing),'errors':errors,'status':'completed' if not errors else 'partial'}; write(ROOT/'data/published/transferegov/special_payment_history.status.json',status); return status
if __name__=='__main__':
  p=argparse.ArgumentParser(); p.add_argument('--limit',type=int,default=1000); print(json.dumps(asyncio.run(sync(p.parse_args().limit)),ensure_ascii=False,indent=2))
