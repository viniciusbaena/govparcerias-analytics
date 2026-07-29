"""Planejador determinístico para o futuro copiloto.

Ele converte perguntas frequentes em intenções e filtros permitidos. O modelo de IA
não recebe acesso irrestrito ao banco.
"""
from dataclasses import dataclass

@dataclass(slots=True)
class QueryPlan:
    intent: str
    filters: dict
    explanation: str

def plan(question: str) -> QueryPlan:
    q=question.casefold()
    if "vigência" in q or "venc" in q:
        return QueryPlan("list_expiries",{"days":90},"Lista instrumentos com término próximo.")
    if "compare" in q:
        return QueryPlan("compare_municipalities",{},"Compara indicadores territoriais e financeiros.")
    if "oportun" in q:
        return QueryPlan("opportunity_radar",{},"Produz análise exploratória de lacunas temáticas.")
    if "mudança" in q or "alter" in q:
        return QueryPlan("recent_changes",{},"Resume diferenças entre sincronizações.")
    return QueryPlan("search",{"q":question},"Executa pesquisa textual estruturada.")
