from datetime import date
from pydantic import BaseModel, Field

class Municipality(BaseModel):
    nome: str
    uf: str = Field(min_length=2,max_length=2)
    ibge: str
    populacao: int
    parcerias: int
    valor: float
    vigencias: int
    status: str

class Partnership(BaseModel):
    numero: str
    municipio: str
    orgao: str
    objeto: str
    situacao: str
    valor: float
    inicio: date
    fim: date
    tema: str
