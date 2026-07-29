from __future__ import annotations

import asyncio
import hashlib
import json
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx


@dataclass(slots=True)
class OfficialResponse:
    payload: Any
    url: str
    fetched_at: str
    sha256: str
    status_code: int


class TransferegovConnector:
    BASE_URL = "https://api-publica.transferegov.gestao.gov.br"

    def __init__(self, raw_dir: str | Path, timeout: float = 60, retries: int = 6, min_delay: float = 0.35) -> None:
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.retries = retries
        self.min_delay = min_delay

    async def get_json(self, url: str, params: dict[str, Any] | None = None) -> OfficialResponse:
        headers = {
            "Accept": "application/json",
            "User-Agent": "GovParcerias-Intelligence/1.0 official-data-client",
        }
        async with httpx.AsyncClient(timeout=self.timeout, headers=headers, follow_redirects=True) as client:
            for attempt in range(self.retries + 1):
                try:
                    response = await client.get(url, params=params)
                    if response.status_code == 429 or response.status_code >= 500:
                        if attempt >= self.retries:
                            response.raise_for_status()
                        retry_after = response.headers.get("Retry-After")
                        wait = float(retry_after) if retry_after and retry_after.isdigit() else min(60.0, (2 ** attempt) + random.random())
                        await asyncio.sleep(wait)
                        continue

                    response.raise_for_status()
                    raw = response.content
                    payload = response.json()
                    await asyncio.sleep(self.min_delay)
                    return OfficialResponse(
                        payload=payload,
                        url=str(response.url),
                        fetched_at=datetime.now(timezone.utc).isoformat(),
                        sha256=hashlib.sha256(raw).hexdigest(),
                        status_code=response.status_code,
                    )
                except (httpx.HTTPError, json.JSONDecodeError):
                    if attempt >= self.retries:
                        raise
                    await asyncio.sleep(min(60.0, (2 ** attempt) + random.random()))

        raise RuntimeError("Falha inesperada na consulta oficial.")
