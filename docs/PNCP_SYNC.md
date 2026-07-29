# Sincronização PNCP

A carga de contratos usa exclusivamente a API pública de consultas do PNCP.

## Execução padrão

```cmd
python scripts\sync_pncp_contracts.py
```

O período padrão começa em 1º de janeiro do ano corrente e termina na data atual.

## Período histórico

```cmd
python scripts\sync_pncp_contracts.py --start 20240101 --end 20261231
```

## Teste curto

```cmd
python scripts\sync_pncp_contracts.py --start 20260701 --end 20260729 --max-pages 1
```

Arquivos publicados:

- `data/published/contracts.json`
- `data/published/pncp_errors.json`
- `data/published/pncp_sync_status.json`
- `site/data/contracts.json`

A ausência de registros é preservada; nenhum contrato sintético é criado.
