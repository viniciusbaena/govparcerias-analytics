# GovParcerias Intelligence — v1.2.0-alpha

Plataforma independente de inteligência para transferências públicas, organizada em dois eixos complementares:

- **Contrato:** núcleo operacional para finanças, engenharia, documentos, vistorias e prestação de contas.
- **Município e território:** núcleo gerencial para consolidação, comparação e visão macro.

## Carteira v1

Esta versão incorpora os 121 municípios da planilha `Planilha 121 municipios.xlsx`.

Os registros da planilha são classificados como **carteira administrativa fornecida pela equipe**. Eles não são confundidos com dados sincronizados de fontes públicas oficiais. Contratos, valores, obras, documentos, indicadores e conclusões permanecem vazios até que conectores oficiais validados forneçam evidências.

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
