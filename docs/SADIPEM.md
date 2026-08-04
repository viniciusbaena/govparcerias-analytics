# SADIPEM — primeira etapa

Fonte oficial: `https://apidatalake.tesouro.gov.br/docs/sadipem/`.

A primeira etapa consulta o endpoint `/pvl` por `id_ente`, usando exclusivamente os 121 códigos IBGE da carteira. O identificador oficial publicado é `id_pleito`; cada registro preserva URL, data de coleta e SHA-256. A API impõe limite de uma requisição por segundo, respeitado pelo conector.

Resultado da carga: 1.276 PVLs, sem erros territoriais.

Os endpoints oficiais de cronogramas, liberações, câmbio e CDP ficam como próxima etapa do grafo, sempre ancorados nos `id_pleito` publicados. Nenhuma consulta nacional é feita.
