from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app=FastAPI(title="GovParcerias API",version="0.6.0-alpha",docs_url="/docs")
app.add_middleware(CORSMiddleware,allow_origins=["https://viniciusbaena.github.io","http://localhost:5173"],allow_methods=["GET"],allow_headers=["*"])
app.include_router(router,prefix="/api/v1")
