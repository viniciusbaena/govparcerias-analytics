# SICONFI — auditoria e decisão de integração

## Fonte oficial

- Documentação: <https://apidatalake.tesouro.gov.br/docs/siconfi/>
- OpenAPI: <https://apidatalake.tesouro.gov.br/docs/siconfi.yaml>
- Base oficial: `https://apidatalake.tesouro.gov.br/ords/cdwhprd/siconfi/tt/`

## Piloto restrito à carteira

Foi consultado somente o município canônico Altamira do Paraná (IBGE `4100459`), no endpoint oficial DCA de 2024:

`/dca?an_exercicio=2024&id_ente=4100459`

A resposta retornou 1.164 itens. Não houve carga nacional nem publicação desses itens no dataset da aplicação.

## Ambiguidade de chave

A resposta não fornece um identificador primário de linha. A combinação dimensional inicialmente avaliada (`exercicio`, `cod_ibge`, `anexo`, `rotulo`, `coluna`, `cod_conta`) gerou 385 colisões. Incluir também `conta` tornou as 1.164 linhas do piloto distintas, mas isso é uma inferência de identidade dimensional, não uma chave declarada pela fonte.

Por regra de integridade, o conector SICONFI permanece **auditado, mas não publicado** até que a identidade oficial da linha (ou um contrato dimensional explicitamente documentado pelo Tesouro) seja confirmada. Não será criada chave sintética nem feito upsert baseado em uma inferência silenciosa.

## Próximo passo seguro

Quando a chave oficial estiver esclarecida, implementar paginação, limite de 1 requisição por segundo, retry exponencial para 429/5xx, checkpoint por município/exercício/endpoint e upsert preservador. Todos os pedidos deverão conter `id_ente` de um dos 121 municípios; endpoints sem filtro territorial não serão utilizados.
