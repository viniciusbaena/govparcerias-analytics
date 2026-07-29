from pathlib import Path
import json
class JsonRepository:
    def __init__(self,root: str="data/published"): self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True)
    def read(self,name:str,default):
        p=self.root/f"{name}.json"; return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default
    def write(self,name:str,data):
        p=self.root/f"{name}.json"; p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8'); return p
