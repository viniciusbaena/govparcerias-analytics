import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_portfolio_has_121_unique_municipalities():
    data = json.loads((ROOT / 'site/data/municipalities.json').read_text(encoding='utf-8'))
    rows = data['municipalities']
    assert len(rows) == 121
    assert len({r['ibge_code'] for r in rows}) == 121
    assert len({r['cnpj_digits'] for r in rows}) == 121


def test_all_cnpj_checksums_are_valid():
    data = json.loads((ROOT / 'site/data/municipalities.json').read_text(encoding='utf-8'))
    assert all(r['cnpj_checksum_valid'] for r in data['municipalities'])


def test_portfolio_is_not_mislabeled_as_official():
    data = json.loads((ROOT / 'site/data/municipalities.json').read_text(encoding='utf-8'))
    assert all(r['data_classification'] == 'carteira_de_trabalho' for r in data['municipalities'])
    assert 'Não equivalem' in data['manifest']['provenance_note']


def test_contract_axis_remains_present():
    app = (ROOT / 'site/assets/app.js').read_text(encoding='utf-8')
    assert 'Dossiê integral por contrato' in app
    assert 'Contratos e instrumentos' in app
