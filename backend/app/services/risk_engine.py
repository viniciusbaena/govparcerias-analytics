"""Deterministic risk engine. Rules require explicit official inputs."""
from dataclasses import dataclass
from typing import Any, Callable

@dataclass(frozen=True)
class RiskResult:
    rule_id: str
    triggered: bool
    severity: str
    explanation: str
    evidence_ids: list[str]

@dataclass(frozen=True)
class Rule:
    id: str
    severity: str
    predicate: Callable[[dict[str, Any]], bool]
    explanation: str
    required_fields: tuple[str, ...]

class RiskEngine:
    def evaluate(self, record: dict[str, Any], rules: list[Rule]) -> list[RiskResult]:
        results: list[RiskResult] = []
        for rule in rules:
            missing = [field for field in rule.required_fields if record.get(field) is None]
            if missing:
                continue
            triggered = bool(rule.predicate(record))
            results.append(RiskResult(
                rule_id=rule.id,
                triggered=triggered,
                severity=rule.severity,
                explanation=rule.explanation,
                evidence_ids=list(record.get("evidence_ids", [])),
            ))
        return results
