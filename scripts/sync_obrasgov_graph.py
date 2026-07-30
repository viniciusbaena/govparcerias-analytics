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

BASE_URL = "https://api-publica.obrasgov.gestao.gov.br/obras"
PUBLISHED = ROOT / "data/published/obrasgov"
MISSING = "Não informado pela fonte"


@dataclass(frozen=True)
class Spec:
    name: str
    endpoint: str
    primary_key: str


CHILD_SPECS = {
    "projects": Spec("projects", "projeto-investimento", "id_projeto_investimento"),
    "physical_execution": Spec("physical_execution", "execucao-fisica", "id_projeto_investimento"),
    "project_contracts": Spec("project_contracts", "contrato", "id_contrato"),
    "project_commitments": Spec("project_commitments", "empenho", "nr_empenho"),
    "project_geometries": Spec("project_geometries", "geometria", "id_geometria"),
    "project_interruptions": Spec("project_interruptions", "historico-situacao-cancelada-paralisada", "id_historico_situacao_investimento"),
    "feasibility_studies": Spec("feasibility_studies", "estudo-viabilidade", "id_projeto_investimento"),
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


def items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("data", "items", "content"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
    return []


def pages(payload: Any) -> int:
    if isinstance(payload, dict):
        for key in ("total_pages", "totalPaginas", "totalPages"):
            if isinstance(payload.get(key), int) and payload[key] > 0:
                return payload[key]
    return 1


def persist_raw(entity: str, root: str, page: int, response: OfficialResponse) -> None:
    target = ROOT / "data/raw/obrasgov" / entity / response.fetched_at[:10]
    stamp = response.fetched_at.replace(":", "-")
    write_json(target / f"{root}-p{page}-{stamp}-{response.sha256[:12]}.json", {
        "source": "ObrasGov",
        "entity": entity,
        "root": root,
        "page": page,
        "source_url": response.url,
        "fetched_at": response.fetched_at,
        "sha256": response.sha256,
        "payload": response.payload,
    })


def normalized(row: dict[str, Any], primary_key: str, response: OfficialResponse) -> dict[str, Any]:
    value = row.get(primary_key)
    if value is None:
        raise ValueError(f"Registro sem chave oficial {primary_key}.")
    return {
        "source": "ObrasGov",
        "source_record_id": str(value),
        **row,
        "source_url": response.url,
        "fetched_at": response.fetched_at,
        "sha256": response.sha256,
    }


async def sync_geometries(connector: TransferegovConnector, page_size: int, max_pages: int = 0) -> dict[str, Any]:
    municipalities = read_json(ROOT / "site/data/municipalities.json", {}).get("municipalities", [])
    output = PUBLISHED / "geometries.json"
    checkpoint_path = PUBLISHED / "geometries_checkpoint.json"
    errors_path = PUBLISHED / "geometries_errors.json"
    existing = read_json(output, [])
    records = {str(row["source_record_id"]): row for row in existing if row.get("source_record_id")}
    checkpoint = read_json(checkpoint_path, {})
    index = int(checkpoint.get("municipality_index", 0)) if not checkpoint.get("completed", False) else 0
    next_page = int(checkpoint.get("next_page", 1)) if not checkpoint.get("completed", False) else 1
    errors = read_json(errors_path, []) if not checkpoint.get("completed", False) else []
    pages_run = 0
    partial = False
    for mi in range(index, len(municipalities)):
        municipality = municipalities[mi]
        ibge = str(municipality["ibge_code"])
        page = next_page if mi == index else 1
        while True:
            try:
                response = await connector.get_json(f"{BASE_URL}/geometria", {
                    "cod_ibge": ibge, "pagina": page, "tamanho_da_pagina": page_size,
                })
                persist_raw("geometries", ibge, page, response)
                rows = items(response.payload)
                for row in rows:
                    if str(row.get("cod_ibge")) != ibge:
                        errors.append({"municipality": municipality["name"], "ibge_code": ibge, "page": page, "error": "AmbiguousTerritory", "message": f"cod_ibge retornado: {row.get('cod_ibge')!r}"})
                        continue
                    try:
                        record = normalized(row, "id_geometria", response)
                    except ValueError as exc:
                        errors.append({"municipality": municipality["name"], "ibge_code": ibge, "page": page, "error": "MissingOfficialKey", "message": str(exc)})
                        continue
                    record["municipality_name"] = municipality["name"]
                    record["municipality_cnpj"] = municipality["cnpj"]
                    records[record["source_record_id"]] = record
                total = pages(response.payload)
                more = page < total and bool(rows)
                cp_index, cp_page = (mi, page + 1) if more else (mi + 1, 1)
                pages_run += 1
                write_json(output, sorted(records.values(), key=lambda row: row["source_record_id"]))
                write_json(errors_path, errors)
                write_json(checkpoint_path, {"municipality_index": cp_index, "next_page": cp_page, "municipalities_total": len(municipalities), "completed": False, "updated_at": datetime.now(timezone.utc).isoformat()})
                print(f"geometries {mi + 1}/{len(municipalities)} {municipality['name']} página {page}/{total} — {len(rows)}")
                if max_pages and pages_run >= max_pages:
                    partial = True
                    break
                if not more:
                    break
                page += 1
            except Exception as exc:
                errors.append({"municipality": municipality["name"], "ibge_code": ibge, "page": page, "error": type(exc).__name__, "message": str(exc)[:500] or MISSING})
                write_json(errors_path, errors)
                write_json(checkpoint_path, {"municipality_index": mi, "next_page": page, "municipalities_total": len(municipalities), "completed": False, "updated_at": datetime.now(timezone.utc).isoformat()})
                partial = True
                break
        if partial:
            break
        next_page = 1
    completed = not partial
    if completed:
        write_json(checkpoint_path, {"municipality_index": len(municipalities), "next_page": 1, "municipalities_total": len(municipalities), "completed": True, "updated_at": datetime.now(timezone.utc).isoformat()})
    status = {"entity": "geometries", "records": len(records), "municipalities_total": len(municipalities), "pages_this_run": pages_run, "errors": len(errors), "partial": partial, "completed": completed, "territory_filter": "cod_ibge", "policy": "official_only"}
    write_json(PUBLISHED / "geometries_sync_status.json", status)
    return status


def project_roots() -> list[str]:
    return sorted({str(row["id_projeto_investimento"]) for row in read_json(PUBLISHED / "geometries.json", []) if row.get("id_projeto_investimento")})


async def sync_child(connector: TransferegovConnector, spec: Spec, page_size: int, max_pages: int = 0) -> dict[str, Any]:
    roots = project_roots()
    output = PUBLISHED / f"{spec.name}.json"
    checkpoint_path = PUBLISHED / f"{spec.name}_checkpoint.json"
    errors_path = PUBLISHED / f"{spec.name}_errors.json"
    existing = read_json(output, [])
    records = {str(row["source_record_id"]): row for row in existing if row.get("source_record_id")}
    checkpoint = read_json(checkpoint_path, {})
    index = int(checkpoint.get("root_index", 0)) if not checkpoint.get("completed", False) else 0
    next_page = int(checkpoint.get("next_page", 1)) if not checkpoint.get("completed", False) else 1
    errors = read_json(errors_path, []) if not checkpoint.get("completed", False) else []
    pages_run = 0
    partial = False
    for ri in range(index, len(roots)):
        root = roots[ri]
        page = next_page if ri == index else 1
        while True:
            try:
                response = await connector.get_json(f"{BASE_URL}/{spec.endpoint}", {
                    "id_projeto_investimento": root, "pagina": page, "tamanho_da_pagina": page_size,
                })
                persist_raw(spec.name, root, page, response)
                rows = items(response.payload)
                if spec.primary_key == "id_projeto_investimento" and len(rows) > 1:
                    errors.append({
                        "entity": spec.name,
                        "root": root,
                        "page": page,
                        "error": "AmbiguousOfficialKey",
                        "message": "A fonte retornou múltiplos registros sem identificador próprio além de id_projeto_investimento.",
                    })
                    write_json(errors_path, errors)
                    partial = True
                    break
                for row in rows:
                    if str(row.get("id_projeto_investimento")) != root:
                        errors.append({"entity": spec.name, "root": root, "page": page, "error": "AmbiguousParentRelationship", "message": f"id_projeto_investimento retornado: {row.get('id_projeto_investimento')!r}"})
                        continue
                    try:
                        record = normalized(row, spec.primary_key, response)
                    except ValueError as exc:
                        errors.append({"entity": spec.name, "root": root, "page": page, "error": "MissingOfficialKey", "message": str(exc)})
                        continue
                    records[record["source_record_id"]] = record
                total = pages(response.payload)
                more = page < total and bool(rows)
                cp_index, cp_page = (ri, page + 1) if more else (ri + 1, 1)
                pages_run += 1
                write_json(output, sorted(records.values(), key=lambda row: row["source_record_id"]))
                write_json(errors_path, errors)
                write_json(checkpoint_path, {"root_index": cp_index, "next_page": cp_page, "roots_total": len(roots), "completed": False, "updated_at": datetime.now(timezone.utc).isoformat()})
                print(f"{spec.name} {ri + 1}/{len(roots)} raiz {root} página {page}/{total} — {len(rows)}")
                if max_pages and pages_run >= max_pages:
                    partial = True
                    break
                if not more:
                    break
                page += 1
            except Exception as exc:
                errors.append({"entity": spec.name, "root": root, "page": page, "error": type(exc).__name__, "message": str(exc)[:500] or MISSING})
                write_json(errors_path, errors)
                write_json(checkpoint_path, {"root_index": ri, "next_page": page, "roots_total": len(roots), "completed": False, "updated_at": datetime.now(timezone.utc).isoformat()})
                partial = True
                break
        if partial:
            break
        next_page = 1
    completed = not partial
    if completed:
        write_json(checkpoint_path, {"root_index": len(roots), "next_page": 1, "roots_total": len(roots), "completed": True, "updated_at": datetime.now(timezone.utc).isoformat()})
    status = {"entity": spec.name, "records": len(records), "roots_total": len(roots), "pages_this_run": pages_run, "errors": len(errors), "partial": partial, "completed": completed, "primary_key": spec.primary_key, "parent_key": "id_projeto_investimento", "policy": "official_only"}
    write_json(PUBLISHED / f"{spec.name}_sync_status.json", status)
    return status


async def main(args: argparse.Namespace) -> None:
    connector = TransferegovConnector(ROOT / "data/raw/obrasgov", retries=args.retries, min_delay=args.min_delay)
    if args.entity == "geometries":
        result = await sync_geometries(connector, args.page_size, args.max_pages)
    else:
        result = await sync_child(connector, CHILD_SPECS[args.entity], args.page_size, args.max_pages)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sincroniza o grafo ObrasGov sem carga nacional.")
    parser.add_argument("--entity", choices=["geometries", *CHILD_SPECS], default="geometries")
    parser.add_argument("--page-size", type=int, default=200)
    parser.add_argument("--max-pages", type=int, default=0)
    parser.add_argument("--retries", type=int, default=6)
    parser.add_argument("--min-delay", type=float, default=0.35)
    asyncio.run(main(parser.parse_args()))
