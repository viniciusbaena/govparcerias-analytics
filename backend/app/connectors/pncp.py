from __future__ import annotations

from typing import Any

from .base import PublicApiConnector


class PNCPConnector(PublicApiConnector):
    """Conector de leitura para a API pública de consultas do PNCP."""

    def __init__(self, raw_dir: str = "data/raw"):
        super().__init__("pncp", "https://pncp.gov.br/api/consulta", raw_dir)

    async def contracts_by_period(
        self,
        start_date: str,
        end_date: str,
        page: int = 1,
        page_size: int = 50,
        cnpj_orgao: str | None = None,
    ):
        params: dict[str, Any] = {
            "dataInicial": start_date,
            "dataFinal": end_date,
            "pagina": page,
            "tamanhoPagina": page_size,
        }
        if cnpj_orgao:
            params["cnpjOrgao"] = "".join(ch for ch in cnpj_orgao if ch.isdigit())
        return await self.get("v1/contratos", params)

    async def contract(self, cnpj: str, year: int, sequential: int):
        cnpj = "".join(ch for ch in cnpj if ch.isdigit())
        return await self.get(f"v1/orgaos/{cnpj}/contratos/{year}/{sequential}")

    async def contract_documents(self, cnpj: str, year: int, sequential: int):
        cnpj = "".join(ch for ch in cnpj if ch.isdigit())
        return await self.get(f"v1/orgaos/{cnpj}/contratos/{year}/{sequential}/arquivos")

    async def contract_history(self, cnpj: str, year: int, sequential: int, page: int = 1, page_size: int = 50):
        cnpj = "".join(ch for ch in cnpj if ch.isdigit())
        return await self.get(
            f"v1/orgaos/{cnpj}/contratos/{year}/{sequential}/historico",
            {"pagina": page, "tamanhoPagina": page_size},
        )

    async def contract_terms(self, cnpj: str, year: int, sequential: int):
        cnpj = "".join(ch for ch in cnpj if ch.isdigit())
        return await self.get(f"v1/orgaos/{cnpj}/contratos/{year}/{sequential}/termos")
