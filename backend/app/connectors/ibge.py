from .base import PublicApiConnector
class IBGEConnector(PublicApiConnector):
    def __init__(self,raw_dir: str="data/raw"): super().__init__("ibge","https://servicodados.ibge.gov.br/api/v1",raw_dir)
    async def municipality(self,ibge_code: str): return await self.get(f"localidades/municipios/{ibge_code}")
