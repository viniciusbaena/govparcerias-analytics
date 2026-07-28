from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
    app_name:str="GovParcerias API"
    app_env:str="development"
    database_url:str="postgresql+asyncpg://postgres:postgres@localhost:5432/govparcerias"
    parcerias_api_base_url:str="https://api-publica.transferegov.gestao.gov.br/parcerias"
    ai_provider:str="disabled"
    model_config=SettingsConfigDict(env_file=".env",extra="ignore")
settings=Settings()
