from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any
import json
import httpx

@dataclass(frozen=True)
class FetchResult:
    source: str
    url: str
    fetched_at: str
    status_code: int
    payload: Any
    sha256: str

class PublicApiConnector:
    def __init__(self, source: str, base_url: str, raw_dir: str = "data/raw", timeout: float = 60.0):
        self.source=source; self.base_url=base_url.rstrip('/'); self.raw_dir=Path(raw_dir); self.timeout=timeout
    async def get(self, path: str, params: dict[str, Any] | None=None) -> FetchResult:
        url=f"{self.base_url}/{path.lstrip('/')}"
        async with httpx.AsyncClient(timeout=self.timeout,follow_redirects=True,headers={"User-Agent":"GovParcerias-Intelligence/1.0"}) as client:
            response=await client.get(url,params=params); response.raise_for_status(); payload=response.json()
        canonical=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":")); digest=sha256(canonical.encode()).hexdigest(); fetched_at=datetime.now(timezone.utc).isoformat()
        self._persist(path,params or {},payload,digest,fetched_at)
        return FetchResult(self.source,str(response.url),fetched_at,response.status_code,payload,digest)
    def _persist(self,path,params,payload,digest,fetched_at):
        target=self.raw_dir/self.source/fetched_at[:10]; target.mkdir(parents=True,exist_ok=True)
        stamp=fetched_at.replace(':','-'); (target/f"{stamp}-{digest[:12]}.json").write_text(json.dumps({"source":self.source,"path":path,"params":params,"fetched_at":fetched_at,"sha256":digest,"payload":payload},ensure_ascii=False,indent=2),encoding='utf-8')
