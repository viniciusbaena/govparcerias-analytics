# Status dos conectores oficiais — v2.8.0-alpha

| Fonte/módulo | Estado | Escopo publicado |
|---|---|---|
| Carteira canônica | Concluído | 121 municípios, CNPJ e IBGE validados |
| PNCP | Concluído | 3.118 contratos, chave `numeroControlePNCP` |
| Transferegov — Gestão de Parcerias | Concluído | Propostas, parcerias, cronogramas, empenhos, documentos, pagamentos, contas, extratos, metas, análises, indicadores e recursos |
| ObrasGov | Concluído com ressalvas | Projetos e geometrias filtrados por IBGE; respostas sem chave própria permanecem não publicadas |
| IBGE | Concluído | Enriquecimento territorial restrito à carteira |
| SICONFI | Auditado, aguardando chave oficial | Piloto restrito; sem publicação enquanto a identidade dimensional não for confirmada |
| Transferegov — Transferências Especiais | Grafo ampliado concluído | 1.392 planos, 10 programas, 1.367 executores, 1.368 planos de trabalho, 2.989 análises, 41 pendências de órgãos, 1.404 empenhos, 123 relatórios, 582 novos relatórios, 1.337 documentos, 1.276 ordens e 6.125 eventos de histórico de pagamento |
| SADIPEM — Tesouro Nacional | PVLs publicados | Carga restrita por `id_ente` aos 121 municípios; operações de crédito, credores, valores e situação |
| IBGE — Metadados estatísticos | Auditado, acesso bloqueado | Endpoint documentado no catálogo, mas HTTPS retorna 403 e HTTP entrega a página HTML; nenhum metadado foi tratado como dado JSON |

Todos os conectores publicados preservam dados anteriores em sincronização parcial,
registram fonte/URL/hash e usam somente chaves oficiais. A ausência de um campo é
representada por `Não informado pela fonte`.

## Pendências explícitas

- **SICONFI:** auditado em piloto restrito, mas não publicado porque a fonte não confirma uma chave oficial de linha; não é permitido criar chave sintética.
- **ObrasGov:** medições de execução física e estudos de viabilidade sem chave própria permanecem fora da publicação, conforme `OBRASGOV.md`.
- **Análises especiais:** as chaves foram confirmadas no OpenAPI antes da carga; respostas sem chave continuam sendo rejeitadas e registradas.
