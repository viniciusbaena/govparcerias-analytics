# Transferências Especiais — auditoria da API oficial

## Fonte

- Portal oficial: <https://api-publica.transferegov.gestao.gov.br/especiais>
- OpenAPI oficial: <https://api-publica.transferegov.gestao.gov.br/especiais/openapi.json>
- Comunicado de transição de ambiente: <https://www.gov.br/obrasgov/pt-br/noticias/2026/comunicado-23-2026-mudancas-nos-acessos-as-apis-de-dados-abertos-do-transferegov-br-e-do-obrasgov-br>

O módulo oferece entidades com chaves declaradas (`id_beneficiario`, `id_plano_acao`, `id_plano_trabalho`, `id_empenho`, `id_dh`, `id_op_ob`, `id_executor` etc.), paginação e filtros por CNPJ em alguns endpoints.

## Restrição territorial e implementação

O ambiente atualizado documenta filtros PostgREST por CNPJ. O endpoint `/plano_acao_especial` aceita `cnpj_beneficiario_plano_acao=eq.<CNPJ>`, além de `limit` e `offset`, sem depender de `id_ente` ou de uma inferência IBGE.

O sincronizador `scripts/sync_transferencias_especiais.py` executou carga restrita aos 121 CNPJs da carteira, com paginação, retry, checkpoint, raw, hash e upsert preservador. Foram publicados 1.392 planos de ação com zero erros.

## Próximo passo seguro

O próximo passo é percorrer relações por IDs oficiais (`id_plano_acao`, `id_executor`, `id_empenho`, `id_dh`, `id_op_ob`) sem ampliar o escopo territorial. Campos ausentes recebem `Não informado pela fonte`.

O sincronizador `scripts/sync_transferencias_especiais_graph.py` percorreu os
1.392 planos em lotes de IDs oficiais e publicou 1.367 executores, 1.368 planos
de trabalho e 1.404 empenhos, todos sem erros. A carga é incremental e pode ser
retomada sem apagar registros anteriores.

O mesmo grafo publicou ainda 123 relatórios de gestão e 582 novos relatórios de
gestão, todos vinculados aos planos por `id_plano_acao`.

O estágio financeiro publicou 1.337 documentos hábeis por `id_empenho` e 1.276
ordens bancárias por `id_dh`, sem erros e sem consulta fora das relações oficiais.

Por executor, foram publicados 1.367 finalidades e 3.830 metas relacionadas por
`id_executor`.
