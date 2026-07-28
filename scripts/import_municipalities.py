import csv,sys
from pathlib import Path
def main(path:str):
    rows=list(csv.DictReader(Path(path).open(encoding="utf-8-sig")))
    required={"municipio"}
    if not rows or not required.issubset(rows[0]): raise SystemExit("CSV deve conter a coluna municipio")
    print(f"{len(rows)} municípios validados")
if __name__=="__main__": main(sys.argv[1])
