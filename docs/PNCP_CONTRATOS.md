# Contratos PNCP

## Escopo

O sincronizador consulta exclusivamente os CNPJs dos 121 municípios presentes
em `site/data/municipalities.json`. Não existe modo de carga nacional.

Fonte oficial:

- endpoint: `https://pncp.gov.br/api/consulta/v1/contratos`;
- filtro obrigatório no projeto: `cnpjOrgao`;
- chave de upsert: `numeroControlePNCP`.

Se a API não retornar a chave oficial, ou retornar CNPJ/IBGE incompatível com o
município consultado, o registro não é publicado. A ocorrência é gravada em
`data/published/pncp_errors.json` para auditoria.

## Segurança da sincronização

- retry exponencial para HTTP 429 e 5xx, respeitando `Retry-After`;
- paginação automática, com até 500 registros por página;
- janelas de no máximo 365 dias;
- checkpoint em `data/published/pncp_checkpoint.json`;
- upsert preservador sobre `data/published/contracts.json`;
- cópia publicada em `site/data/contracts.json`;
- payloads brutos com URL, horário e SHA-256 em `data/raw/pncp/`.

Uma execução parcial nunca remove contratos anteriores.

## Execução

Carga histórica restrita à carteira, desde 2021:

```powershell
python scripts/sync_pncp_contracts.py --start 20210101
```

Atualização incremental por data:

```powershell
python scripts/sync_pncp_contracts.py --start 20260729 --end 20260729
```

Para uma execução controlada, use `--max-pages N`. A retomada utiliza o
checkpoint, desde que o período e o conjunto de CNPJs sejam os mesmos.
