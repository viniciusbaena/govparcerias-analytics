from __future__ import annotations
import argparse, csv, json
from pathlib import Path

ALIASES={"nome":"municipio","cidade":"municipio","ibge":"codigo_ibge"}

def normalize(row: dict[str,str]) -> dict[str,str]:
    clean={ALIASES.get(k.strip().lower(),k.strip().lower()):(v or "").strip() for k,v in row.items()}
    return {"municipio":clean.get("municipio",""),"uf":clean.get("uf","PR").upper(),"codigo_ibge":clean.get("codigo_ibge","")}

def main() -> None:
    p=argparse.ArgumentParser(description="Normaliza a carteira municipal para importação futura.")
    p.add_argument("arquivo",type=Path)
    p.add_argument("--saida",type=Path,default=Path("carteira-normalizada.json"))
    a=p.parse_args()
    with a.arquivo.open(encoding="utf-8-sig",newline="") as f:
        sample=f.read(4096); f.seek(0); dialect=csv.Sniffer().sniff(sample,delimiters=";,	")
        rows=[normalize(r) for r in csv.DictReader(f,dialect=dialect)]
    rows=[r for r in rows if r["municipio"]]
    errors=[]; seen=set()
    for i,r in enumerate(rows,2):
        key=(r["municipio"].casefold(),r["uf"]);
        if key in seen: errors.append(f"linha {i}: município duplicado")
        seen.add(key)
        if len(r["uf"])!=2: errors.append(f"linha {i}: UF inválida")
        if r["codigo_ibge"] and (not r["codigo_ibge"].isdigit() or len(r["codigo_ibge"])!=7): errors.append(f"linha {i}: código IBGE inválido")
    a.saida.write_text(json.dumps({"items":rows,"count":len(rows),"errors":errors},ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"{len(rows)} município(s) processado(s); {len(errors)} alerta(s). Saída: {a.saida}")
if __name__=="__main__": main()
