#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.connectors.transferegov import OfficialResponse, TransferegovConnector
from app.services.portfolio import validate_portfolio

ENDPOINT = "https://api-publica.transferegov.gestao.gov.br/parcerias/proposta"
NOT_INFORMED = "Não informado pela fonte"


class ApiContractError(RuntimeError):
    """Raised instead of guessing when the official response contract is ambiguous."""


def read_page(payload: Any) -> tuple[list[dict[str, Any]], int, int]:
    if not isinstance(payload, dict):
        raise ApiContractError("Resposta de propostas não é um objeto JSON.")
    required = {"data", "total_pages", "page_number"}
    if not required.issubset(payload):
        raise ApiContractError(
            "Resposta sem data, total_pages ou page_number; paginação não assumida."
        )
    items = payload["data"]
    total_pages = payload["total_pages"]
    page_number = payload["page_number"]
    if (
        not isinstance(items, list)
        or not isinstance(total_pages, int)
        or not isinstance(page_number, int)
        or any(not isinstance(item, dict) for item in items)
    ):
        raise ApiContractError("Tipos inesperados no contrato paginado da API.")
    return items, total_pages, page_number


def normalize(
    item: dict[str, Any],
    municipality: dict[str, str],
    response: OfficialResponse,
) -> dict[str, Any]:
    source_id = item.get("id_proposta")
    if not isinstance(source_id, int):
        raise ApiContractError("Proposta sem id_proposta inteiro; upsert não executado.")
    source_ibge = item.get("cd_ibge_recebedor")
    if str(source_ibge) != municipality["ibge_code"]:
        raise ApiContractError(
            f"Proposta {source_id} retornou IBGE {source_ibge}, diferente do filtro "
            f"{municipality['ibge_code']}."
        )

    def value(field: str) -> Any:
        result = item.get(field)
        return result if result not in (None, "") else NOT_INFORMED

    return {
        "source": "Transferegov - Gestão de Parcerias",
        "source_record_id": str(source_id),
        "id_proposta": source_id,
        "id_programa": value("id_programa"),
        "municipality_name": municipality["name"],
        "municipality_cnpj": municipality["cnpj"],
        "ibge_code": municipality["ibge_code"],
        "receiver_name": value("nm_ente_recebedor"),
        "receiver_cnpj": value("cnpj_ente_recebedor"),
        "object": value("ds_objeto"),
        "status": value("situacao_proposta"),
        "total_value": value("nr_vlr_total"),
        "proposal_date": value("dt_proposta"),
        "source_url": response.url,
        "fetched_at": response.fetched_at,
        "sha256": response.sha256,
        "raw": item,
    }


def load_existing(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path} deve conter uma lista JSON.")
    records: dict[str, dict[str, Any]] = {}
    for record in payload:
        if not isinstance(record, dict) or not record.get("source_record_id"):
            raise ValueError(f"{path} contém registro sem source_record_id.")
        records[str(record["source_record_id"])] = record
    return records


def upsert(
    existing: dict[str, dict[str, Any]],
    incoming: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    merged = dict(existing)
    for record in incoming:
        merged[str(record["source_record_id"])] = record
    return merged


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for attempt in range(5):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.05 * (2**attempt))


def checkpoint_scope(municipalities: list[dict[str, str]]) -> str:
    joined = "|".join(item["ibge_code"] for item in municipalities)
    return hashlib.sha256(joined.encode("ascii")).hexdigest()


def persist_raw(
    raw_root: Path,
    municipality: dict[str, str],
    page: int,
    response: OfficialResponse,
) -> None:
    timestamp = response.fetched_at.replace(":", "-")
    target = raw_root / response.fetched_at[:10]
    write_json(
        target / f"{municipality['ibge_code']}-p{page}-{timestamp}-{response.sha256[:12]}.json",
        {
            "source": "Transferegov - Gestão de Parcerias",
            "endpoint": ENDPOINT,
            "params": {
                "cd_ibge_recebedor": municipality["ibge_code"],
                "pagina": page,
            },
            "url": response.url,
            "fetched_at": response.fetched_at,
            "sha256": response.sha256,
            "payload": response.payload,
        },
    )


async def synchronize(
    connector: TransferegovConnector,
    municipalities: list[dict[str, str]],
    output_path: Path,
    checkpoint_path: Path,
    status_path: Path,
    raw_root: Path,
    page_size: int = 200,
    max_municipalities: int = 0,
    max_pages: int = 0,
    only_ibge: str | None = None,
) -> dict[str, Any]:
    existing = load_existing(output_path)
    selected = municipalities
    if only_ibge:
        selected = [item for item in municipalities if item["ibge_code"] == only_ibge]
        if not selected:
            raise ValueError(f"IBGE {only_ibge} não pertence à carteira canônica.")
    elif max_municipalities:
        selected = municipalities[: min(len(municipalities), max_municipalities)]
    scope = checkpoint_scope(selected)

    checkpoint: dict[str, Any] = {}
    if checkpoint_path.exists():
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if checkpoint.get("endpoint") != ENDPOINT:
            raise ValueError("Checkpoint pertence a outro endpoint.")
        if checkpoint.get("completed"):
            checkpoint = {}
        elif checkpoint.get("scope_sha256") != scope:
            raise ValueError(
                "Checkpoint incompleto pertence a outro escopo de municípios; "
                "nenhuma retomada foi assumida."
            )
    start_index = int(checkpoint.get("municipality_index", 0))
    start_page = int(checkpoint.get("next_page", 1))

    pages_fetched = 0
    records_seen = 0
    municipalities_processed = 0
    municipalities_completed = start_index
    errors: list[dict[str, Any]] = []
    stopped_by_page_limit = False
    started_at = datetime.now(timezone.utc).isoformat()

    for index in range(start_index, len(selected)):
        municipality = selected[index]
        page = start_page if index == start_index else 1
        municipality_pages = 0
        try:
            while True:
                response = await connector.get_json(
                    ENDPOINT,
                    {
                        "cd_ibge_recebedor": municipality["ibge_code"],
                        "pagina": page,
                        "tamanho_da_pagina": page_size,
                    },
                )
                items, total_pages, returned_page = read_page(response.payload)
                if returned_page != page:
                    raise ApiContractError(
                        f"API retornou página {returned_page} para a página solicitada {page}."
                    )
                normalized = [normalize(item, municipality, response) for item in items]
                existing = upsert(existing, normalized)
                persist_raw(raw_root, municipality, page, response)
                write_json(
                    output_path,
                    sorted(existing.values(), key=lambda row: int(row["id_proposta"])),
                )
                records_seen += len(items)
                pages_fetched += 1
                municipality_pages += 1
                next_page = page + 1
                write_json(
                    checkpoint_path,
                    {
                        "endpoint": ENDPOINT,
                        "municipality_index": index,
                        "municipality_ibge": municipality["ibge_code"],
                        "next_page": next_page,
                        "scope_sha256": scope,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "completed": False,
                    },
                )
                print(
                    f"Transferegov {index + 1}/{len(selected)} {municipality['name']} "
                    f"página {page}/{total_pages} — {len(items)} proposta(s)"
                )
                if page >= total_pages:
                    break
                if max_pages and municipality_pages >= max_pages:
                    stopped_by_page_limit = True
                    break
                page = next_page
            if stopped_by_page_limit:
                break
            start_page = 1
            write_json(
                checkpoint_path,
                {
                    "endpoint": ENDPOINT,
                    "municipality_index": index + 1,
                    "municipality_ibge": None,
                    "next_page": 1,
                    "scope_sha256": scope,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "completed": index + 1 >= len(selected),
                },
            )
            municipalities_processed += 1
            municipalities_completed = index + 1
        except Exception as exc:
            errors.append(
                {
                    "municipality": municipality["name"],
                    "ibge_code": municipality["ibge_code"],
                    "error": type(exc).__name__,
                    "message": str(exc)[:500] or NOT_INFORMED,
                }
            )
            break

    status = {
        "source": "Transferegov - Gestão de Parcerias",
        "endpoint": ENDPOINT,
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "portfolio_size": len(municipalities),
        "municipalities_selected": len(selected),
        "resume_from_index": start_index,
        "municipalities_processed_this_run": municipalities_processed,
        "municipalities_completed_total": municipalities_completed,
        "pages_fetched": pages_fetched,
        "records_seen": records_seen,
        "records_published": len(existing),
        "errors": errors,
        "partial": (
            bool(errors)
            or len(selected) < len(municipalities)
            or stopped_by_page_limit
        ),
        "policy": "official_only",
        "scope_filter": "cd_ibge_recebedor from canonical portfolio only",
    }
    write_json(status_path, status)
    return status


async def main(args: argparse.Namespace) -> None:
    municipalities = validate_portfolio(
        ROOT / "site/data/municipalities.json",
        ROOT / "source-data/Planilha 121 municipios.xlsx",
    )
    root = ROOT / "data/published/transferegov"
    connector = TransferegovConnector(
        ROOT / "data/raw/transferegov/proposals",
        retries=args.retries,
        min_delay=args.min_delay,
    )
    status = await synchronize(
        connector,
        municipalities,
        root / "proposals.json",
        root / "proposals_checkpoint.json",
        root / "proposals_sync_status.json",
        ROOT / "data/raw/transferegov/proposals",
        page_size=args.page_size,
        max_municipalities=args.max_municipalities,
        max_pages=args.max_pages,
        only_ibge=args.only_ibge,
    )
    print(json.dumps(status, ensure_ascii=False, indent=2))
    if status["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sincroniza propostas do Transferegov somente para a carteira canônica."
    )
    parser.add_argument("--page-size", type=int, default=200, choices=range(1, 201))
    parser.add_argument("--retries", type=int, default=6)
    parser.add_argument("--min-delay", type=float, default=0.35)
    parser.add_argument("--max-municipalities", type=int, default=0)
    parser.add_argument("--max-pages", type=int, default=0)
    parser.add_argument(
        "--only-ibge",
        help="Valida somente um código IBGE, obrigatoriamente pertencente à carteira.",
    )
    asyncio.run(main(parser.parse_args()))
