"""Motor incremental de sincronização.

A implementação persiste snapshots quando um banco estiver disponível. Nesta fase,
os métodos de comparação são puros e testáveis para facilitar a conexão posterior aos
endpoints oficiais.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Iterable

@dataclass(slots=True)
class Change:
    entity: str
    key: str
    field: str
    before: Any
    after: Any
    detected_at: str


def fingerprint(record: dict[str, Any]) -> str:
    payload=json.dumps(record,ensure_ascii=False,sort_keys=True,default=str,separators=(",",":"))
    return sha256(payload.encode("utf-8")).hexdigest()


def compare_records(entity: str, key_field: str, before: Iterable[dict], after: Iterable[dict]) -> list[dict]:
    old={str(x[key_field]):x for x in before if key_field in x}
    new={str(x[key_field]):x for x in after if key_field in x}
    detected=datetime.now(timezone.utc).isoformat()
    changes:list[Change]=[]
    for key in sorted(old.keys() | new.keys()):
        if key not in old:
            changes.append(Change(entity,key,"__record__",None,new[key],detected));continue
        if key not in new:
            changes.append(Change(entity,key,"__record__",old[key],None,detected));continue
        for field in sorted(old[key].keys() | new[key].keys()):
            if old[key].get(field)!=new[key].get(field):
                changes.append(Change(entity,key,field,old[key].get(field),new[key].get(field),detected))
    return [asdict(x) for x in changes]
