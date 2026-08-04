# Status dos conectores oficiais — v1.4.0-alpha

| Fonte/módulo | Estado | Escopo publicado |
|---|---|---|
| Carteira canônica | Concluído | 121 municípios, CNPJ e IBGE validados |
| PNCP | Concluído | 3.118 contratos, chave `numeroControlePNCP` |
| Transferegov — Gestão de Parcerias | Concluído | Propostas, parcerias, cronogramas, empenhos, documentos, pagamentos, contas, extratos, metas, análises, indicadores e recursos |
| ObrasGov | Concluído com ressalvas | Projetos e geometrias filtrados por IBGE; respostas sem chave própria permanecem não publicadas |
| IBGE | Concluído | Enriquecimento territorial restrito à carteira |
| SICONFI | Auditado, aguardando chave oficial | Piloto restrito; sem publicação enquanto a identidade dimensional não for confirmada |
| Transferegov — Transferências Especiais | Auditado, aguardando relacionamento oficial | OpenAPI validada; sem carga enquanto `id_ente` não for relacionado oficialmente aos 121 municípios |

Todos os conectores publicados preservam dados anteriores em sincronização parcial,
registram fonte/URL/hash e usam somente chaves oficiais. A ausência de um campo é
representada por `Não informado pela fonte`.
