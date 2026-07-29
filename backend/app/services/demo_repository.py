from functools import lru_cache
import json
from pathlib import Path

@lru_cache
def load_demo() -> dict:
    path=Path(__file__).resolve().parents[3]/"site"/"data"/"demo.json"
    return json.loads(path.read_text(encoding="utf-8"))
