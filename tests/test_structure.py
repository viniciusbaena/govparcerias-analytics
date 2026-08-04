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
    assert {
        'commitment_issued', 'payable_document_issued',
        'payment_order_issued', 'bank_order_issued'
    } <= {row['event_type'] for row in integrated['timeline']}
    assert all(
        row['source_url'] == 'Não informado pela fonte' or row['source_url'].startswith('https://')
        for row in integrated['timeline']
    )
    assert all(row['ibge_code'] in allowed_ibge for row in integrated['instrument_relations'])
    assert all({
        'partnership_ids', 'goal_count', 'schedule_count', 'analysis_count',
        'indicator_count', 'indicators', 'resource_count', 'resources', 'commitment_count',
        'payable_document_count', 'payment_order_count', 'bank_statement_count'
    } <= set(row) for row in integrated['instrument_relations'])
    assert integrated['financial']['records']['proposal_indicators'] >= 0
    assert integrated['financial']['records']['proposal_resources'] >= 0
    project_commitments = json.loads((ROOT / 'data/published/obrasgov/project_commitments.json').read_text(encoding='utf-8'))
    assert integrated['financial']['records']['project_commitments'] == 825
    assert integrated['financial']['obrasgov_commitment_total'] == sum(
        row['valor_empenho'] for row in project_commitments if row.get('valor_empenho') is not None
    )
    assert integrated['financial']['records']['commitments'] == 1517
    assert integrated['financial']['commitment_total'] == 422753821.0
    assert len(integrated['documents']) == integrated['financial']['records']['payable_documents']
    assert len(integrated['documents']) == 1143
    assert all(row['document_id'] and row['partnership_id'] and row['sha256'] for row in integrated['documents'])
    assert all(row['source_url'].startswith('https://api-publica.transferegov.gestao.gov.br/') for row in integrated['documents'])
    assert len(integrated['payment_orders']) == integrated['financial']['records']['payment_orders']
    assert len(integrated['payment_orders']) == 1142
    assert integrated['financial']['payment_order_total'] == 299975085.0
    assert all(row['payment_order_id'] and row['document_id'] and row['sha256'] for row in integrated['payment_orders'])
    assert len(integrated['accounts']) == integrated['financial']['records']['partnership_accounts']
    assert len(integrated['accounts']) == 1963
    assert all(row['account_id'] and row['partnership_id'] and row['sha256'] for row in integrated['accounts'])
    assert integrated['sync_status']['partnership_accounts']['completed'] is True
    assert integrated['sync_status']['partnership_accounts']['processed_roots'] == 1935
    assert integrated['financial']['records']['bank_statements'] == 30634
    assert integrated['sync_status']['bank_statements']['completed'] is True
    assert integrated['sync_status']['bank_statements']['processed_roots'] == 1963
    assert integrated['financial']['records']['proposal_indicators'] == 52
    assert integrated['financial']['records']['proposal_resources'] == 1885
    assert integrated['financial']['records']['proposal_goals'] == 2019
    assert integrated['financial']['records']['proposal_analyses'] == 1912
    assert integrated['sync_status']['proposal_goals']['completed'] is True
    assert integrated['sync_status']['proposal_analyses']['completed'] is True
    assert integrated['sync_status']['proposal_indicators']['completed'] is True
    assert integrated['sync_status']['proposal_resources']['completed'] is True
    assert integrated['sync_status']['disbursement_schedule']['completed'] is True
    assert integrated['sync_status']['commitments']['completed'] is True
    assert integrated['sync_status']['payable_documents']['completed'] is True
    assert integrated['sync_status']['payable_documents']['processed_roots'] == 1935
    assert integrated['sync_status']['payment_orders']['completed'] is True
    assert integrated['sync_status']['payment_orders']['processed_roots'] == 1143
    assert integrated['sync_status']['project_commitments']['completed'] is True
    assert integrated['sync_status']['project_interruptions']['completed'] is True
    assert integrated['sync_status']['physical_execution']['completed'] is False
    assert integrated['sync_status']['physical_execution']['errors'] == 1
    assert integrated['sync_status']['feasibility_studies']['completed'] is False
    assert integrated['sync_status']['feasibility_studies']['errors'] == 1
    assert integrated['integrity']['ambiguous_relationships'] == 2
    physical_errors = json.loads((ROOT / 'data/published/obrasgov/physical_execution_errors.json').read_text(encoding='utf-8'))
    feasibility_errors = json.loads((ROOT / 'data/published/obrasgov/feasibility_studies_errors.json').read_text(encoding='utf-8'))
    assert physical_errors == [{
        'entity': 'physical_execution',
        'root': '3106.41-04',
        'page': 1,
        'error': 'AmbiguousOfficialKey',
        'message': 'A fonte retornou múltiplos registros sem identificador próprio além de id_projeto_investimento.'
    }]
    assert feasibility_errors == [{
        'entity': 'feasibility_studies',
        'root': '103239.41-90',
        'page': 1,
        'error': 'AmbiguousOfficialKey',
        'message': 'A fonte retornou múltiplos registros sem identificador próprio além de id_projeto_investimento.'
    }]
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
    assert 'Estado dos conectores' in app
    assert 'function projectHaystack' in app
    assert 'function documentHaystack' in app
    assert 'function paymentOrderHaystack' in app
    assert 'function accountHaystack' in app
    assert 'function assistantTerms' in app
    assert 'Documentos hábeis oficiais' in app
    assert 'Obras oficiais' in app
    for page in ('Inteligência financeira', 'Centro de documentos e proveniência', 'Timeline integrada', 'Risco e conformidade'):
        assert page in app
