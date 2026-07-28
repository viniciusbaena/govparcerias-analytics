import httpx
from app.core.config import settings
class ParceriasConnector:
    def __init__(self): self.base_url=settings.parcerias_api_base_url.rstrip("/")
    async def get(self,path:str,params:dict|None=None)->dict|list:
        async with httpx.AsyncClient(timeout=30,headers={"User-Agent":"GovParceriasAnalytics/0.3"}) as client:
            response=await client.get(f"{self.base_url}/{path.lstrip('/')}",params=params)
            response.raise_for_status();return response.json()
