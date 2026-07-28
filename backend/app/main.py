from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
app=FastAPI(title="GovParcerias API",version="0.3.0-alpha",docs_url="/docs")
app.add_middleware(CORSMiddleware,allow_origins=["https://viniciusbaena.github.io"],allow_methods=["GET"],allow_headers=["*"])
app.include_router(router,prefix="/api/v1")
