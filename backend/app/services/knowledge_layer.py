"""Unified knowledge-layer contracts.

No method in this module fabricates records. Empty evidence produces an explicit
'insufficient_evidence' result.
"""
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class Evidence:
    source_system: str
    source_url: str
    collected_at: str
    external_id: str
    payload_hash: str
    excerpt: str | None = None
    page: int | None = None

@dataclass
class AnswerEnvelope:
    status: str
    answer: str | None = None
    official_facts: list[dict[str, Any]] = field(default_factory=list)
    deterministic_calculations: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

class KnowledgeLayer:
    def answer(self, question: str, evidence: list[Evidence]) -> AnswerEnvelope:
        if not question.strip():
            return AnswerEnvelope(status="invalid_question", limitations=["Pergunta vazia."])
        if not evidence:
            return AnswerEnvelope(
                status="insufficient_evidence",
                answer=None,
                limitations=["Nenhuma evidência oficial foi recuperada para responder."],
            )
        return AnswerEnvelope(
            status="evidence_ready",
            answer=None,
            evidence=evidence,
            limitations=["A síntese deve citar todas as afirmações factuais."],
        )
