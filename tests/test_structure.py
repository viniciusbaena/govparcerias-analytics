from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_public_site_files():
    for rel in ["site/index.html","site/assets/app.js","site/assets/app.css","site/data/demo.json","site/data/modelo-carteira.csv"]:
        assert (ROOT/rel).exists(), rel

def test_demo_data_contract():
    data=json.loads((ROOT/"site/data/demo.json").read_text(encoding="utf-8"))
    assert data["version"]=="0.6.0-alpha"
    assert data["municipios"] and data["parcerias"]
    assert all("valor_per_capita" in x for x in data["municipios"])
    assert all("eventos" in x for x in data["parcerias"])

def test_workflows_present():
    assert (ROOT/".github/workflows/deploy-pages.yml").exists()
    assert (ROOT/".github/workflows/quality.yml").exists()
