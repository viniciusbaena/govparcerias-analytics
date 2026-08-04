# Metadados estatísticos do IBGE — auditoria de acesso

O catálogo oficial documenta os endpoints `/api/Pesquisa` e `/api/ocorrenciaPesquisa/{codigoPesquisa}` em `https://apimetadados.ibge.gov.br/`.

Durante a implementação, as rotas HTTPS retornaram HTTP 403; a rota HTTP devolveu a página HTML de documentação, não JSON. Por isso nenhum conteúdo foi tratado como dado e nenhum registro foi publicado. A pendência está registrada para retomada quando o serviço disponibilizar resposta JSON autenticada ou pública.
