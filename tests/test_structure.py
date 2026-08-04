import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_readme_links_published_manifest():
    readme=(ROOT/'README.md').read_text(encoding='utf-8')
    manifest=ROOT/'data/published/integrated_status.json'
    assert manifest.exists()
    assert 'data/published/integrated_status.json' in readme

def test_release_audit_passes_with_documented_ambiguities():
    audit=json.loads((ROOT/'data/published/release_audit.json').read_text(encoding='utf-8'))
    assert audit['status']=='passed'
    assert audit['municipalities']==121
    assert set(audit['documented_ambiguities']) == {'physical_execution','feasibility_studies'}

def test_special_transferegov_graph_is_scoped_to_official_plan_ids():
    script=(ROOT/'scripts/sync_transferencias_especiais_graph.py').read_text(encoding='utf-8')
    assert "special_action_plans.json" in script
    assert "id_plano_acao" in script
    assert "executor_especial" in script and "plano_trabalho_especial" in script and "empenho_especial" in script
    assert "api.transferegov.gestao.gov.br/transferenciasespeciais" in script

def test_canonical_portfolio_and_special_plans_scope():
    portfolio=json.loads((ROOT/'site/data/municipalities.json').read_text(encoding='utf-8'))
    municipalities=portfolio['municipalities']
    assert portfolio['manifest']['record_count'] == 121
    assert len(municipalities) == 121
    cnps={row['cnpj'].replace('.','').replace('/','').replace('-','') for row in municipalities}
    ibges={str(row['ibge_code']) for row in municipalities}
    plans=json.loads((ROOT/'data/published/transferegov/special_action_plans.json').read_text(encoding='utf-8'))
    assert plans
    assert all(str(row.get('cnpj_beneficiario_plano_acao','')) in cnps for row in plans)
    assert all(str(row.get('ibge_code','')) in ibges for row in plans)

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
    assert 'v1.5.0-alpha' in app
    assert 'contrato/convênio' in app
    assert "safeJson('data/proposals.json',[])" in app
    assert 'proposalHaystack' in app
    assert 'data-action="municipality-page"' in app
    assert 'data-action="instrument-contract-page"' in app
    assert 'data-action="open-contract"' in app
    assert 'data-action="open-proposal"' in app
    assert 'data-action="show"' in app
    assert 'data-action="assistant-query"' in app
    assert 'Documentos especiais' in app
    assert 'Ordens especiais' in app
    assert 'Relatórios especiais' in app
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
    assert integrated['financial']['records']['special_action_plans'] == 1392
    assert integrated['counts']['special_action_plans'] == 1392
    assert integrated['sync_status']['special_action_plans']['completed'] is True
    special = json.loads((ROOT / 'data/published/transferegov/special_action_plans.json').read_text(encoding='utf-8'))
    allowed_cnpj = {''.join(ch for ch in row['cnpj'] if ch.isdigit()) for row in municipalities}
    assert len(special) == 1392
    assert len({row['source_record_id'] for row in special}) == len(special)
    assert all(row['cnpj_beneficiario_plano_acao'] in allowed_cnpj for row in special)
    assert all(row['source'] == 'Transferegov - Transferências Especiais' for row in special)
    assert integrated['financial']['records']['special_executors'] == 1367
    assert integrated['financial']['records']['special_work_plans'] == 1368
    assert integrated['financial']['records']['special_commitments'] == 1404
    assert integrated['sync_status']['special_executors']['completed'] is True
    assert integrated['sync_status']['special_work_plans']['completed'] is True
    assert integrated['sync_status']['special_commitments']['completed'] is True
    assert integrated['financial']['records']['special_reports'] == 123
    assert integrated['financial']['records']['special_new_reports'] == 582
    assert integrated['sync_status']['special_reports']['completed'] is True
    assert integrated['sync_status']['special_new_reports']['completed'] is True
    assert integrated['financial']['records']['special_documents'] == 1337
    assert integrated['financial']['records']['special_orders'] == 1276
    assert integrated['sync_status']['special_documents']['completed'] is True
    assert integrated['sync_status']['special_orders']['completed'] is True
    assert integrated['financial']['records']['special_purposes'] == 1367
    assert integrated['financial']['records']['special_goals'] == 3830
    assert integrated['sync_status']['special_purposes']['completed'] is True
    assert integrated['sync_status']['special_goals']['completed'] is True
    assert integrated['financial']['records']['special_work_plan_analyses'] == 2989
    assert integrated['financial']['records']['special_pending_organs'] == 41
    assert integrated['sync_status']['special_work_plan_analyses']['completed'] is True
    assert integrated['sync_status']['special_pending_organs']['completed'] is True
    assert integrated['financial']['records']['special_payment_history'] == 6125
    assert integrated['sync_status']['special_payment_history']['completed'] is True
    assert integrated['financial']['records']['special_programs'] == 10
    assert integrated['sync_status']['special_programs']['completed'] is True
    for filename in ('special_programs.json','special_work_plan_analyses.json','special_payment_history.json'):
        rows=json.loads((ROOT/'data/published/transferegov'/filename).read_text(encoding='utf-8'))
        assert rows
        assert all(row.get('source') == 'Transferegov - Transferências Especiais' for row in rows)
        assert all(row.get('source_url','').startswith('https://api.transferegov.gestao.gov.br/') for row in rows)
        assert all(row.get('sha256') for row in rows)
    app = (ROOT / 'site/assets/app.js').read_text(encoding='utf-8')
    assert 'Programas especiais' in app
    assert 'Histórico de pagamentos' in app
    assert 'v3.1.0-alpha' in app
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
    assert integrated['sync_status']['physical_execution']['completed'] is True
    assert integrated['financial']['records'].get('sadipem_pvls', 0) == 1276
    assert integrated['sync_status']['sadipem_pvls']['completed'] is True
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
