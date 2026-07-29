#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.connectors.transferegov import TransferegovConnector


def schema_value(schema: dict[str, Any]) -> Any:
    if "default" in schema:
        return schema["default"]

    enum = schema.get("enum")
    if isinstance(enum, list) and enum:
        return enum[0]

    kind = schema.get("type")
    fmt = schema.get("format")

    if kind == "integer":
        return 1
    if kind == "number":
        return 1
    if kind == "boolean":
        return False
    if kind == "string":
        if fmt == "date":
            return "2026-01-01"
        if fmt == "date-time":
            return "2026-01-01T00:00:00Z"
        return None

    return None


def operation_parameters(
    path_item: dict[str, Any],
    operation: dict[str, Any],
) -> list[dict[str, Any]]:
    params: list[dict[str, Any]] = []

    for source in (path_item.get("parameters"), operation.get("parameters")):
        if isinstance(source, list):
            params.extend(x for x in source if isinstance(x, dict))

    return params


def build_probe(
    path: str,
    parameters: list[dict[str, Any]],
) -> tuple[str | None, dict[str, Any], list[str]]:
    query: dict[str, Any] = {}
    reasons: list[str] = []
    resolved_path = path

    for param in parameters:
        name = param.get("name")
        location = param.get("in")
        required = bool(param.get("required"))
        schema = param.get("schema") or {}
        value = schema_value(schema)

        if location == "path":
            if value is None:
                reasons.append(
                    f"parâmetro obrigatório de rota sem valor seguro: {name}"
                )
            else:
                resolved_path = resolved_path.replace(
                    "{" + str(name) + "}",
                    str(value),
                )

        elif location == "query":
            lower = str(name or "").lower()

            if lower in {"pagina", "page", "numero_pagina", "pagenumber"}:
                query[name] = 1
            elif lower in {
                "tamanho_pagina",
                "size",
                "pagesize",
                "limite",
                "limit",
                "per_page",
            }:
                query[name] = 1
            elif lower in {"ano", "ano_exercicio", "exercicio"}:
                query[name] = 2026
            elif required:
                if value is None:
                    reasons.append(
                        f"parâmetro obrigatório de consulta sem valor seguro: {name}"
                    )
                else:
                    query[name] = value

    if reasons:
        return None, query, reasons

    return resolved_path, query, []


def summarize_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, list):
        first = payload[0] if payload else None
        return {
            "shape": "list",
            "record_count_sample": len(payload),
            "sample_keys": sorted(first.keys())
            if isinstance(first, dict)
            else [],
        }

    if isinstance(payload, dict):
        list_key = None
        records = None

        for key in (
            "data",
            "items",
            "content",
            "resultados",
            "resultado",
        ):
            value = payload.get(key)
            if isinstance(value, list):
                list_key = key
                records = value
                break

        first = records[0] if records else None

        return {
            "shape": "object",
            "top_level_keys": sorted(payload.keys()),
            "records_key": list_key,
            "record_count_sample": len(records)
            if isinstance(records, list)
            else None,
            "sample_keys": sorted(first.keys())
            if isinstance(first, dict)
            else [],
        }

    return {"shape": type(payload).__name__}


def resolve_base_url(openapi_url: str, spec: dict[str, Any]) -> str:
    servers = spec.get("servers") or []

    if servers and isinstance(servers[0], dict):
        server_url = str(servers[0].get("url") or "").strip()

        if server_url:
            parsed = urlparse(server_url)

            if parsed.scheme in {"http", "https"}:
                return server_url.rstrip("/")

            return urljoin(openapi_url, server_url).rstrip("/")

    return openapi_url.rsplit("/openapi.json", 1)[0].rstrip("/")


async def main() -> None:
    catalog_path = ROOT / "data/config/transferegov_catalog.json"

    if not catalog_path.exists():
        raise FileNotFoundError(
            "Catálogo não encontrado. Execute primeiro "
            "python scripts\\discover_transferegov_api.py"
        )

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    apis = catalog.get("apis") or []

    connector = TransferegovConnector(
        ROOT / "data/raw/transferegov",
        retries=4,
        min_delay=0.5,
    )

    profiles: list[dict[str, Any]] = []
    totals = {
        "apis": 0,
        "get_endpoints": 0,
        "probed": 0,
        "skipped": 0,
        "errors": 0,
    }

    for api in apis:
        openapi_url = api.get("openapi_url")

        if not openapi_url:
            continue

        totals["apis"] += 1
        spec_result = await connector.get_json(openapi_url)
        spec = spec_result.payload
        base_url = resolve_base_url(openapi_url, spec)

        for path, path_item in (spec.get("paths") or {}).items():
            if not isinstance(path_item, dict):
                continue

            operation = path_item.get("get")

            if not isinstance(operation, dict):
                continue

            totals["get_endpoints"] += 1
            params = operation_parameters(path_item, operation)
            resolved_path, query, reasons = build_probe(path, params)

            profile = {
                "api_title": (spec.get("info") or {}).get("title"),
                "openapi_url": openapi_url,
                "base_url": base_url,
                "path": path,
                "operation_id": operation.get("operationId"),
                "summary": operation.get("summary"),
                "tags": operation.get("tags") or [],
                "parameters": [
                    {
                        "name": p.get("name"),
                        "in": p.get("in"),
                        "required": bool(p.get("required")),
                        "schema": p.get("schema") or {},
                    }
                    for p in params
                ],
                "probe_query": query,
                "status": None,
            }

            if resolved_path is None:
                profile["status"] = "skipped"
                profile["reasons"] = reasons
                totals["skipped"] += 1
                profiles.append(profile)
                print(f"PULADO {path} — {'; '.join(reasons)}")
                continue

            url = urljoin(base_url.rstrip("/") + "/", resolved_path.lstrip("/"))

            try:
                result = await connector.get_json(url, params=query)
                profile["status"] = "ok"
                profile["probe_url"] = result.url
                profile["fetched_at"] = result.fetched_at
                profile["sha256"] = result.sha256
                profile["payload_summary"] = summarize_payload(result.payload)
                totals["probed"] += 1
                print(f"OK {path}")
            except Exception as exc:
                profile["status"] = "error"
                profile["error"] = type(exc).__name__
                profile["message"] = (
                    str(exc)[:500] or "Não informado pela fonte"
                )
                totals["errors"] += 1
                print(
                    f"ERRO {path} — {type(exc).__name__}: "
                    f"{str(exc)[:160]}"
                )

            profiles.append(profile)

    published = ROOT / "data/published/transferegov"
    config = ROOT / "data/config"
    published.mkdir(parents=True, exist_ok=True)
    config.mkdir(parents=True, exist_ok=True)

    output = {
        "source": "Transferegov",
        "profiled_at": datetime.now(timezone.utc).isoformat(),
        "totals": totals,
        "profiles": profiles,
        "policy": "official_only",
    }

    (config / "transferegov_endpoint_profiles.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (published / "endpoint_profile_status.json").write_text(
        json.dumps(
            {
                "profiled_at": output["profiled_at"],
                **totals,
                "policy": "official_only",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(json.dumps(totals, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
