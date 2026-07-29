#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.connectors.pncp import PNCPConnector


def digits(value: Any) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


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


def municipality_identity(contract: dict[str, Any]) -> tuple[str | None, str | None]:
    unit = contract.get("unidadeOrgao") or contract.get("unidadeExecutora") or {}
    locality = unit.get("localidade") or {}
    ibge = unit.get("municipioId") or unit.get("codigoIbgeMunicipio") or locality.get("codigoIbgeMunicipio")
    name = unit.get("municipioNome") or locality.get("nomeMunicipio")
    return (str(ibge) if ibge is not None else None, name)


def normalize(contract: dict[str, Any], portfolio_by_cnpj: dict[str, dict[str, Any]], fetched_at: str, source_url: str, sha256: str) -> dict[str, Any]:
    org = contract.get("orgaoEntidade") or contract.get("orgao") or {}
    supplier = contract.get("fornecedor") or {}
    org_cnpj = digits(org.get("cnpj") or contract.get("cnpjOrgao") or contract.get("orgaoEntidadeCnpj"))
    ibge_code, municipality_name = municipality_identity(contract)
    portfolio = portfolio_by_cnpj.get(org_cnpj)
    if portfolio:
        ibge_code = str(portfolio.get("ibge_code") or ibge_code or "") or None
        municipality_name = portfolio.get("name") or municipality_name
    number = contract.get("numeroContratoEmpenho") or contract.get("numeroContrato") or contract.get("numero")
    control = contract.get("numeroControlePNCP") or contract.get("numeroControlePncp")
    return {
        "source": "PNCP",
        "source_record_id": control,
        "numero": number,
        "ano": contract.get("anoContrato"),
        "processo": contract.get("processo"),
        "objeto": contract.get("objetoContrato"),
        "tipo_contrato": contract.get("tipoContratoNome") or (contract.get("tipoContrato") or {}).get("nome"),
        "orgao_cnpj": org_cnpj or None,
        "orgao_nome": org.get("razaoSocial") or org.get("razaosocial") or org.get("nome"),
        "municipality_cnpj": portfolio.get("cnpj") if portfolio else None,
        "ibge_code": ibge_code,
        "municipality_name": municipality_name,
        "fornecedor_documento": digits(contract.get("niFornecedor") or supplier.get("niFornecedor")) or None,
        "fornecedor_nome": contract.get("nomeRazaoSocialFornecedor") or supplier.get("nomeRazaoSocialFornecedor") or supplier.get("nome"),
        "valor_inicial": contract.get("valorInicial"),
        "valor_global": contract.get("valorGlobal"),
        "valor_acumulado": contract.get("valorAcumulado"),
        "data_assinatura": contract.get("dataAssinatura"),
        "vigencia_inicio": contract.get("dataVigenciaInicio"),
        "vigencia_fim": contract.get("dataVigenciaFim"),
        "data_publicacao_pncp": contract.get("dataPublicacaoPncp"),
        "data_atualizacao": contract.get("dataAtualizacao"),
        "url_cipi": contract.get("urlCipi"),
        "source_url": source_url,
        "fetched_at": fetched_at,
        "sha256": sha256,
        "raw": contract,
    }


async def main(args: argparse.Namespace) -> None:
    portfolio = json.loads((ROOT / "site/data/municipalities.json").read_text(encoding="utf-8"))
    municipalities = portfolio.get("municipalities", [])
    by_cnpj = {digits(m.get("cnpj")): m for m in municipalities}
    published = ROOT / "data/published"
    published.mkdir(parents=True, exist_ok=True)
    connector = PNCPConnector(str(ROOT / "data/raw"))
    start = args.start or f"{date.today().year}0101"
    end = args.end or date.today().strftime("%Y%m%d")
    contracts: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, Any]] = []

    for index, municipality in enumerate(municipalities, 1):
        cnpj = digits(municipality.get("cnpj"))
        page = 1
        try:
            while True:
                result = await connector.contracts_by_period(start, end, page, args.page_size, cnpj)
                items = payload_items(result.payload)
                for item in items:
                    normalized = normalize(item, by_cnpj, result.fetched_at, result.url, result.sha256)
                    key = str(normalized.get("source_record_id") or f"{cnpj}:{normalized.get('ano')}:{normalized.get('numero')}")
                    contracts[key] = normalized
                pages = total_pages(result.payload)
                print(f"PNCP {index}/{len(municipalities)} {municipality['name']} página {page}/{pages} — {len(items)} registro(s)")
                if page >= pages or not items:
                    break
                page += 1
                if args.max_pages and page > args.max_pages:
                    break
        except Exception as exc:
            errors.append({
                "municipality": municipality.get("name"),
                "cnpj": municipality.get("cnpj"),
                "error": type(exc).__name__,
                "message": str(exc)[:500] or "Não informado pela fonte",
            })
            print(f"PNCP {index}/{len(municipalities)} {municipality['name']} — ERRO {type(exc).__name__}")

    ordered = sorted(
        contracts.values(),
        key=lambda x: (str(x.get("municipality_name") or ""), str(x.get("ano") or ""), str(x.get("numero") or "")),
    )
    (published / "contracts.json").write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")
    (published / "pncp_errors.json").write_text(json.dumps(errors, ensure_ascii=False, indent=2), encoding="utf-8")
    site_data = ROOT / "site/data"
    site_data.mkdir(parents=True, exist_ok=True)
    (site_data / "contracts.json").write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")
    status = {
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "source": "PNCP",
        "period": {"start": start, "end": end},
        "municipalities_total": len(municipalities),
        "contracts": len(ordered),
        "errors": len(errors),
        "policy": "official_only",
    }
    (published / "pncp_sync_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(status, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sincroniza contratos PNCP para os municípios da carteira.")
    parser.add_argument("--start", help="Data inicial no formato AAAAMMDD. Padrão: 1º de janeiro do ano atual.")
    parser.add_argument("--end", help="Data final no formato AAAAMMDD. Padrão: hoje.")
    parser.add_argument("--page-size", type=int, default=50)
    parser.add_argument("--max-pages", type=int, default=0, help="Limite de páginas por município; 0 = sem limite.")
    asyncio.run(main(parser.parse_args()))
