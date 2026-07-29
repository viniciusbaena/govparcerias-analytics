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
