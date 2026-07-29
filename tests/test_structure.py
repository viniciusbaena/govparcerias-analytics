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
    assert 'v1.3.0-alpha' in app
    assert "safeJson('data/proposals.json',[])" in app
    assert 'proposalHaystack' in app
    assert 'data-action="municipality-page"' in app
    assert 'data-action="open-contract"' in app
    assert 'data-action="open-proposal"' in app
    assert 'data-action="show"' in app
    assert 'data-action="assistant-query"' in app
    assert ' onclick="' not in app


def test_v130_integrated_dataset_is_official_and_scoped():
    integrated = json.loads((ROOT / 'site/data/integrated.json').read_text(encoding='utf-8'))
    municipalities = json.loads((ROOT / 'site/data/municipalities.json').read_text(encoding='utf-8'))['municipalities']
    allowed_ibge = {row['ibge_code'] for row in municipalities}
    assert integrated['policy'] == 'official_only'
    assert integrated['counts']['municipalities'] == 121
    assert integrated['counts']['proposals'] == 1935
    assert all(row['ibge_code'] in allowed_ibge for row in integrated['instrument_relations'])
    project_commitments = json.loads((ROOT / 'data/published/obrasgov/project_commitments.json').read_text(encoding='utf-8'))
    assert integrated['financial']['records']['project_commitments'] == 825
    assert integrated['financial']['obrasgov_commitment_total'] == sum(
        row['valor_empenho'] for row in project_commitments if row.get('valor_empenho') is not None
    )
    assert integrated['financial']['records']['commitments'] == 1517
    assert integrated['financial']['commitment_total'] == 422753821.0
    assert integrated['sync_status']['disbursement_schedule']['completed'] is True
    assert integrated['sync_status']['commitments']['completed'] is True
    assert integrated['sync_status']['payable_documents']['completed'] is False
    assert integrated['sync_status']['payable_documents']['processed_roots'] == 578
    assert integrated['sync_status']['project_commitments']['completed'] is True
    assert integrated['sync_status']['project_interruptions']['completed'] is True
    assert integrated['sync_status']['physical_execution']['completed'] is False
    assert integrated['sync_status']['physical_execution']['errors'] == 1
    assert integrated['integrity']['ambiguous_relationships'] == 0
    assert {signal['id'] for signal in integrated['integrity']['signals']} == {
        'contract-term-ended', 'project-source-status-interrupted',
        'project-official-interruption-history'
    }
    assert all('não presume irregularidade' in signal['classification'].casefold() for signal in integrated['integrity']['signals'])
    app = (ROOT / 'site/assets/app.js').read_text(encoding='utf-8')
    assert "safeJson('data/integrated.json'" in app
    assert 'ObrasGov por código IBGE' in app
    assert 'Fonte ainda não sincronizada' not in app
    assert 'Comparação dos 121 municípios' in app
    for page in ('Inteligência financeira', 'Centro de documentos e proveniência', 'Timeline integrada', 'Risco e conformidade'):
        assert page in app
