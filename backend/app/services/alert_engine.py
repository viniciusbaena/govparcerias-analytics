from __future__ import annotations
from datetime import date, datetime
from typing import Iterable

def build_expiry_alerts(partnerships: Iterable[dict], today: date | None=None) -> list[dict]:
    today=today or date.today();alerts=[]
    for p in partnerships:
        raw=p.get("fim")
        if not raw: continue
        end=datetime.fromisoformat(str(raw)).date()
        days=(end-today).days
        if 0 <= days <= 180:
            level="alto" if days <= 60 else "médio" if days <= 120 else "baixo"
            alerts.append({"type":"vigencia","level":level,"days":days,"numero":p.get("numero"),"municipio":p.get("municipio"),"message":f"Vigência termina em {days} dias."})
    return sorted(alerts,key=lambda x:x["days"])
