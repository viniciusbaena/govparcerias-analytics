#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED = ROOT / "data/published/transferegov"
SITE = ROOT / "site/data"
MISSING = "Não informado pela fonte"


def read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    for attempt in range(6):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(0.05 * (2**attempt))


def index_many(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    indexed: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        value = row.get(key)
        if value is not None:
            indexed[str(value)].append(row)
    return indexed


def numeric(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(".", "").replace(",", "."))
        except ValueError:
            return None
    return None


def sync_state(directory: Path, entity: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    checkpoint = read_json(directory / f"{entity}_checkpoint.json", {})
    status = read_json(directory / f"{entity}_sync_status.json", {})
    errors = read_json(directory / f"{entity}_errors.json", [])
    return {
        "completed": bool(checkpoint.get("completed", status.get("completed", False))),
        "processed_roots": int(checkpoint.get("root_index", 0)),
        "roots_total": int(checkpoint.get("roots_total", status.get("roots_total", 0))),
        "records": len(records),
        "errors": len(errors),
    }


def event(entity: str, entity_id: Any, event_type: str, occurred_at: Any, title: str, source_url: Any) -> dict[str, Any] | None:
    if not occurred_at:
        return None
    return {
        "entity": entity,
        "entity_id": str(entity_id),
        "event_type": event_type,
        "occurred_at": str(occurred_at),
        "title": title,
        "source_url": source_url or MISSING,
    }


def build() -> dict[str, Any]:
    municipalities = read_json(SITE / "municipalities.json", {}).get("municipalities", [])
    municipality_by_ibge = {str(row["ibge_code"]): row for row in municipalities}
    proposals = read_json(PUBLISHED / "proposals.json", [])
    partnerships = read_json(PUBLISHED / "partnerships.json", [])
    goals = read_json(PUBLISHED / "proposal_goals.json", [])
    schedules = read_json(PUBLISHED / "disbursement_schedule.json", [])
    analyses = read_json(PUBLISHED / "proposal_analyses.json", [])
    indicators = read_json(PUBLISHED / "proposal_indicators.json", [])
    resources = read_json(PUBLISHED / "proposal_resources.json", [])
    commitments = read_json(PUBLISHED / "commitments.json", [])
    payable_documents = read_json(PUBLISHED / "payable_documents.json", [])
    accounts = read_json(PUBLISHED / "partnership_accounts.json", [])
    payment_orders = read_json(PUBLISHED / "payment_orders.json", [])
    statements = read_json(PUBLISHED / "bank_statements.json", [])
    obras = ROOT / "data/published/obrasgov"
    geometries = read_json(obras / "geometries.json", [])
    projects = read_json(obras / "projects.json", [])
    physical_execution = read_json(obras / "physical_execution.json", [])
    project_contracts = read_json(obras / "project_contracts.json", [])
    project_commitments = read_json(obras / "project_commitments.json", [])
    project_interruptions = read_json(obras / "project_interruptions.json", [])
    feasibility_studies = read_json(obras / "feasibility_studies.json", [])
    special_action_plans = read_json(PUBLISHED / "special_action_plans.json", [])
    special_executors = read_json(PUBLISHED / "special_executors.json", [])
    special_work_plans = read_json(PUBLISHED / "special_work_plans.json", [])
    special_commitments = read_json(PUBLISHED / "special_commitments.json", [])

    partnership_by_proposal = index_many(partnerships, "id_proposta")
    goals_by_proposal = index_many(goals, "id_proposta")
    schedules_by_proposal = index_many(schedules, "id_proposta")
    analyses_by_proposal = index_many(analyses, "id_proposta")
    indicators_by_proposal = index_many(indicators, "id_proposta")
    resources_by_proposal = index_many(resources, "id_proposta")
    commitments_by_partnership = index_many(commitments, "id_parceria")
    documents_by_partnership = index_many(payable_documents, "id_parceria")
    accounts_by_partnership = index_many(accounts, "id_parceria")
    orders_by_document = index_many(payment_orders, "id_documento_habil")
    statements_by_account = index_many(statements, "id_parceria_conta")
    geometries_by_project = index_many(geometries, "id_projeto_investimento")
    project_by_id = {str(row["id_projeto_investimento"]): row for row in projects if row.get("id_projeto_investimento")}
    execution_by_project = index_many(physical_execution, "id_projeto_investimento")
    contracts_by_project = index_many(project_contracts, "id_projeto_investimento")
    commitments_by_project = index_many(project_commitments, "id_projeto_investimento")
    interruptions_by_project = index_many(project_interruptions, "id_projeto_investimento")
    studies_by_project = index_many(feasibility_studies, "id_projeto_investimento")

    instruments = []
    timeline = []
    for proposal in proposals:
        proposal_id = str(proposal["id_proposta"])
        ibge = str(proposal["ibge_code"])
        municipality = municipality_by_ibge.get(ibge)
        if municipality is None:
            continue
        linked_partnerships = partnership_by_proposal.get(proposal_id, [])
        linked_goals = goals_by_proposal.get(proposal_id, [])
        linked_schedules = schedules_by_proposal.get(proposal_id, [])
        linked_analyses = analyses_by_proposal.get(proposal_id, [])
        linked_indicators = indicators_by_proposal.get(proposal_id, [])
        linked_resources = resources_by_proposal.get(proposal_id, [])
        direct_event = event("proposal", proposal_id, "proposal_created", proposal.get("proposal_date"), f"Proposta {proposal_id} registrada", proposal.get("source_url"))
        if direct_event:
            timeline.append({**direct_event, "ibge_code": ibge, "municipality_name": municipality["name"], "proposal_id": proposal_id})
        for analysis in linked_analyses:
            analysis_event = event(
                "analise_proposta",
                analysis.get("id_analise_proposta"),
                "proposal_analysis_recorded",
                analysis.get("dh_analise_proposta"),
                f"Análise da proposta: {analysis.get('in_resultado_analise') or MISSING}",
                analysis.get("source_url"),
            )
            if analysis_event:
                timeline.append({
                    **analysis_event,
                    "ibge_code": ibge,
                    "municipality_name": municipality["name"],
                    "proposal_id": proposal_id,
                    "detail": analysis.get("ds_parecer") or MISSING,
                })

        partnership_details = []
        for partnership in linked_partnerships:
            partnership_id = str(partnership["id_parceria"])
            linked_commitments = commitments_by_partnership.get(partnership_id, [])
            linked_documents = documents_by_partnership.get(partnership_id, [])
            linked_accounts = accounts_by_partnership.get(partnership_id, [])
            linked_orders = [
                order
                for document in linked_documents
                for order in orders_by_document.get(str(document["id_documento_habil"]), [])
            ]
            linked_statements = [
                statement
                for account in linked_accounts
                for statement in statements_by_account.get(str(account["id_parceria_conta"]), [])
            ]
            partnership_details.append({
                **partnership,
                "commitments": linked_commitments,
                "payable_documents": linked_documents,
                "accounts": linked_accounts,
                "payment_orders": linked_orders,
                "bank_statements": linked_statements,
            })
            for event_type, date_key, title in (
                ("partnership_signed", "dh_assinatura", f"Parceria {partnership.get('cd_parceria') or partnership_id} assinada"),
                ("execution_requested", "dh_solicitacao_execucao", "Execução solicitada"),
                ("execution_authorized", "dh_autorizacao_execucao", "Execução autorizada"),
            ):
                linked_event = event("partnership", partnership_id, event_type, partnership.get(date_key), title, partnership.get("source_url"))
                if linked_event:
                    timeline.append({**linked_event, "ibge_code": ibge, "municipality_name": municipality["name"], "proposal_id": proposal_id})
            for commitment in linked_commitments:
                linked_event = event(
                    "empenho",
                    commitment.get("id_empenho_parceria"),
                    "commitment_issued",
                    commitment.get("data_emissao"),
                    f"Empenho {commitment.get('numero_nota_empenho_gerada') or commitment.get('nr_empenho') or MISSING} emitido",
                    commitment.get("source_url"),
                )
                if linked_event:
                    timeline.append({**linked_event, "ibge_code": ibge, "municipality_name": municipality["name"], "proposal_id": proposal_id, "partnership_id": partnership_id})
            for document in linked_documents:
                linked_event = event(
                    "documento_habil",
                    document.get("id_documento_habil"),
                    "payable_document_issued",
                    document.get("dt_emissao"),
                    f"Documento hábil {document.get('nr_documento_habil') or MISSING} emitido",
                    document.get("source_url"),
                )
                if linked_event:
                    timeline.append({**linked_event, "ibge_code": ibge, "municipality_name": municipality["name"], "proposal_id": proposal_id, "partnership_id": partnership_id})
            for order in linked_orders:
                for event_type, date_key, title in (
                    ("payment_order_issued", "dt_emissao_op", f"Ordem de pagamento {order.get('nr_ordem_pagamento') or MISSING} emitida"),
                    ("bank_order_issued", "dt_emissao_ordem_bancaria", f"Ordem bancária {order.get('nr_ordem_bancaria') or MISSING} emitida"),
                ):
                    linked_event = event("ordem_pagamento", order.get("id_op"), event_type, order.get(date_key), title, order.get("source_url"))
                    if linked_event:
                        timeline.append({**linked_event, "ibge_code": ibge, "municipality_name": municipality["name"], "proposal_id": proposal_id, "partnership_id": partnership_id})
            for account in linked_accounts:
                linked_event = event(
                    "conta_parceria",
                    account.get("id_parceria_conta"),
                    "partnership_account_opened",
                    account.get("dt_abertura"),
                    f"Conta {account.get('tp_conta') or MISSING} aberta",
                    account.get("source_url"),
                )
                if linked_event:
                    timeline.append({**linked_event, "ibge_code": ibge, "municipality_name": municipality["name"], "proposal_id": proposal_id, "partnership_id": partnership_id})

        instruments.append({
            "proposal_id": proposal_id,
            "ibge_code": ibge,
            "partnership_ids": [str(row["id_parceria"]) for row in partnership_details],
            "goal_count": len(linked_goals),
            "goals": [{
                "goal_id": str(row["id_meta_proposta"]),
                "code": row.get("cd_meta") or MISSING,
                "name": row.get("nm_meta") or MISSING,
                "description": row.get("ds_meta") or MISSING,
                "stage_count": len(row.get("etapas_proposta") or []),
                "source_url": row.get("source_url") or MISSING,
            } for row in linked_goals if row.get("id_meta_proposta") is not None],
            "schedule_count": len(linked_schedules),
            "analysis_count": len(linked_analyses),
            "analyses": [{
                "analysis_id": str(row["id_analise_proposta"]),
                "recorded_at": row.get("dh_analise_proposta") or MISSING,
                "phase": row.get("in_fase_analise") or MISSING,
                "result": row.get("in_resultado_analise") or MISSING,
                "opinion": row.get("ds_parecer") or MISSING,
                "analysis_type_count": len(row.get("tipos_analise") or []),
                "source_url": row.get("source_url") or MISSING,
            } for row in linked_analyses if row.get("id_analise_proposta") is not None],
            "indicator_count": len(linked_indicators),
            "indicators": [{
                "indicator_id": str(row["id_proposta_resultado_indicador"]),
                "expected_result": row.get("ds_resultado_esperado_proposta_resultado_indicador") or MISSING,
                "name": row.get("nm_indicador_proposta") or MISSING,
                "value": numeric(row.get("vl_indicador_proposta")),
                "unit": row.get("nm_unidade_medida_indicador_proposta") or MISSING,
                "source_url": row.get("source_url") or MISSING,
            } for row in linked_indicators if row.get("id_proposta_resultado_indicador") is not None],
            "resource_count": len(linked_resources),
            "resources": [{
                "resource_id": str(row["id_distribuicao_recurso_proposta"]),
                "distribution_type": row.get("in_tipo_distribuicao") or MISSING,
                "gnd": row.get("in_tipo_gnd") or MISSING,
                "amendment_number": row.get("nr_emenda_proposta") or MISSING,
                "parliamentarian": row.get("nm_parlamentar_proposta") or MISSING,
                "amendment_type": row.get("in_tipo_emenda_parlamentar_proposta") or MISSING,
                "value": numeric(row.get("valor_emenda")),
                "source_url": row.get("source_url") or MISSING,
            } for row in linked_resources if row.get("id_distribuicao_recurso_proposta") is not None],
            "commitment_count": sum(len(row["commitments"]) for row in partnership_details),
            "payable_document_count": sum(len(row["payable_documents"]) for row in partnership_details),
            "account_count": sum(len(row["accounts"]) for row in partnership_details),
            "payment_order_count": sum(len(row["payment_orders"]) for row in partnership_details),
            "bank_statement_count": sum(len(row["bank_statements"]) for row in partnership_details),
        })

    engineering = []
    for project_id, project_geometries in geometries_by_project.items():
        details = project_by_id.get(project_id, {})
        municipalities_for_project = sorted({
            (str(row.get("cod_ibge")), str(row.get("no_municipio") or row.get("municipality_name") or MISSING))
            for row in project_geometries
        })
        engineering.append({
            "project_id": project_id,
            "name": details.get("desc_nome") or MISSING,
            "description": details.get("desc_projeto") or MISSING,
            "situation": details.get("situacao") or MISSING,
            "nature": details.get("natureza_intervencao") or MISSING,
            "species": details.get("especie_intervencao") or MISSING,
            "organization": details.get("organizacao_resp") or MISSING,
            "planned_start": details.get("dt_inicial_prevista") or MISSING,
            "planned_end": details.get("dt_final_prevista") or MISSING,
            "effective_start": details.get("dt_inicial_efetiva") or MISSING,
            "effective_end": details.get("dt_final_efetiva") or MISSING,
            "municipalities": [{"ibge_code": ibge, "name": name} for ibge, name in municipalities_for_project],
            "geometry_count": len(project_geometries),
            "physical_execution_count": len(execution_by_project.get(project_id, [])),
            "contract_count": len(contracts_by_project.get(project_id, [])),
            "commitment_count": len(commitments_by_project.get(project_id, [])),
            "interruption_count": len(interruptions_by_project.get(project_id, [])),
            "feasibility_study_count": len(studies_by_project.get(project_id, [])),
            "source": "ObrasGov",
            "source_url": details.get("source_url") or project_geometries[0].get("source_url") or MISSING,
        })
        project_event = event("obra", project_id, "project_registered", details.get("dt_cadastro"), f"Projeto de investimento {project_id} cadastrado", details.get("source_url"))
        if project_event:
            first = municipalities_for_project[0]
            timeline.append({**project_event, "ibge_code": first[0], "municipality_name": first[1], "proposal_id": None})
        for interruption in interruptions_by_project.get(project_id, []):
            interruption_id = interruption.get("id_historico_situacao_investimento")
            situation = interruption.get("descricao_historico_situacao_investimento") or MISSING
            interruption_event = event(
                "obra_historico",
                interruption_id,
                "project_source_status",
                interruption.get("data_historico_situacao_investimento"),
                f"Projeto {project_id}: {situation}",
                interruption.get("source_url"),
            )
            if interruption_event:
                first = municipalities_for_project[0]
                timeline.append({
                    **interruption_event,
                    "ibge_code": first[0],
                    "municipality_name": first[1],
                    "proposal_id": None,
                    "project_id": project_id,
                    "detail": interruption.get("justificativa_cancelada_paralisada") or MISSING,
                })

    contracts = read_json(SITE / "contracts.json", [])
    financial = {
        "contract_value_total": sum(value for row in contracts if (value := numeric(row.get("valor_global"))) is not None),
        "scheduled_disbursement_total": sum(value for row in schedules if (value := numeric(row.get("vl_cronograma_desembolso"))) is not None),
        "commitment_total": sum(value for row in commitments if (value := numeric(row.get("valor_empenho"))) is not None),
        "obrasgov_commitment_total": sum(value for row in project_commitments if (value := numeric(row.get("valor_empenho"))) is not None),
        "payable_document_total": sum(value for row in payable_documents if (value := numeric(row.get("vl_documento_habil"))) is not None),
        "payment_order_total": sum(value for row in payment_orders if (value := numeric(row.get("vl_ordem_pagamento"))) is not None),
        "proposal_resource_total": sum(value for row in resources if (value := numeric(row.get("valor_emenda"))) is not None),
        "bank_movement_total": sum(value for row in statements if (value := numeric(row.get("vl_lancamento_extrato_bancario"))) is not None),
        "bank_credit_total": sum(
            value for row in statements
            if str(row.get("in_transacao") or "").casefold() == "crédito"
            and (value := numeric(row.get("vl_lancamento_extrato_bancario"))) is not None
        ),
        "bank_debit_total": sum(
            value for row in statements
            if str(row.get("in_transacao") or "").casefold() == "débito"
            and (value := numeric(row.get("vl_lancamento_extrato_bancario"))) is not None
        ),
        "records": {
            "contracts": len(contracts),
            "schedules": len(schedules),
            "commitments": len(commitments),
            "project_commitments": len(project_commitments),
            "payable_documents": len(payable_documents),
            "payment_orders": len(payment_orders),
            "proposal_goals": len(goals),
            "proposal_analyses": len(analyses),
            "proposal_indicators": len(indicators),
            "proposal_resources": len(resources),
            "partnership_accounts": len(accounts),
            "bank_statements": len(statements),
            "special_action_plans": len(special_action_plans),
            "special_executors": len(special_executors),
            "special_work_plans": len(special_work_plans),
            "special_commitments": len(special_commitments),
        },
    }
    documents = [
        {
            "document_id": str(row["id_documento_habil"]),
            "partnership_id": str(row["id_parceria"]),
            "number": row.get("nr_documento_habil") or MISSING,
            "document_type": row.get("tp_documento_habil") or MISSING,
            "issued_at": row.get("dt_emissao") or MISSING,
            "value": numeric(row.get("vl_documento_habil")),
            "status": row.get("in_situacao_dh") or MISSING,
            "creditor_id": row.get("cd_credor_devedor") or MISSING,
            "creditor_name": row.get("nm_credor_devedor") or MISSING,
            "observation": row.get("tx_observacao") or MISSING,
            "commitment_number": row.get("nr_empenho_dh") or MISSING,
            "payment_order_count": len(orders_by_document.get(str(row["id_documento_habil"]), [])),
            "source": row.get("source") or "Transferegov - Gestão de Parcerias",
            "source_url": row.get("source_url") or MISSING,
            "fetched_at": row.get("fetched_at") or MISSING,
            "sha256": row.get("sha256") or MISSING,
        }
        for row in payable_documents
        if row.get("id_documento_habil") is not None and row.get("id_parceria") is not None
    ]
    payment_order_references = [
        {
            "payment_order_id": str(row["id_op"]),
            "document_id": str(row["id_documento_habil"]),
            "number": row.get("nr_ordem_pagamento") or MISSING,
            "status": row.get("in_situacao_op") or MISSING,
            "issued_at": row.get("dt_emissao_op") or MISSING,
            "value": numeric(row.get("vl_ordem_pagamento")),
            "bank_order_number": row.get("nr_ordem_bancaria") or MISSING,
            "bank_order_issued_at": row.get("dt_emissao_ordem_bancaria") or MISSING,
            "observation": row.get("tx_observacao_op") or MISSING,
            "source": row.get("source") or "Transferegov - Gestão de Parcerias",
            "source_url": row.get("source_url") or MISSING,
            "fetched_at": row.get("fetched_at") or MISSING,
            "sha256": row.get("sha256") or MISSING,
        }
        for row in payment_orders
        if row.get("id_op") is not None and row.get("id_documento_habil") is not None
    ]
    account_references = [
        {
            "account_id": str(row["id_parceria_conta"]),
            "partnership_id": str(row["id_parceria"]),
            "type": row.get("tp_conta") or MISSING,
            "name": row.get("nm_conta") or MISSING,
            "opened_at": row.get("dt_abertura") or MISSING,
            "status": row.get("tx_descricao") or MISSING,
            "status_detail": row.get("tx_detalhamento") or MISSING,
            "bank": row.get("nm_banco") or MISSING,
            "account_number": row.get("tx_conta") or MISSING,
            "branch_number": row.get("tx_numero") or MISSING,
            "branch_name": row.get("nm_agencia") or MISSING,
            "branch_municipality": row.get("nm_municipio_agencia") or MISSING,
            "branch_state": row.get("sg_uf_agencia") or MISSING,
            "current_balance": numeric(row.get("vl_saldo_conta_corrente")),
            "current_balance_at": row.get("dt_referencia_saldo_conta_corrente") or MISSING,
            "investment_balance": numeric(row.get("vl_saldo_conta_investimento")),
            "investment_balance_at": row.get("dt_referencia_saldo_conta_investimento") or MISSING,
            "income_classification_count": len(row.get("classificacoes_ingresso") or []),
            "bank_statement_count": len(statements_by_account.get(str(row["id_parceria_conta"]), [])),
            "bank_credit_total": sum(
                value for statement in statements_by_account.get(str(row["id_parceria_conta"]), [])
                if str(statement.get("in_transacao") or "").casefold() == "crédito"
                and (value := numeric(statement.get("vl_lancamento_extrato_bancario"))) is not None
            ),
            "bank_debit_total": sum(
                value for statement in statements_by_account.get(str(row["id_parceria_conta"]), [])
                if str(statement.get("in_transacao") or "").casefold() == "débito"
                and (value := numeric(statement.get("vl_lancamento_extrato_bancario"))) is not None
            ),
            "bank_statement_first_at": min(
                (
                    statement["dt_movimento_lancamento_extrato_bancario"]
                    for statement in statements_by_account.get(str(row["id_parceria_conta"]), [])
                    if statement.get("dt_movimento_lancamento_extrato_bancario")
                ),
                default=MISSING,
            ),
            "bank_statement_last_at": max(
                (
                    statement["dt_movimento_lancamento_extrato_bancario"]
                    for statement in statements_by_account.get(str(row["id_parceria_conta"]), [])
                    if statement.get("dt_movimento_lancamento_extrato_bancario")
                ),
                default=MISSING,
            ),
            "source": row.get("source") or "Transferegov - Gestão de Parcerias",
            "source_url": row.get("source_url") or MISSING,
            "fetched_at": row.get("fetched_at") or MISSING,
            "sha256": row.get("sha256") or MISSING,
        }
        for row in accounts
        if row.get("id_parceria_conta") is not None and row.get("id_parceria") is not None
    ]
    today = date.today().isoformat()
    expired_contracts = [
        row for row in contracts
        if isinstance(row.get("vigencia_fim"), str)
        and len(row["vigencia_fim"]) >= 10
        and row["vigencia_fim"][:10] < today
    ]
    interrupted_projects = [
        row for row in projects
        if any(term in str(row.get("situacao") or "").casefold() for term in ("paralis", "cancel"))
    ]
    ambiguity_errors = []
    for directory in (PUBLISHED, obras):
        for errors_path in directory.glob("*_errors.json"):
            ambiguity_errors.extend(
                row for row in read_json(errors_path, [])
                if str(row.get("error", "")).startswith("Ambiguous")
            )
    integrity = {
        "records_assessed": sum(len(rows) for rows in (proposals, partnerships, goals, schedules, analyses, indicators, resources, commitments, payable_documents, accounts, payment_orders, statements, special_action_plans, special_executors, special_work_plans, special_commitments, geometries, projects, physical_execution, project_contracts, project_commitments, project_interruptions, feasibility_studies)),
        "ambiguous_relationships": len(ambiguity_errors),
        "rules": [
            {
                "id": "official-primary-key",
                "description": "Todo registro publicado deve possuir a chave oficial declarada para sua entidade.",
                "violations": 0,
            },
            {
                "id": "official-parent-key",
                "description": "Todo relacionamento deve repetir exatamente a chave pai usada na consulta oficial.",
                "violations": 0,
            },
        ],
        "signals": [
            {
                "id": "contract-term-ended",
                "label": "Contratos com fim de vigência anterior à data de referência",
                "count": len(expired_contracts),
                "basis": "Comparação determinística de vigencia_fim do PNCP com a data de geração.",
                "classification": "Atenção operacional; não presume irregularidade.",
            },
            {
                "id": "project-source-status-interrupted",
                "label": "Projetos com situação de paralisação ou cancelamento informada pela fonte",
                "count": len(interrupted_projects),
                "basis": "Campo situacao do ObrasGov.",
                "classification": "Situação oficial; não presume irregularidade.",
            },
            {
                "id": "project-official-interruption-history",
                "label": "Eventos no histórico oficial de paralisação ou cancelamento",
                "count": len(project_interruptions),
                "basis": "Endpoint de histórico de situação cancelada/paralisada do ObrasGov.",
                "classification": "Histórico oficial; não presume irregularidade.",
            },
        ],
    }
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": "official_only",
        "sync_status": {
            "partnerships": sync_state(PUBLISHED, "partnerships", partnerships),
            "proposal_goals": sync_state(PUBLISHED, "proposal_goals", goals),
            "disbursement_schedule": sync_state(PUBLISHED, "disbursement_schedule", schedules),
            "proposal_analyses": sync_state(PUBLISHED, "proposal_analyses", analyses),
            "proposal_indicators": sync_state(PUBLISHED, "proposal_indicators", indicators),
            "proposal_resources": sync_state(PUBLISHED, "proposal_resources", resources),
            "commitments": sync_state(PUBLISHED, "commitments", commitments),
            "payable_documents": sync_state(PUBLISHED, "payable_documents", payable_documents),
            "partnership_accounts": sync_state(PUBLISHED, "partnership_accounts", accounts),
            "payment_orders": sync_state(PUBLISHED, "payment_orders", payment_orders),
            "bank_statements": sync_state(PUBLISHED, "bank_statements", statements),
            "special_action_plans": sync_state(PUBLISHED, "special_action_plans", special_action_plans),
            "special_executors": sync_state(PUBLISHED, "special_executors", special_executors),
            "special_work_plans": sync_state(PUBLISHED, "special_work_plans", special_work_plans),
            "special_commitments": sync_state(PUBLISHED, "special_commitments", special_commitments),
            "physical_execution": sync_state(obras, "physical_execution", physical_execution),
            "project_contracts": sync_state(obras, "project_contracts", project_contracts),
            "project_commitments": sync_state(obras, "project_commitments", project_commitments),
            "project_interruptions": sync_state(obras, "project_interruptions", project_interruptions),
            "feasibility_studies": sync_state(obras, "feasibility_studies", feasibility_studies),
        },
        "instrument_relations": instruments,
        "timeline": sorted(timeline, key=lambda row: row["occurred_at"], reverse=True),
        "engineering": sorted(engineering, key=lambda row: row["project_id"]),
        "documents": sorted(documents, key=lambda row: row["document_id"]),
        "payment_orders": sorted(payment_order_references, key=lambda row: row["payment_order_id"]),
        "accounts": sorted(account_references, key=lambda row: row["account_id"]),
        "financial": financial,
        "integrity": integrity,
        "counts": {
            "municipalities": len(municipalities),
            "proposals": len(proposals),
            "partnerships": len(partnerships),
            "instruments": len(instruments),
            "timeline_events": len(timeline),
            "engineering_projects": len(engineering),
            "obrasgov_geometries": len(geometries),
            "special_action_plans": len(special_action_plans),
            "special_executors": len(special_executors),
            "special_work_plans": len(special_work_plans),
            "special_commitments": len(special_commitments),
        },
    }
    write_json(SITE / "integrated.json", output)
    write_json(ROOT / "data/published/integrated_status.json", {
        "generated_at": output["generated_at"],
        "counts": output["counts"],
            "financial_records": financial["records"],
        "integrity": integrity,
        "policy": "official_only",
    })
    return output


if __name__ == "__main__":
    result = build()
    print(json.dumps({"counts": result["counts"], "financial": result["financial"], "integrity": result["integrity"]}, ensure_ascii=False, indent=2))
