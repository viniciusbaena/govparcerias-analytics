from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_integrated_dataset",
    ROOT / "scripts/build_integrated_dataset.py",
)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


def test_atomic_integrated_write_retries_transient_windows_lock(tmp_path, monkeypatch):
    target = tmp_path / "integrated.json"
    original_replace = Path.replace
    attempts = {"count": 0}

    def flaky_replace(path, destination):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise PermissionError("arquivo temporariamente bloqueado")
        return original_replace(path, destination)

    monkeypatch.setattr(Path, "replace", flaky_replace)
    monkeypatch.setattr(module.time, "sleep", lambda _delay: None)
    module.write_json(target, {"policy": "official_only"})

    assert attempts["count"] == 3
    assert json.loads(target.read_text(encoding="utf-8")) == {"policy": "official_only"}
    assert list(tmp_path.glob("*.tmp")) == []


def test_discretionary_fragments_preserve_official_relationships():
    integrated = json.loads((ROOT / "site/data/integrated.json").read_text(encoding="utf-8"))
    meta = integrated["transferegov_discretionary"]
    assert meta["fragmented"] is True
    records = {
        name: json.loads((ROOT / "site" / entry["path"].replace("data/", "data/")).read_text(encoding="utf-8"))
        for name, entry in meta["records"].items()
    }
    proposals = {str(row["ID_PROPOSTA"]) for row in records["proposals"]}
    agreements = {str(row["NR_CONVENIO"]) for row in records["agreements"]}
    procurements = {str(row["ID_LICITACAO"]) for row in records["procurements"]}
    assert all(str(row["ID_PROPOSTA"]) in proposals for row in records["agreements"])
    assert all(str(row["NR_CONVENIO"]) in agreements for row in records["procurements"])
    assert all(str(row["ID_LICITACAO"]) in procurements for row in records["contracts"])
    assert all(str(row["NR_CONVENIO"]) in agreements for kind in ("commitments", "disbursements", "payments") for row in records[kind])
