# Transferegov — sincronização incremental de propostas

Esta etapa consulta exclusivamente a API oficial de Gestão de Parcerias:

`https://api-publica.transferegov.gestao.gov.br/parcerias/proposta`

## Escopo e decisões de identidade

- O universo de consulta é lido de `site/data/municipalities.json` e comparado,
  registro a registro, com `source-data/Planilha 121 municipios.xlsx`.
- A execução é recusada se a carteira não tiver exatamente 121 registros com
  somente `name`, `cnpj` e `ibge_code`, ou se houver divergência, duplicidade ou
  formato inválido.
- Cada requisição inclui um único `cd_ibge_recebedor` da carteira. Nunca há
  consulta sem filtro nem carga nacional.
- O endpoint também aceita `cnpj_ente_recebedor`, mas esse filtro não representa
  todo o município: fundos municipais podem possuir CNPJ diferente da prefeitura.
  Por isso o código IBGE é a fronteira territorial da coleta; os CNPJs retornados
  pela fonte são preservados como `receiver_cnpj`.
- O upsert usa `id_proposta`. A especificação OpenAPI oficial descreve esse campo
  como “Identificador único da proposta”.
- Uma resposta sem `id_proposta`, sem metadados inequívocos de paginação ou com
  IBGE diferente do filtro interrompe a sincronização e é registrada no status.

## Segurança incremental

- Retry exponencial com jitter para falhas de rede, HTTP 429 e 5xx.
- `Retry-After` é respeitado quando informado em segundos.
- Paginação automática, com tamanho máximo oficial de 200 registros.
- Checkpoint gravado após cada página e retomada pela próxima página.
- Arquivo normalizado atualizado por upsert; registros antigos que não aparecem
  numa execução parcial não são apagados.
- Resposta bruta, URL final, horário UTC e SHA-256 são preservados por página.
- Campos normalizados ausentes recebem `Não informado pela fonte`; o objeto bruto
  continua inalterado.
- Nenhum arquivo PNCP é lido para escrita ou substituído por este sincronizador.

## Execução

Validação controlada de um município e uma página:

```powershell
python scripts/sync_transferegov_proposals.py --only-ibge 4115200 --max-pages 1
```

Sincronização integral da carteira (sempre filtrada município a município):

```powershell
python scripts/sync_transferegov_proposals.py
```

Arquivos operacionais:

- `data/published/transferegov/proposals.json`
- `data/published/transferegov/proposals_checkpoint.json`
- `data/published/transferegov/proposals_sync_status.json`
- `data/raw/transferegov/proposals/<data>/...`

`--only-ibge`, `--max-municipalities` e `--max-pages` existem para validações
parciais. `--only-ibge` recusa códigos fora da carteira. Uma execução parcial
preserva tudo que já estiver em `proposals.json`.
