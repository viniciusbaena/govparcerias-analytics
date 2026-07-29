from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
SPEC = importlib.util.spec_from_file_location("sync_transferegov_graph", ROOT / "scripts/sync_transferegov_graph.py")
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)

from app.connectors.transferegov import OfficialResponse


class FakeConnector:
    def __init__(self, rows_by_root):
        self.rows_by_root = rows_by_root
        self.calls = []

    async def get_json(self, url, params):
        self.calls.append((url, dict(params)))
        root = str(params["id_proposta"])
        return OfficialResponse(
            payload={"data": self.rows_by_root.get(root, []), "total_pages": 1},
            url=f"{url}?id_proposta={root}",
            fetched_at="2026-07-29T12:00:00+00:00",
            sha256="abc",
            status_code=200,
        )


def prepare(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "ROOT", tmp_path)
    published = tmp_path / "data/published/transferegov"
    published.mkdir(parents=True)
    (published / "proposals.json").write_text(
        json.dumps([{"id_proposta": 10}, {"id_proposta": 20}]),
        encoding="utf-8",
    )
    return published


def test_graph_sync_uses_official_parent_and_primary_keys(tmp_path, monkeypatch):
    published = prepare(tmp_path, monkeypatch)
    connector = FakeConnector({
        "10": [{"id_parceria": 100, "id_proposta": 10}],
        "20": [{"id_parceria": 200, "id_proposta": 20}],
    })
    status = asyncio.run(module.synchronize_entity(connector, module.SPECS["partnerships"], page_size=50))
    rows = json.loads((published / "partnerships.json").read_text(encoding="utf-8"))
    assert {row["source_record_id"] for row in rows} == {"100", "200"}
    assert all(call[1]["tamanho_da_pagina"] == 50 for call in connector.calls)
    assert status["completed"] is True
    assert status["errors"] == 0


def test_graph_sync_rejects_ambiguous_parent_without_deleting_existing(tmp_path, monkeypatch):
    published = prepare(tmp_path, monkeypatch)
    (published / "partnerships.json").write_text(
        json.dumps([{"source_record_id": "old", "id_parceria": "old", "id_proposta": 10}]),
        encoding="utf-8",
    )
    connector = FakeConnector({
        "10": [{"id_parceria": 100, "id_proposta": 999}],
        "20": [],
    })
    status = asyncio.run(module.synchronize_entity(connector, module.SPECS["partnerships"]))
    rows = json.loads((published / "partnerships.json").read_text(encoding="utf-8"))
    errors = json.loads((published / "partnerships_errors.json").read_text(encoding="utf-8"))
    assert [row["source_record_id"] for row in rows] == ["old"]
    assert errors[0]["error"] == "AmbiguousParentRelationship"
    assert status["errors"] == 1


def test_all_graph_entities_declare_unambiguous_keys():
    assert len(module.SPECS) == 11
    for spec in module.SPECS.values():
        assert spec.primary_key.startswith("id_")
        assert spec.parent_key.startswith("id_")
        assert spec.roots_from == "proposals" or spec.roots_from in module.SPECS


def test_atomic_json_write_retries_transient_windows_lock(tmp_path, monkeypatch):
    target = tmp_path / "checkpoint.json"
    original_replace = Path.replace
    attempts = {"count": 0}

    def flaky_replace(path, destination):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise PermissionError("arquivo temporariamente bloqueado")
        return original_replace(path, destination)

    monkeypatch.setattr(Path, "replace", flaky_replace)
    monkeypatch.setattr(module.time, "sleep", lambda _delay: None)
    module.write_json(target, {"root_index": 42})

    assert attempts["count"] == 3
    assert json.loads(target.read_text(encoding="utf-8")) == {"root_index": 42}
    assert list(tmp_path.glob("*.tmp")) == []
