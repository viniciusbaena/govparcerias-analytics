from backend.app.services.document_compare import compare_text
from backend.app.services.knowledge_layer import KnowledgeLayer
from backend.app.services.plugin_registry import PluginManifest, PluginRegistry
from backend.app.services.risk_engine import RiskEngine, Rule

def test_knowledge_layer_blocks_without_evidence():
    result = KnowledgeLayer().answer("Qual é o valor?", [])
    assert result.status == "insufficient_evidence"
    assert result.answer is None

def test_risk_engine_skips_missing_required_fields():
    rule = Rule("late", "high", lambda r: r["days"] > 30, "Atraso", ("days",))
    assert RiskEngine().evaluate({}, [rule]) == []

def test_plugin_requires_https():
    registry = PluginRegistry()
    try:
        registry.register(PluginManifest("x", "1", "http://example", ("x",)))
    except ValueError:
        pass
    else:
        raise AssertionError("HTTP inseguro deveria ser rejeitado")

def test_document_compare_requires_both_texts():
    assert compare_text("", "texto")["status"] == "insufficient_content"
