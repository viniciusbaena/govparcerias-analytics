#!/usr/bin/env python3
"""Auditoria determinística da release publicada, sem chamadas externas."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MISSING='Não informado pela fonte'
def load(path): return json.loads(path.read_text(encoding='utf-8'))
def main():
  portfolio=load(ROOT/'site/data/municipalities.json'); municipalities=portfolio['municipalities']
  integrated=load(ROOT/'site/data/integrated.json'); status=load(ROOT/'data/published/integrated_status.json')
  errors=[]
  if len(municipalities)!=121 or portfolio['manifest'].get('record_count')!=121: errors.append('carteira não contém exatamente 121 municípios')
  if integrated.get('policy')!='official_only': errors.append('política official_only ausente')
  for key,value in integrated.get('counts',{}).items():
    if isinstance(value,int) and value<0: errors.append(f'contagem negativa: {key}')
  documented_ambiguities={'physical_execution','feasibility_studies'}
  partial=[]
  for entity,info in integrated.get('sync_status',{}).items():
    if isinstance(info,dict) and info.get('completed') is False:
      (partial if entity in documented_ambiguities else errors).append(entity)
  integrity=integrated.get('integrity',{})
  for rule in integrity.get('rules',[]):
    if rule.get('violations',0)!=0: errors.append(f"violação de integridade: {rule.get('id')}")
  report={'status':'passed' if not errors else 'failed','municipalities':len(municipalities),'counts':integrated.get('counts',{}),'sync_status':integrated.get('sync_status',{}),'integrity':integrity,'documented_ambiguities':partial,'errors':errors}
  out=ROOT/'data/published/release_audit.json'; out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
  print(json.dumps({'status':report['status'],'municipalities':len(municipalities),'errors':errors},ensure_ascii=False,indent=2))
  raise SystemExit(1 if errors else 0)
if __name__=='__main__': main()
