# Integrações oficiais — v1.4.0-alpha

Fontes preparadas: IBGE Localidades, Transferegov Gestão de Parcerias, Transferências Especiais, ObrasGov e PNCP.

```bash
docker compose up -d db api
python scripts/sync_official_data.py
```

Payloads brutos: `data/raw/<fonte>/<data>/`. Dados publicados: `data/published/`.

Falhas e ausências nunca são substituídas por estimativas; a saída registra `Não informado pela fonte`.

Consulte [`CONNECTOR_STATUS.md`](CONNECTOR_STATUS.md) para o estado verificável
de cada fonte e as decisões de bloqueio de conectores ambíguos.
