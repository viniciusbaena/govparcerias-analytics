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
