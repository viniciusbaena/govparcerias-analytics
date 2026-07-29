import json
import re
from pathlib import Path

from backend.app.services.portfolio import is_valid_cnpj

ROOT = Path(__file__).resolve().parents[1]

def test_portfolio_has_121_unique_municipalities():
    data = json.loads((ROOT / 'site/data/municipalities.json').read_text(encoding='utf-8'))
    rows = data['municipalities']
    assert len(rows) == 121
    assert len({r['ibge_code'] for r in rows}) == 121
    assert len({re.sub(r'\D', '', r['cnpj']) for r in rows}) == 121
    assert all(set(r) == {'name', 'cnpj', 'ibge_code'} for r in rows)


def test_all_cnpj_checksums_are_valid():
    data = json.loads((ROOT / 'site/data/municipalities.json').read_text(encoding='utf-8'))
    assert all(is_valid_cnpj(r['cnpj']) for r in data['municipalities'])


def test_portfolio_is_not_mislabeled_as_official():
    manifest = json.loads((ROOT / 'source-data/manifest.json').read_text(encoding='utf-8'))
    assert 'Não equivalem' in manifest['provenance_note']


def test_contract_axis_remains_present():
    app = (ROOT / 'site/assets/app.js').read_text(encoding='utf-8')
    assert 'Dossiê integral por contrato' in app
    assert 'Contratos e propostas' in app
