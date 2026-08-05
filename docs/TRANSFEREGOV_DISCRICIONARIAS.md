# Transferegov — Discricionárias e Legais

O catálogo oficial de downloads é um container público do Transferegov:

`https://api-publica.transferegov.gestao.gov.br/downloads/dadosgov/?restype=container&comp=list`

O conector `scripts/sync_discretionary_csv.py` baixa apenas datasets selecionados, lê os CSVs oficiais dentro dos ZIPs e mantém exclusivamente linhas que contenham CNPJ ou código IBGE da carteira de 121 municípios. O arquivo nacional bruto nunca é publicado.

Datasets centrais previstos: `siconv_programa`, `siconv_proposta`, `siconv_convenio`, `siconv_contrato`, `siconv_empenho`, `siconv_desembolso`, `siconv_pagamento` e `siconv_licitacao`.

## Ambiguidade registrada

Algumas tabelas não possuem CNPJ/IBGE próprio e dependem de relacionamento por identificadores oficiais. O conector não cria esses vínculos automaticamente. A integração dessas tabelas deve ocorrer após confirmar, no modelo oficial, a chave estrangeira correspondente.

## Execução controlada

```powershell
python scripts/sync_discretionary_csv.py --dataset siconv_programa
```

Os resultados filtrados são gravados em `data/published/transferegov_discricionarias/`, acompanhados de status de coleta, fonte, horário e indicação de que o arquivo nacional não foi publicado.
