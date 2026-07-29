#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.connectors.pncp import PNCPConnector

MISSING = "Não informado pela fonte"
ENDPOINT = "https://pncp.gov.br/api/consulta/v1/contratos"


def digits(value: Any) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def payload_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("data", "items", "content", "contratos", "resultado"):
        value = payload.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
    return []


def total_pages(payload: Any) -> int:
    if not isinstance(payload, dict):
        return 1
    for key in ("totalPaginas", "total_pages", "totalPages"):
        value = payload.get(key)
        if isinstance(value, int) and value > 0:
            return value
    return 1


def date_windows(start: date, end: date, days: int = 365) -> list[tuple[date, date]]:
    windows = []
    cursor = start
    while cursor <= end:
        window_end = min(end, cursor + timedelta(days=days - 1))
        windows.append((cursor, window_end))
        cursor = window_end + timedelta(days=1)
    return windows


def checkpoint_scope(municipalities: list[dict[str, Any]], start: date, end: date) -> str:
    canonical = json.dumps(
        {
            "cnpjs": sorted(digits(m["cnpj"]) for m in municipalities),
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode()).hexdigest()


def municipality_identity(contract: dict[str, Any]) -> tuple[str | None, str | None]:
    unit = contract.get("unidadeOrgao") or contract.get("unidadeExecutora") or {}
    locality = unit.get("localidade") or {}
    ibge = (
        unit.get("codigoIbge")
        or unit.get("municipioId")
        or unit.get("codigoIbgeMunicipio")
        or locality.get("codigoIbgeMunicipio")
    )
    name = unit.get("municipioNome") or locality.get("nomeMunicipio")
    return (str(ibge) if ibge is not None else None, name)


def official_key(contract: dict[str, Any]) -> str:
    key = contract.get("numeroControlePNCP") or contract.get("numeroControlePncp")
    if not key:
        raise ValueError("Contrato sem numeroControlePNCP; relacionamento ambíguo.")
    return str(key)


def normalize(
    contract: dict[str, Any],
    municipality: dict[str, Any],
    fetched_at: str,
    source_url: str,
    digest: str,
) -> dict[str, Any]:
    org = contract.get("orgaoEntidade") or contract.get("orgao") or {}
    supplier = contract.get("fornecedor") or {}
    response_cnpj = digits(org.get("cnpj") or contract.get("cnpjOrgao") or contract.get("orgaoEntidadeCnpj"))
    expected_cnpj = digits(municipality["cnpj"])
    if response_cnpj and response_cnpj != expected_cnpj:
        raise ValueError(f"CNPJ retornado {response_cnpj} difere do CNPJ consultado {expected_cnpj}.")
    response_ibge, response_name = municipality_identity(contract)
    expected_ibge = str(municipality["ibge_code"])
    if response_ibge and response_ibge != expected_ibge:
        raise ValueError(f"IBGE retornado {response_ibge} difere do IBGE da carteira {expected_ibge}.")
    key = official_key(contract)
    return {
        "source": "PNCP",
        "source_record_id": key,
        "numero": contract.get("numeroContratoEmpenho") or contract.get("numeroContrato") or contract.get("numero") or MISSING,
        "ano": contract.get("anoContrato") if contract.get("anoContrato") is not None else MISSING,
        "processo": contract.get("processo") or MISSING,
        "objeto": contract.get("objetoContrato") or MISSING,
        "tipo_contrato": contract.get("tipoContratoNome") or (contract.get("tipoContrato") or {}).get("nome") or MISSING,
        "orgao_cnpj": response_cnpj or expected_cnpj,
        "orgao_nome": org.get("razaoSocial") or org.get("razaosocial") or org.get("nome") or MISSING,
        "municipality_cnpj": municipality["cnpj"],
        "ibge_code": expected_ibge,
        "municipality_name": municipality["name"],
        "fornecedor_documento": digits(contract.get("niFornecedor") or supplier.get("niFornecedor")) or MISSING,
        "fornecedor_nome": contract.get("nomeRazaoSocialFornecedor") or supplier.get("nomeRazaoSocialFornecedor") or supplier.get("nome") or MISSING,
        "valor_inicial": contract.get("valorInicial") if contract.get("valorInicial") is not None else MISSING,
        "valor_global": contract.get("valorGlobal") if contract.get("valorGlobal") is not None else MISSING,
        "valor_acumulado": contract.get("valorAcumulado") if contract.get("valorAcumulado") is not None else MISSING,
        "data_assinatura": contract.get("dataAssinatura") or MISSING,
        "vigencia_inicio": contract.get("dataVigenciaInicio") or MISSING,
        "vigencia_fim": contract.get("dataVigenciaFim") or MISSING,
        "data_publicacao_pncp": contract.get("dataPublicacaoPncp") or MISSING,
        "data_atualizacao": contract.get("dataAtualizacao") or contract.get("dataAtualizacaoGlobal") or MISSING,
        "url_cipi": contract.get("urlCipi") or MISSING,
        "source_url": source_url,
        "fetched_at": fetched_at,
        "sha256": digest,
        "raw": contract,
    }


async def synchronize(
    connector: PNCPConnector,
    municipalities: list[dict[str, Any]],
    output: Path,
    checkpoint_path: Path,
    status_path: Path,
    errors_path: Path,
    start: date,
    end: date,
    page_size: int = 500,
    max_pages: int = 0,
) -> dict[str, Any]:
    windows = date_windows(start, end)
    scope = checkpoint_scope(municipalities, start, end)
    saved = read_json(checkpoint_path, {})
    if saved and not saved.get("completed", False) and saved.get("scope_sha256") != scope:
        raise ValueError("Checkpoint incompleto pertence a outro escopo; remova-o somente após auditoria.")
    municipality_index = int(saved.get("municipality_index", 0)) if not saved.get("completed", False) else 0
    window_index = int(saved.get("window_index", 0)) if not saved.get("completed", False) else 0
    next_page = int(saved.get("next_page", 1)) if not saved.get("completed", False) else 1
    existing = read_json(output, [])
    records = {str(row["source_record_id"]): row for row in existing if row.get("source_record_id")}
    errors = read_json(errors_path, []) if saved and saved.get("scope_sha256") == scope and not saved.get("completed", False) else []
    pages_this_run = 0
    partial = False

    for mi in range(municipality_index, len(municipalities)):
        municipality = municipalities[mi]
        first_window = window_index if mi == municipality_index else 0
        for wi in range(first_window, len(windows)):
            window_start, window_end = windows[wi]
            page = next_page if mi == municipality_index and wi == first_window else 1
            while True:
                try:
                    result = await connector.contracts_by_period(
                        window_start.strftime("%Y%m%d"),
                        window_end.strftime("%Y%m%d"),
                        page,
                        page_size,
                        digits(municipality["cnpj"]),
                    )
                    errors = [
                        error for error in errors
                        if not (
                            error.get("municipality") == municipality["name"]
                            and error.get("window") == [window_start.isoformat(), window_end.isoformat()]
                            and error.get("page") == page
                            and error.get("error") != "AmbiguousOfficialRecord"
                        )
                    ]
                    items = payload_items(result.payload)
                    for item in items:
                        try:
                            normalized = normalize(item, municipality, result.fetched_at, result.url, result.sha256)
                            records[normalized["source_record_id"]] = normalized
                        except ValueError as exc:
                            errors.append({
                                "municipality": municipality["name"],
                                "cnpj": municipality["cnpj"],
                                "window": [window_start.isoformat(), window_end.isoformat()],
                                "page": page,
                                "error": "AmbiguousOfficialRecord",
                                "message": str(exc),
                            })
                    pages = total_pages(result.payload)
                    pages_this_run += 1
                    has_more_pages = page < pages and bool(items)
                    if has_more_pages:
                        checkpoint_municipality, checkpoint_window, checkpoint_page = mi, wi, page + 1
                    elif wi + 1 < len(windows):
                        checkpoint_municipality, checkpoint_window, checkpoint_page = mi, wi + 1, 1
                    else:
                        checkpoint_municipality, checkpoint_window, checkpoint_page = mi + 1, 0, 1
                    write_json(output, sorted(records.values(), key=lambda x: (str(x.get("municipality_name")), str(x.get("ano")), str(x.get("numero")))))
                    write_json(errors_path, errors)
                    write_json(checkpoint_path, {
                        "endpoint": ENDPOINT,
                        "scope_sha256": scope,
                        "municipality_index": checkpoint_municipality,
                        "window_index": checkpoint_window,
                        "next_page": checkpoint_page,
                        "completed": False,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    })
                    print(f"PNCP {mi + 1}/{len(municipalities)} {municipality['name']} {window_start:%Y-%m-%d}..{window_end:%Y-%m-%d} página {page}/{pages} — {len(items)}")
                    if max_pages and pages_this_run >= max_pages:
                        partial = True
                        break
                    if not has_more_pages:
                        break
                    page += 1
                except Exception as exc:
                    errors.append({
                        "municipality": municipality["name"],
                        "cnpj": municipality["cnpj"],
                        "window": [window_start.isoformat(), window_end.isoformat()],
                        "page": page,
                        "error": type(exc).__name__,
                        "message": str(exc)[:500] or MISSING,
                    })
                    write_json(errors_path, errors)
                    write_json(checkpoint_path, {
                        "endpoint": ENDPOINT,
                        "scope_sha256": scope,
                        "municipality_index": mi,
                        "window_index": wi,
                        "next_page": page,
                        "completed": False,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    })
                    partial = True
                    break
            if partial:
                break
            next_page = 1
        if partial:
            break
        window_index = 0

    completed = not partial
    if completed:
        write_json(checkpoint_path, {
            "endpoint": ENDPOINT,
            "scope_sha256": scope,
            "municipality_index": len(municipalities),
            "window_index": 0,
            "next_page": 1,
            "completed": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
    status = {
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "source": "PNCP",
        "endpoint": ENDPOINT,
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "municipalities_total": len(municipalities),
        "contracts": len(records),
        "errors": len(errors),
        "partial": partial,
        "completed": completed,
        "pages_this_run": pages_this_run,
        "policy": "official_only",
        "upsert_key": "numeroControlePNCP",
    }
    write_json(status_path, status)
    return status


async def main(args: argparse.Namespace) -> None:
    portfolio = read_json(ROOT / "site/data/municipalities.json", {})
    municipalities = portfolio.get("municipalities", [])
    if len(municipalities) != 121:
        raise ValueError(f"Carteira inválida: esperados 121 municípios, recebidos {len(municipalities)}.")
    published = ROOT / "data/published"
    output = published / "contracts.json"
    start = datetime.strptime(args.start or "20210101", "%Y%m%d").date()
    end = datetime.strptime(args.end or date.today().strftime("%Y%m%d"), "%Y%m%d").date()
    connector = PNCPConnector(str(ROOT / "data/raw"), retries=args.retries, min_delay=args.min_delay)
    status = await synchronize(
        connector,
        municipalities,
        output,
        published / "pncp_checkpoint.json",
        published / "pncp_sync_status.json",
        published / "pncp_errors.json",
        start,
        end,
        args.page_size,
        args.max_pages,
    )
    public_rows = [
        {key: value for key, value in row.items() if key != "raw"}
        for row in read_json(output, [])
    ]
    write_json(ROOT / "site/data/contracts.json", public_rows)
    print(json.dumps(status, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sincroniza incrementalmente contratos PNCP para os 121 CNPJs da carteira.")
    parser.add_argument("--start", help="Data inicial AAAAMMDD. Padrão: 20210101.")
    parser.add_argument("--end", help="Data final AAAAMMDD. Padrão: hoje.")
    parser.add_argument("--page-size", type=int, default=500)
    parser.add_argument("--max-pages", type=int, default=0, help="Limite total de páginas nesta execução; 0 = sem limite.")
    parser.add_argument("--retries", type=int, default=5)
    parser.add_argument("--min-delay", type=float, default=0.25)
    asyncio.run(main(parser.parse_args()))
