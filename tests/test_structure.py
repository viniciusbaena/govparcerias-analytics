import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_official_only_dataset():
    data=json.loads((ROOT/'site/data/demo.json').read_text(encoding='utf-8'))
    assert data['data_mode']=='official_only'
    assert data['municipios']==[] and data['parcerias']==[]
    assert data['updated_at'] is None

def test_dossier_contract_has_finance_and_engineering():
    c=json.loads((ROOT/'site/data/dossier-contract.json').read_text(encoding='utf-8'))
    ids={x['id'] for x in c['sections']}
    required={'financeiro','origens','empenhos','documentos_habeis','ordens_pagamento','contas','extratos','obras','documentos_engenharia','vistorias','licitacoes_contratos','prestacao_contas','proveniencia'}
    assert required <= ids

def test_no_fictitious_entities_in_public_data():
    text=(ROOT/'site/data/demo.json').read_text(encoding='utf-8').casefold()
    for term in ['município alfa','órgão federal a','900001/2025']:
        assert term not in text


def test_v120_publishes_official_data_and_uses_csp_safe_actions():
    proposals = json.loads((ROOT / 'site/data/proposals.json').read_text(encoding='utf-8'))
    contracts = json.loads((ROOT / 'site/data/contracts.json').read_text(encoding='utf-8'))
    app = (ROOT / 'site/assets/app.js').read_text(encoding='utf-8')
    assert len(proposals) == 1935
    assert len({row['source_record_id'] for row in proposals}) == 1935
    assert all(row['source'] == 'Transferegov - Gestão de Parcerias' for row in proposals)
    assert len(contracts) >= 45
    assert len({row['source_record_id'] for row in contracts}) == len(contracts)
    assert all(row['source'] == 'PNCP' for row in contracts)
    assert 'v1.2.0-alpha' in app
    assert "safeJson('data/proposals.json',[])" in app
    assert 'proposalHaystack' in app
    assert 'data-action="municipality-page"' in app
    assert 'data-action="open-contract"' in app
    assert 'data-action="open-proposal"' in app
    assert 'data-action="show"' in app
    assert 'data-action="assistant-query"' in app
    assert ' onclick="' not in app
