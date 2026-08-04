#!/usr/bin/env python3
"""Sincroniza PVLs do SADIPEM somente para os 121 códigos IBGE da carteira."""
from __future__ import annotations
import argparse, asyncio, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend'))
from app.connectors.transferegov import TransferegovConnector
BASE='https://apidatalake.tesouro.gov.br/ords/cdwhprd/sadipem/tt'
def read(p,f): return json.loads(p.read_text(encoding='utf-8')) if p.exists() else f
def write(p,v): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
async def sync(limit=500):
  municipalities=read(ROOT/'site/data/municipalities.json',{}).get('municipalities',[]); ibges=[str(x['ibge_code']) for x in municipalities]
  c=TransferegovConnector(ROOT/'data/raw/sadipem',min_delay=1.0); records={}; errors=[]
  for municipality,ibge in zip(municipalities,ibges):
    offset=0
    try:
      while True:
        r=await c.get_json(f'{BASE}/pvl',{'id_ente':ibge,'limit':limit,'offset':offset}); payload=r.payload; rows=payload.get('items',[]) if isinstance(payload,dict) else []
        for row in rows:
          key=row.get('id_pleito')
          if key is None: raise ValueError('PVL sem id_pleito')
          if str(row.get('cod_ibge'))!=ibge: raise ValueError(f'ente retornado divergente: {row.get("cod_ibge")}')
          records[str(key)]={'source':'SADIPEM - Tesouro Nacional','source_record_id':str(key),'municipality_name':municipality['name'],'municipality_cnpj':municipality['cnpj'],'ibge_code':ibge,**row,'source_url':r.url,'fetched_at':r.fetched_at,'sha256':r.sha256}
        has_more=bool(payload.get('hasMore')) if isinstance(payload,dict) else False
        if not has_more or not rows: break
        offset+=limit
    except Exception as exc: errors.append({'municipality':municipality['name'],'ibge_code':ibge,'error':str(exc)})
  write(ROOT/'data/published/sadipem_pvls.json',list(records.values())); write(ROOT/'data/published/sadipem_pvls_errors.json',errors)
  status={'records':len(records),'municipalities':len(ibges),'errors':errors,'completed':not errors,'territory_filter':'id_ente','policy':'official_only'}; write(ROOT/'data/published/sadipem_pvls_sync_status.json',status); return status
if __name__=='__main__':
  p=argparse.ArgumentParser(); p.add_argument('--limit',type=int,default=500); print(json.dumps(asyncio.run(sync(p.parse_args().limit)),ensure_ascii=False,indent=2))
