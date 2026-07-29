#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.connectors.transferegov import OfficialResponse, TransferegovConnector

BASE_URL = "https://api-publica.transferegov.gestao.gov.br/parcerias"
MISSING = "Não informado pela fonte"


@dataclass(frozen=True)
class EntitySpec:
    name: str
    endpoint: str
    primary_key: str
    parent_key: str
    roots_from: str


SPECS = {
    "partnerships": EntitySpec("partnerships", "parceria", "id_parceria", "id_proposta", "proposals"),
    "proposal_goals": EntitySpec("proposal_goals", "meta-proposta", "id_meta_proposta", "id_proposta", "proposals"),
    "disbursement_schedule": EntitySpec("disbursement_schedule", "cronograma-desembolso", "id_proposta_cronograma_item", "id_proposta", "proposals"),
    "proposal_analyses": EntitySpec("proposal_analyses", "analise-proposta", "id_analise_proposta", "id_proposta", "proposals"),
    "proposal_indicators": EntitySpec("proposal_indicators", "proposta-resultado-indicador", "id_proposta_resultado_indicador", "id_proposta", "proposals"),
    "proposal_resources": EntitySpec("proposal_resources", "distribuicao-recurso-proposta", "id_distribuicao_recurso_proposta", "id_proposta", "proposals"),
    "commitments": EntitySpec("commitments", "empenho-parceria", "id_empenho_parceria", "id_parceria", "partnerships"),
    "payable_documents": EntitySpec("payable_documents", "documento-habil", "id_documento_habil", "id_parceria", "partnerships"),
    "partnership_accounts": EntitySpec("partnership_accounts", "parceria-conta", "id_parceria_conta", "id_parceria", "partnerships"),
    "payment_orders": EntitySpec("payment_orders", "ordem-pagamento", "id_op", "id_documento_habil", "payable_documents"),
    "bank_statements": EntitySpec("bank_statements", "extrato-bancario", "id_extrato_bancario", "id_parceria_conta", "partnership_accounts"),
}


def read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    for attempt in range(6):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(0.05 * (2**attempt))


def payload_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("data", "items", "content", "resultados", "resultado"):
        rows = payload.get(key)
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def total_pages(payload: Any) -> int:
    if not isinstance(payload, dict):
        return 1
    for key in ("total_pages", "totalPaginas", "totalPages"):
        value = payload.get(key)
        if isinstance(value, int) and value > 0:
            return value
    return 1


def roots_for(spec: EntitySpec) -> list[str]:
    published = ROOT / "data/published/transferegov"
    source = read_json(published / f"{spec.roots_from}.json", [])
    key = SPECS[spec.roots_from].primary_key if spec.roots_from in SPECS else "id_proposta"
    return sorted({str(row[key]) for row in source if row.get(key) is not None}, key=lambda value: (len(value), value))


def normalize(row: dict[str, Any], spec: EntitySpec, response: OfficialResponse) -> dict[str, Any]:
    official_id = row.get(spec.primary_key)
    if official_id is None:
        raise ValueError(f"{spec.name}: registro sem chave oficial {spec.primary_key}.")
    return {
        "source": "Transferegov - Gestão de Parcerias",
        "source_record_id": str(official_id),
        **row,
        "source_url": response.url,
        "fetched_at": response.fetched_at,
        "sha256": response.sha256,
    }


def persist_raw(spec: EntitySpec, root: str, page: int, response: OfficialResponse) -> None:
    day = response.fetched_at[:10]
    target = ROOT / "data/raw/transferegov" / spec.name / day
    target.mkdir(parents=True, exist_ok=True)
    stamp = response.fetched_at.replace(":", "-")
    write_json(target / f"{root}-p{page}-{stamp}-{response.sha256[:12]}.json", {
        "source": "Transferegov - Gestão de Parcerias",
        "entity": spec.name,
        "root_key": spec.parent_key,
        "root_value": root,
        "page": page,
        "source_url": response.url,
        "fetched_at": response.fetched_at,
        "sha256": response.sha256,
        "payload": response.payload,
    })


async def synchronize_entity(
    connector: TransferegovConnector,
    spec: EntitySpec,
    page_size: int = 200,
    max_pages: int = 0,
    max_roots: int = 0,
) -> dict[str, Any]:
    published = ROOT / "data/published/transferegov"
    output = published / f"{spec.name}.json"
    checkpoint_path = published / f"{spec.name}_checkpoint.json"
    status_path = published / f"{spec.name}_sync_status.json"
    errors_path = published / f"{spec.name}_errors.json"
    roots = roots_for(spec)
    if max_roots:
        roots = roots[:max_roots]
    existing = read_json(output, [])
    records = {str(row["source_record_id"]): row for row in existing if row.get("source_record_id")}
    checkpoint = read_json(checkpoint_path, {})
    root_index = int(checkpoint.get("root_index", 0)) if not checkpoint.get("completed", False) else 0
    next_page = int(checkpoint.get("next_page", 1)) if not checkpoint.get("completed", False) else 1
    errors = read_json(errors_path, []) if not checkpoint.get("completed", False) else []
    pages_this_run = 0
    partial = False

    for index in range(root_index, len(roots)):
        root = roots[index]
        page = next_page if index == root_index else 1
        while True:
            try:
                response = await connector.get_json(
                    f"{BASE_URL}/{spec.endpoint}",
                    {spec.parent_key: root, "pagina": page, "tamanho_da_pagina": page_size},
                )
                errors = [
                    error for error in errors
                    if not (
                        error.get("root") == root
                        and error.get("page") == page
                        and error.get("error") not in {"AmbiguousParentRelationship", "MissingOfficialKey"}
                    )
                ]
                persist_raw(spec, root, page, response)
                rows = payload_items(response.payload)
                for row in rows:
                    returned_parent = row.get(spec.parent_key)
                    if returned_parent is None or str(returned_parent) != root:
                        errors.append({
                            "entity": spec.name,
                            "root": root,
                            "page": page,
                            "error": "AmbiguousParentRelationship",
                            "message": f"{spec.parent_key} retornado: {returned_parent!r}",
                        })
                        continue
                    try:
                        normalized = normalize(row, spec, response)
                    except ValueError as exc:
                        errors.append({
                            "entity": spec.name,
                            "root": root,
                            "page": page,
                            "error": "MissingOfficialKey",
                            "message": str(exc),
                        })
                        continue
                    records[normalized["source_record_id"]] = normalized

                pages = total_pages(response.payload)
                has_more = page < pages and bool(rows)
                if has_more:
                    checkpoint_root, checkpoint_page = index, page + 1
                else:
                    checkpoint_root, checkpoint_page = index + 1, 1
                pages_this_run += 1
                write_json(output, sorted(records.values(), key=lambda row: row["source_record_id"]))
                write_json(errors_path, errors)
                write_json(checkpoint_path, {
                    "entity": spec.name,
                    "root_index": checkpoint_root,
                    "next_page": checkpoint_page,
                    "roots_total": len(roots),
                    "completed": False,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                })
                print(f"{spec.name} {index + 1}/{len(roots)} raiz {root} página {page}/{pages} — {len(rows)}")
                if max_pages and pages_this_run >= max_pages:
                    partial = True
                    break
                if not has_more:
                    break
                page += 1
            except Exception as exc:
                errors.append({
                    "entity": spec.name,
                    "root": root,
                    "page": page,
                    "error": type(exc).__name__,
                    "message": str(exc)[:500] or MISSING,
                })
                write_json(errors_path, errors)
                write_json(checkpoint_path, {
                    "entity": spec.name,
                    "root_index": index,
                    "next_page": page,
                    "roots_total": len(roots),
                    "completed": False,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                })
                partial = True
                break
        if partial:
            break
        next_page = 1

    completed = not partial
    if completed:
        write_json(checkpoint_path, {
            "entity": spec.name,
            "root_index": len(roots),
            "next_page": 1,
            "roots_total": len(roots),
            "completed": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
    status = {
        "entity": spec.name,
        "endpoint": f"{BASE_URL}/{spec.endpoint}",
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "roots_total": len(roots),
        "records": len(records),
        "errors": len(errors),
        "pages_this_run": pages_this_run,
        "partial": partial,
        "completed": completed,
        "primary_key": spec.primary_key,
        "parent_key": spec.parent_key,
        "policy": "official_only",
    }
    write_json(status_path, status)
    return status


async def main(args: argparse.Namespace) -> None:
    names = list(SPECS) if args.entity == "all" else [args.entity]
    connector = TransferegovConnector(ROOT / "data/raw/transferegov", retries=args.retries, min_delay=args.min_delay)
    results = []
    for name in names:
        spec = SPECS[name]
        roots = roots_for(spec)
        if not roots:
            results.append({"entity": name, "skipped": True, "reason": f"Sem raízes em {spec.roots_from}.json"})
            continue
        results.append(await synchronize_entity(connector, spec, args.page_size, args.max_pages, args.max_roots))
        if results[-1].get("partial"):
            break
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sincroniza o grafo oficial do Transferegov restrito às propostas da carteira.")
    parser.add_argument("--entity", choices=["all", *SPECS], default="all")
    parser.add_argument("--page-size", type=int, default=200)
    parser.add_argument("--max-pages", type=int, default=0)
    parser.add_argument("--max-roots", type=int, default=0)
    parser.add_argument("--retries", type=int, default=6)
    parser.add_argument("--min-delay", type=float, default=0.35)
    asyncio.run(main(parser.parse_args()))
