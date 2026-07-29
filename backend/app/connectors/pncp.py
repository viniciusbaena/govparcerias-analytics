from .base import PublicApiConnector
class PNCPConnector(PublicApiConnector):
    def __init__(self,raw_dir: str="data/raw"): super().__init__("pncp","https://pncp.gov.br/api/consulta",raw_dir)
    async def contracts_by_period(self,start_date: str,end_date: str,page: int=1,page_size: int=50):
        return await self.get("v1/contratos",{"dataInicial":start_date,"dataFinal":end_date,"pagina":page,"tamanhoPagina":page_size})
