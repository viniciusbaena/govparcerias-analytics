# Transferegov — Fase 1

Esta fase:

1. cadastra todos os municípios brasileiros pela API oficial de Localidades do IBGE;
2. preserva os 121 municípios da carteira original com `portfolio_member: true`;
3. descobre automaticamente as APIs e endpoints publicados no novo ambiente do Transferegov;
4. registra URL, horário de coleta, hash SHA-256 e erros;
5. prepara o catálogo para a sincronização incremental.

## Execução

```cmd
python scripts\sync_all_municipalities.py
python scripts\discover_transferegov_api.py
```

## Arquivos gerados

- `site/data/municipalities.json`
- `data/published/municipalities_all.json`
- `data/config/transferegov_catalog.json`
- `data/published/transferegov/discovery_status.json`

## Política

Somente dados oficiais. Campos ausentes permanecem nulos e devem ser exibidos como `Não informado pela fonte`.
