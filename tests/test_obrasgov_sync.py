from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
SPEC = importlib.util.spec_from_file_location("sync_obrasgov_graph", ROOT / "scripts/sync_obrasgov_graph.py")
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)

from app.connectors.transferegov import OfficialResponse


class FakeConnector:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    async def get_json(self, url, params):
        self.calls.append((url, dict(params)))
        return OfficialResponse(
            payload={"data": self.rows, "total_pages": 1},
            url=url,
            fetched_at="2026-07-29T12:00:00+00:00",
            sha256="abc",
            status_code=200,
        )


def prepare(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "PUBLISHED", tmp_path / "data/published/obrasgov")
    site = tmp_path / "site/data"
    site.mkdir(parents=True)
    (site / "municipalities.json").write_text(json.dumps({
        "municipalities": [{"name": "Maringá", "cnpj": "76.282.656/0001-06", "ibge_code": "4115200"}]
    }), encoding="utf-8")


def test_geometry_sync_is_filtered_by_portfolio_ibge(tmp_path, monkeypatch):
    prepare(tmp_path, monkeypatch)
    connector = FakeConnector([{"id_geometria": 1, "id_projeto_investimento": "P1", "cod_ibge": 4115200}])
    status = asyncio.run(module.sync_geometries(connector, 200))
    rows = json.loads((module.PUBLISHED / "geometries.json").read_text(encoding="utf-8"))
    assert rows[0]["source_record_id"] == "1"
    assert rows[0]["municipality_cnpj"] == "76.282.656/0001-06"
    assert connector.calls[0][1]["cod_ibge"] == "4115200"
    assert status["completed"] is True


def test_geometry_sync_rejects_response_from_other_ibge(tmp_path, monkeypatch):
    prepare(tmp_path, monkeypatch)
    connector = FakeConnector([{"id_geometria": 1, "id_projeto_investimento": "P1", "cod_ibge": 9999999}])
    status = asyncio.run(module.sync_geometries(connector, 200))
    assert json.loads((module.PUBLISHED / "geometries.json").read_text(encoding="utf-8")) == []
    errors = json.loads((module.PUBLISHED / "geometries_errors.json").read_text(encoding="utf-8"))
    assert errors[0]["error"] == "AmbiguousTerritory"
    assert status["errors"] == 1


def test_obrasgov_children_are_rooted_in_project_id():
    assert set(module.CHILD_SPECS) == {
        "projects", "physical_execution", "project_contracts", "project_commitments",
        "project_geometries", "project_interruptions", "feasibility_studies",
    }


def test_atomic_json_write_retries_transient_windows_lock(tmp_path, monkeypatch):
    target = tmp_path / "checkpoint.json"
    original_replace = Path.replace
    attempts = {"count": 0}

    def flaky_replace(path, destination):
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise PermissionError("arquivo temporariamente bloqueado")
        return original_replace(path, destination)

    monkeypatch.setattr(Path, "replace", flaky_replace)
    monkeypatch.setattr(module.time, "sleep", lambda _delay: None)
    module.write_json(target, {"root_index": 7})

    assert attempts["count"] == 2
    assert json.loads(target.read_text(encoding="utf-8")) == {"root_index": 7}
    assert list(tmp_path.glob("*.tmp")) == []
