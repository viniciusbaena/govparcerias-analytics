# GovParcerias Intelligence — v1.3.0-alpha

Plataforma independente de inteligência para transferências públicas, organizada em dois eixos complementares:

- **Contrato:** núcleo operacional para finanças, engenharia, documentos, vistorias e prestação de contas.
- **Município e território:** núcleo gerencial para consolidação, comparação e visão macro.

## Carteira v1

Esta versão incorpora os 121 municípios da planilha `Planilha 121 municipios.xlsx`.

Os registros da planilha são classificados como **carteira administrativa fornecida pela equipe**. Eles não são confundidos com dados sincronizados de fontes públicas oficiais. Contratos, valores, obras, documentos, indicadores e conclusões só são exibidos quando conectores oficiais validados fornecem evidências.

As telas exibem somente entidades que já possuem evidência oficial
sincronizada. Campos ausentes são apresentados como “Não informado pela fonte”,
e cargas parciais são identificadas como tal sem remover registros de execuções
anteriores.

A versão estática pronta para publicação está em `site/`.


## Integrações v1
A página inicial possui consulta por contrato e por município. O pipeline oficial está em `scripts/sync_official_data.py`.

O primeiro sincronizador incremental do Transferegov cobre propostas e é
estritamente limitado aos códigos IBGE da carteira canônica. Consulte
[`docs/TRANSFEREGOV_PROPOSTAS.md`](docs/TRANSFEREGOV_PROPOSTAS.md) para decisões
de identidade, retomada por checkpoint e execução segura.

O sincronizador incremental do PNCP cobre contratos dos mesmos 121 municípios,
com filtro por CNPJ, paginação, retry exponencial, checkpoint e upsert pela chave
oficial `numeroControlePNCP`. Consulte [`docs/PNCP_CONTRATOS.md`](docs/PNCP_CONTRATOS.md).

O grafo incremental do Transferegov parte exclusivamente das 1.935 propostas já
filtradas pela carteira e percorre relações por chaves oficiais. Ele alimenta
parcerias, metas, cronogramas, análises, recursos, empenhos, documentos hábeis,
contas, ordens de pagamento e extratos. Consulte
[`docs/TRANSFEREGOV_GRAFO.md`](docs/TRANSFEREGOV_GRAFO.md).

O ObrasGov é consultado primeiro por `cod_ibge` para descobrir somente projetos
localizados na carteira. As demais entidades são consultadas por
`id_projeto_investimento`. Consulte [`docs/OBRASGOV.md`](docs/OBRASGOV.md).
