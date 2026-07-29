from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from datetime import date
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
SPEC = importlib.util.spec_from_file_location("sync_pncp_contracts", ROOT / "scripts/sync_pncp_contracts.py")
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(module)

from app.connectors.base import FetchResult
from app.connectors.pncp import PNCPConnector


class FakeConnector:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    async def contracts_by_period(self, start, end, page, page_size, cnpj):
        self.calls.append((start, end, page, page_size, cnpj))
        return FetchResult("PNCP", "https://pncp.gov.br/api/consulta/v1/contratos", "2026-07-29T12:00:00+00:00", 200, self.payload, "abc")


def municipality():
    return {"name": "Maringá", "cnpj": "76.282.656/0001-06", "ibge_code": "4115200"}


def contract(key="76282656000106-2-000001/2026"):
    return {
        "numeroControlePNCP": key,
        "numeroContratoEmpenho": "1",
        "anoContrato": 2026,
        "orgaoEntidade": {"cnpj": "76282656000106", "razaoSocial": "MUNICIPIO DE MARINGA"},
        "unidadeOrgao": {"codigoIbge": "4115200", "municipioNome": "Maringá"},
    }


def test_incremental_upsert_preserves_existing_contracts(tmp_path):
    output = tmp_path / "contracts.json"
    output.write_text(json.dumps([{"source_record_id": "old", "source": "PNCP"}]), encoding="utf-8")
    connector = FakeConnector({"data": [contract()], "totalPaginas": 1})
    status = asyncio.run(module.synchronize(
        connector, [municipality()], output, tmp_path / "checkpoint.json",
        tmp_path / "status.json", tmp_path / "errors.json",
        date(2026, 7, 1), date(2026, 7, 31), page_size=500,
    ))
    rows = json.loads(output.read_text(encoding="utf-8"))
    assert {row["source_record_id"] for row in rows} == {"old", "76282656000106-2-000001/2026"}
    assert status["completed"] is True
    assert status["upsert_key"] == "numeroControlePNCP"


def test_missing_official_key_is_recorded_and_not_published(tmp_path):
    connector = FakeConnector({"data": [contract(key=None)], "totalPaginas": 1})
    output = tmp_path / "contracts.json"
    status = asyncio.run(module.synchronize(
        connector, [municipality()], output, tmp_path / "checkpoint.json",
        tmp_path / "status.json", tmp_path / "errors.json",
        date(2026, 7, 1), date(2026, 7, 31),
    ))
    assert json.loads(output.read_text(encoding="utf-8")) == []
    errors = json.loads((tmp_path / "errors.json").read_text(encoding="utf-8"))
    assert errors[0]["error"] == "AmbiguousOfficialRecord"
    assert status["errors"] == 1


def test_response_outside_portfolio_is_rejected(tmp_path):
    bad = contract()
    bad["unidadeOrgao"]["codigoIbge"] = "9999999"
    connector = FakeConnector({"data": [bad], "totalPaginas": 1})
    asyncio.run(module.synchronize(
        connector, [municipality()], tmp_path / "contracts.json", tmp_path / "checkpoint.json",
        tmp_path / "status.json", tmp_path / "errors.json",
        date(2026, 7, 1), date(2026, 7, 31),
    ))
    assert json.loads((tmp_path / "contracts.json").read_text(encoding="utf-8")) == []
    assert "IBGE retornado" in json.loads((tmp_path / "errors.json").read_text(encoding="utf-8"))[0]["message"]


def test_pncp_connector_retries_429_5xx_and_transport_errors(monkeypatch, tmp_path):
    attempts = 0

    async def handler(request):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ReadTimeout("temporário", request=request)
        if attempts == 2:
            return httpx.Response(429, request=request, headers={"Retry-After": "0"})
        if attempts == 3:
            return httpx.Response(503, request=request)
        return httpx.Response(204, request=request)

    transport = httpx.MockTransport(handler)
    original = httpx.AsyncClient

    def client(*args, **kwargs):
        kwargs["transport"] = transport
        return original(*args, **kwargs)

    waits = []

    async def no_sleep(delay):
        waits.append(delay)

    monkeypatch.setattr(httpx, "AsyncClient", client)
    monkeypatch.setattr("app.connectors.base.asyncio.sleep", no_sleep)
    connector = PNCPConnector(str(tmp_path), retries=3, min_delay=0)
    result = asyncio.run(connector.contracts_by_period("20260101", "20260131", cnpj_orgao="76.282.656/0001-06"))
    assert result.payload == []
    assert attempts == 4
    assert len(waits) == 3
