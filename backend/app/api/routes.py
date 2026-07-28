from fastapi import APIRouter
router=APIRouter()
@router.get("/health")
async def health(): return {"status":"ok","service":"govparcerias-api"}
@router.get("/meta")
async def meta(): return {"version":"0.3.0-alpha","data_mode":"demonstration"}
@router.get("/municipios")
async def municipios(): return {"items":[],"message":"Aguardando importação da carteira municipal."}
