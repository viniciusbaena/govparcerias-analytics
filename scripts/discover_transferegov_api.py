#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.connectors.transferegov import TransferegovConnector

OPENAPI_URLS = [
    "https://api-publica.transferegov.gestao.gov.br/especiais/openapi.json",
    "https://api-publica.transferegov.gestao.gov.br/parcerias/openapi.json",
]


async def main() -> None:
    connector = TransferegovConnector(ROOT / "data/raw/transferegov")
    catalogs = []
    errors = []

    for url in OPENAPI_URLS:
        try:
            result = await connector.get_json(url)
            payload = result.payload

            if not isinstance(payload, dict) or not isinstance(payload.get("paths"), dict):
                raise ValueError("A resposta não contém uma especificação OpenAPI válida.")

            info = payload.get("info") or {}
            endpoints = []

            for path, operations in payload["paths"].items():
                if not isinstance(operations, dict):
                    continue

                methods = [
                    method.upper()
                    for method in operations
                    if method.lower() in {"get", "post", "put", "patch", "delete"}
                ]

                endpoints.append({
                    "path": path,
                    "methods": methods,
                })

            catalogs.append({
                "title": info.get("title") or "Não informado pela fonte",
                "version": info.get("version") or "Não informado pela fonte",
                "openapi_url": result.url,
                "fetched_at": result.fetched_at,
                "sha256": result.sha256,
                "endpoint_count": len(endpoints),
                "endpoints": endpoints,
            })

            print(f"OK: {info.get('title') or url} — {len(endpoints)} endpoint(s)")

        except Exception as exc:
            errors.append({
                "url": url,
                "error": type(exc).__name__,
                "message": str(exc)[:500] or "Não informado pela fonte",
            })
            print(f"ERRO: {url} — {type(exc).__name__}: {str(exc)[:200]}")

    discovered_at = datetime.now(timezone.utc).isoformat()

    catalog = {
        "source": "Transferegov",
        "discovered_at": discovered_at,
        "api_count": len(catalogs),
        "apis": catalogs,
        "errors": errors,
        "policy": "official_only",
    }

    status = {
        "discovered_at": discovered_at,
        "api_count": len(catalogs),
        "endpoint_count": sum(api["endpoint_count"] for api in catalogs),
        "errors": len(errors),
        "policy": "official_only",
    }

    config_dir = ROOT / "data/config"
    published_dir = ROOT / "data/published/transferegov"
    config_dir.mkdir(parents=True, exist_ok=True)
    published_dir.mkdir(parents=True, exist_ok=True)

    (config_dir / "transferegov_catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (published_dir / "discovery_status.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(status, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
