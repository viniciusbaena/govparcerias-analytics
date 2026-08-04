#!/usr/bin/env python3
"""Sincroniza documentos hábeis e ordens bancárias por IDs oficiais."""
from __future__ import annotations
import argparse, asyncio, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend'))
from app.connectors.transferegov import TransferegovConnector
BASE='https://api.transferegov.gestao.gov.br/transferenciasespeciais'
def read(p,f): return json.loads(p.read_text(encoding='utf-8')) if p.exists() else f
def write(p,v): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def rows(x): return x if isinstance(x,list) else next((x[k] for k in ('data','items','content') if isinstance(x,dict) and isinstance(x.get(k),list)),[])
async def fetch(connector,endpoint,param,ids,limit):
  out=[]
  for start in range(0,len(ids),50):
    batch=ids[start:start+50]; offset=0
    while True:
      response=await connector.get_json(f'{BASE}/{endpoint}',{param:f'in.({",".join(batch)})','limit':limit,'offset':offset}); part=rows(response.payload)
      out.extend((row,response) for row in part)
      if len(part)<limit: break
      offset+=limit
  return out
async def sync(limit=1000):
  connector=TransferegovConnector(ROOT/'data/raw/transferegov/special_finance',min_delay=.35); errors=[]
  commitments=read(ROOT/'data/published/transferegov/special_commitments.json',[]); commitment_ids=sorted({str(x['id_empenho']) for x in commitments if x.get('id_empenho') is not None})
  documents={}
  try:
    for row,response in await fetch(connector,'documento_habil_especial','id_empenho',commitment_ids,limit):
      key=row.get('id_dh')
      if key is None: raise ValueError('documento sem id_dh')
      documents[str(key)]={'source':'Transferegov - Transferências Especiais','source_record_id':str(key),**row,'source_url':response.url,'fetched_at':response.fetched_at,'sha256':response.sha256}
  except Exception as exc: errors.append({'entity':'documents','error':str(exc)})
  write(ROOT/'data/published/transferegov/special_documents.json',list(documents.values()))
  write(ROOT/'data/published/transferegov/special_documents_sync_status.json',{'completed':not errors,'roots_total':len(commitment_ids)})
  write(ROOT/'data/published/transferegov/special_documents_errors.json',[e for e in errors if e.get('entity')=='documents'])
  document_ids=sorted(documents)
  orders={}
  try:
    for row,response in await fetch(connector,'ordem_pagamento_ordem_bancaria_especial','id_dh',document_ids,limit):
      key=row.get('id_op_ob')
      if key is None: raise ValueError('ordem sem id_op_ob')
      orders[str(key)]={'source':'Transferegov - Transferências Especiais','source_record_id':str(key),**row,'source_url':response.url,'fetched_at':response.fetched_at,'sha256':response.sha256}
  except Exception as exc: errors.append({'entity':'orders','error':str(exc)})
  write(ROOT/'data/published/transferegov/special_orders.json',list(orders.values()))
  write(ROOT/'data/published/transferegov/special_orders_sync_status.json',{'completed':not errors,'roots_total':len(document_ids)})
  write(ROOT/'data/published/transferegov/special_orders_errors.json',[e for e in errors if e.get('entity')=='orders'])
  status={'commitments':len(commitment_ids),'documents':len(documents),'orders':len(orders),'errors':errors,'status':'completed' if not errors else 'partial'}
  write(ROOT/'data/published/transferegov/special_finance.status.json',status); return status
if __name__=='__main__':
  p=argparse.ArgumentParser(); p.add_argument('--limit',type=int,default=1000); print(json.dumps(asyncio.run(sync(p.parse_args().limit)),ensure_ascii=False,indent=2))
