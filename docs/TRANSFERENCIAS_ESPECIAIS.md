# Transferências Especiais — auditoria da API oficial

## Fonte

- Portal oficial: <https://api-publica.transferegov.gestao.gov.br/especiais>
- OpenAPI oficial: <https://api-publica.transferegov.gestao.gov.br/especiais/openapi.json>
- Comunicado de transição de ambiente: <https://www.gov.br/obrasgov/pt-br/noticias/2026/comunicado-23-2026-mudancas-nos-acessos-as-apis-de-dados-abertos-do-transferegov-br-e-do-obrasgov-br>

O módulo oferece entidades com chaves declaradas (`id_beneficiario`, `id_plano_acao`, `id_plano_trabalho`, `id_empenho`, `id_dh`, `id_op_ob`, `id_executor` etc.), paginação e filtros por CNPJ em alguns endpoints.

## Restrição territorial e ambiguidade

O endpoint `/beneficiarios_especiais` documenta `id_ente` como “Identificador do Ente”, mas o OpenAPI não define que esse identificador seja o código IBGE. Pilotos limitados a 10 registros com `id_ente=4100459` (Altamira do Paraná) e `id_ente=4115200` (Maringá) retornaram resposta vazia, sem permitir inferir o relacionamento.

Por isso, nenhuma carga de Transferências Especiais foi publicada. Não será tratado `id_ente` como IBGE nem será feita enumeração nacional para descobrir a relação. A implementação fica pendente de uma correspondência oficial entre os 121 entes da carteira e o identificador aceito pela API (ou de um endpoint oficial que aceite diretamente os CNPJs/IBGEs da carteira).

## Próximo passo seguro

Com a correspondência oficial confirmada, iniciar por `/beneficiarios_especiais`, depois seguir as relações por IDs oficiais (`id_plano_acao`, `id_executor`, `id_empenho`, `id_dh`, `id_op_ob`). Usar paginação, retry para 429/5xx, checkpoint e upsert preservador; campos ausentes recebem `Não informado pela fonte`.
