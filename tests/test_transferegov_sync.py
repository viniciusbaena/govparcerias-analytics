from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
SPEC = importlib.util.spec_from_file_location(
    "sync_transferegov_proposals",
    ROOT / "scripts/sync_transferegov_proposals.py",
)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(module)

from app.connectors.transferegov import OfficialResponse, TransferegovConnector
from app.services.portfolio import validate_portfolio


def response(payload, url="https://official.test/proposta") -> OfficialResponse:
    return OfficialResponse(payload, url, "2026-07-29T12:00:00+00:00", "abc123", 200)


def test_canonical_portfolio_has_exactly_121_minimal_records():
    rows = validate_portfolio(
        ROOT / "site/data/municipalities.json",
        ROOT / "source-data/Planilha 121 municipios.xlsx",
    )
    assert len(rows) == 121
    assert all(set(row) == {"name", "cnpj", "ibge_code"} for row in rows)


class FakeConnector:
    def __init__(self):
        self.pages = []

    async def get_json(self, url, params):
        self.pages.append(dict(params))
        page = params["pagina"]
        item = {
            "id_proposta": page,
            "cd_ibge_recebedor": int(params["cd_ibge_recebedor"]),
            "nm_ente_recebedor": None,
        }
        return response(
            {
                "data": [item],
                "total_pages": 2,
                "total_items": 2,
                "page_number": page,
                "page_size": 1,
            }
        )


def test_pagination_checkpoint_and_upsert_preserve_previous_records(tmp_path):
    output = tmp_path / "proposals.json"
    output.write_text(
        json.dumps([{"source_record_id": "99", "id_proposta": 99}]),
        encoding="utf-8",
    )
    municipality = {
        "name": "Maringá",
        "cnpj": "76.282.656/0001-06",
        "ibge_code": "4115200",
    }
    connector = FakeConnector()
    status = asyncio.run(
        module.synchronize(
            connector,
            [municipality],
            output,
            tmp_path / "checkpoint.json",
            tmp_path / "status.json",
            tmp_path / "raw",
            page_size=1,
        )
    )
    records = json.loads(output.read_text(encoding="utf-8"))
    checkpoint = json.loads((tmp_path / "checkpoint.json").read_text(encoding="utf-8"))
    assert [call["pagina"] for call in connector.pages] == [1, 2]
    assert {row["source_record_id"] for row in records} == {"1", "2", "99"}
    assert checkpoint["completed"] is True
    assert status["records_published"] == 3
    assert status["resume_from_index"] == 0
    assert status["municipalities_processed_this_run"] == 1
    assert status["municipalities_completed_total"] == 1
    normalized = next(row for row in records if row["source_record_id"] == "1")
    assert normalized["receiver_name"] == "Não informado pela fonte"


def test_checkpoint_resume_starts_at_saved_page(tmp_path):
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text(
        json.dumps(
            {
                "endpoint": module.ENDPOINT,
                "municipality_index": 0,
                "next_page": 2,
                "scope_sha256": module.checkpoint_scope(
                    [{"ibge_code": "4115200"}]
                ),
            }
        ),
        encoding="utf-8",
    )
    connector = FakeConnector()
    asyncio.run(
        module.synchronize(
            connector,
            [{"name": "Maringá", "cnpj": "76.282.656/0001-06", "ibge_code": "4115200"}],
            tmp_path / "out.json",
            checkpoint,
            tmp_path / "status.json",
            tmp_path / "raw",
            page_size=1,
        )
    )
    assert [call["pagina"] for call in connector.pages] == [2]


def test_page_limit_leaves_checkpoint_on_next_page(tmp_path):
    connector = FakeConnector()
    checkpoint = tmp_path / "checkpoint.json"
    status = asyncio.run(
        module.synchronize(
            connector,
            [{"name": "Maringá", "cnpj": "76.282.656/0001-06", "ibge_code": "4115200"}],
            tmp_path / "out.json",
            checkpoint,
            tmp_path / "status.json",
            tmp_path / "raw",
            page_size=1,
            max_pages=1,
        )
    )
    saved = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert [call["pagina"] for call in connector.pages] == [1]
    assert saved["next_page"] == 2
    assert saved["completed"] is False
    assert status["partial"] is True


def test_incomplete_checkpoint_from_another_scope_is_rejected(tmp_path):
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text(
        json.dumps(
            {
                "endpoint": module.ENDPOINT,
                "municipality_index": 0,
                "next_page": 2,
                "scope_sha256": "different-scope",
                "completed": False,
            }
        ),
        encoding="utf-8",
    )
    try:
        asyncio.run(
            module.synchronize(
                FakeConnector(),
                [{"name": "Maringá", "cnpj": "76.282.656/0001-06", "ibge_code": "4115200"}],
                tmp_path / "out.json",
                checkpoint,
                tmp_path / "status.json",
                tmp_path / "raw",
            )
        )
    except ValueError as exc:
        assert "outro escopo" in str(exc)
    else:
        raise AssertionError("Checkpoint ambíguo deveria ser recusado.")


def test_atomic_write_retries_transient_permission_error(monkeypatch, tmp_path):
    original = Path.replace
    attempts = []

    def flaky_replace(path, target):
        attempts.append(str(target))
        if len(attempts) < 3:
            raise PermissionError("arquivo temporariamente bloqueado")
        return original(path, target)

    monkeypatch.setattr(Path, "replace", flaky_replace)
    monkeypatch.setattr(module.time, "sleep", lambda _: None)
    target = tmp_path / "status.json"
    module.write_json(target, {"ok": True})
    assert json.loads(target.read_text(encoding="utf-8")) == {"ok": True}
    assert len(attempts) == 3


def test_ibge_mismatch_stops_without_publishing(tmp_path):
    class WrongMunicipalityConnector:
        async def get_json(self, url, params):
            return response(
                {
                    "data": [{"id_proposta": 1, "cd_ibge_recebedor": 9999999}],
                    "total_pages": 1,
                    "page_number": 1,
                }
            )

    status = asyncio.run(
        module.synchronize(
            WrongMunicipalityConnector(),
            [{"name": "Maringá", "cnpj": "76.282.656/0001-06", "ibge_code": "4115200"}],
            tmp_path / "out.json",
            tmp_path / "checkpoint.json",
            tmp_path / "status.json",
            tmp_path / "raw",
        )
    )
    assert status["errors"][0]["error"] == "ApiContractError"
    assert not (tmp_path / "out.json").exists()


def test_connector_retries_429_and_5xx(monkeypatch, tmp_path):
    statuses = iter([429, 503, 200])

    async def handler(request):
        status = next(statuses)
        return httpx.Response(
            status,
            request=request,
            json={"data": []},
            headers={"Retry-After": "0"} if status == 429 else {},
        )

    transport = httpx.MockTransport(handler)
    original = httpx.AsyncClient

    def client(*args, **kwargs):
        kwargs["transport"] = transport
        return original(*args, **kwargs)

    waits = []

    async def no_sleep(delay):
        waits.append(delay)

    monkeypatch.setattr(httpx, "AsyncClient", client)
    monkeypatch.setattr("app.connectors.transferegov.asyncio.sleep", no_sleep)
    connector = TransferegovConnector(tmp_path, retries=3, min_delay=0)
    result = asyncio.run(connector.get_json("https://official.test/proposta"))
    assert result.status_code == 200
    assert len(waits) == 3  # two retry waits plus the configured post-success delay
