#!/usr/bin/env python3
"""Sincroniza planos de ação de Transferências Especiais por CNPJ da carteira.

O endpoint atual usa filtros PostgREST (`eq.`), `limit` e `offset`. Nenhuma
consulta sem CNPJ da carteira é permitida.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.connectors.transferegov import TransferegovConnector

BASE = "https://api.transferegov.gestao.gov.br/transferenciasespeciais"
ENTITY = "special_action_plans"
MISSING = "Não informado pela fonte"


def read_json(path: Path, fallback):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else fallback


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def items(payload):
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("data", "items", "content", "resultados"):
            if isinstance(payload.get(key), list):
                return [row for row in payload[key] if isinstance(row, dict)]
    return []


async def sync(limit: int = 1000) -> dict:
    municipalities = read_json(ROOT / "site/data/municipalities.json", {}).get("municipalities", [])
    output = ROOT / "data/published/transferegov/special_action_plans.json"
    checkpoint_path = ROOT / "data/published/transferegov/special_action_plans.checkpoint.json"
    existing = {str(row["source_record_id"]): row for row in read_json(output, []) if row.get("source_record_id")}
    checkpoint = read_json(checkpoint_path, {"completed_cnpjs": []})
    completed = set(checkpoint.get("completed_cnpjs", []))
    connector = TransferegovConnector(ROOT / "data/raw/transferegov/special_action_plans", min_delay=0.35)
    errors = []
    for municipality in municipalities:
        cnpj = "".join(ch for ch in str(municipality.get("cnpj", "")) if ch.isdigit())
        if len(cnpj) != 14 or cnpj in completed:
            continue
        offset = 0
        try:
            while True:
                response = await connector.get_json(
                    f"{BASE}/plano_acao_especial",
                    {"cnpj_beneficiario_plano_acao": f"eq.{cnpj}", "limit": limit, "offset": offset},
                )
                rows = items(response.payload)
                for row in rows:
                    official_id = row.get("id_plano_acao")
                    if official_id is None:
                        raise ValueError("registro sem id_plano_acao")
                    normalized = {
                        "source": "Transferegov - Transferências Especiais",
                        "source_record_id": str(official_id),
                        "municipality_name": municipality.get("name", MISSING),
                        "ibge_code": municipality.get("ibge_code", MISSING),
                        "cnpj": municipality.get("cnpj", MISSING),
                        **row,
                        "source_url": response.url,
                        "fetched_at": response.fetched_at,
                        "sha256": response.sha256,
                    }
                    existing[str(official_id)] = normalized
                if len(rows) < limit:
                    break
                offset += limit
            completed.add(cnpj)
            write_json(checkpoint_path, {"completed_cnpjs": sorted(completed), "entity": ENTITY, "completed": len(completed) == len(municipalities), "root_index": len(completed), "roots_total": len(municipalities)})
            write_json(output, list(existing.values()))
        except Exception as exc:  # checkpoint preserva os municípios já concluídos
            errors.append({"cnpj": cnpj, "municipality": municipality.get("name", MISSING), "error": str(exc)})
    write_json(output, list(existing.values()))
    status = {"entity": ENTITY, "completed_cnpjs": len(completed), "records": len(existing), "errors": errors, "status": "completed" if not errors else "partial"}
    write_json(ROOT / "data/published/transferegov/special_action_plans.status.json", status)
    write_json(ROOT / "data/published/transferegov/special_action_plans_sync_status.json", {"completed": not errors and len(completed) == len(municipalities), "roots_total": len(municipalities)})
    write_json(ROOT / "data/published/transferegov/special_action_plans_errors.json", errors)
    return status


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=1000)
    args = parser.parse_args()
    print(json.dumps(asyncio.run(sync(args.limit)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
