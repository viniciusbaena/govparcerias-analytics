from dataclasses import dataclass
@dataclass(frozen=True)
class ConnectorDefinition:
    key:str; label:str; base_url:str; status:str; notes:str
CONNECTORS=[
 ConnectorDefinition("ibge","IBGE Localidades","https://servicodados.ibge.gov.br/api/v1","ready","Enriquecimento territorial por código IBGE."),
 ConnectorDefinition("transferegov_parcerias","Transferegov Gestão de Parcerias","https://api-publica.transferegov.gestao.gov.br","discovery_required","Novo ambiente oficial; rotas lidas do OpenAPI publicado."),
 ConnectorDefinition("transferegov_especiais","Transferegov Transferências Especiais","https://api-publica.transferegov.gestao.gov.br","discovery_required","Novo ambiente oficial; rotas lidas do OpenAPI publicado."),
 ConnectorDefinition("obrasgov","ObrasGov","https://api-publica.obrasgov.gestao.gov.br","discovery_required","Novo ambiente oficial; rotas lidas do OpenAPI publicado."),
 ConnectorDefinition("pncp","PNCP Dados Abertos","https://pncp.gov.br/api/consulta","ready","Consultas públicas para leitura."),]
