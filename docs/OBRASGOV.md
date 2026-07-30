# ObrasGov — coleta restrita à carteira

Fonte oficial:

- portal: `https://api-publica.obrasgov.gestao.gov.br/`;
- OpenAPI: `https://api-publica.obrasgov.gestao.gov.br/obras/openapi.json`;
- módulo: `/obras`.

## Fronteira territorial

A coleta começa em `/geometria`, sempre com um único `cod_ibge` pertencente à
carteira canônica. Cada resposta deve repetir exatamente esse código. O registro
é rejeitado quando o território retornado diverge.

Os `id_projeto_investimento` descobertos dessa forma são as únicas raízes
permitidas para consultar:

- projeto de investimento;
- execução física;
- contrato;
- empenho;
- geometria;
- histórico de cancelamento ou paralisação;
- estudo de viabilidade.

Não existe consulta nacional seguida de filtragem local.

## Chaves e ambiguidades

Cada entidade só é publicada quando existe uma chave oficial inequívoca. Os
endpoints de execução física e estudo de viabilidade não documentam um
identificador próprio além de `id_projeto_investimento`; se retornarem mais de
um registro para o mesmo projeto, a execução para e grava
`AmbiguousOfficialKey`.

Em 29/07/2026, a carga de execução física foi interrompida de forma
conservadora na raiz `3106.41-04`: a resposta oficial trouxe múltiplas medições
e nenhuma chave própria documentada para distingui-las. As 331 respostas
inequívocas coletadas antes desse ponto foram preservadas, mas a entidade
permanece marcada como parcial. Não foi criada chave sintética nem inferida
ordem entre as medições.

Em 30/07/2026, a carga de estudos de viabilidade foi interrompida no projeto
`103239.41-90`. A resposta oficial trouxe quatro estudos distintos para o mesmo
projeto, incluindo tipos Ambiental, Econômica e Social, mas não forneceu
identificador próprio para cada estudo. O tipo não foi assumido como chave e
nenhuma chave composta ou posicional foi criada.

Durante o perfil controlado, alguns endpoints filhos responderam HTTP 404 para
um projeto válido, embora o OpenAPI documente apenas 200 e 422. Esse 404 não é
tratado automaticamente como lista vazia. Ele permanece registrado como
ambiguidade da API até que a fonte documente seu significado.

## Execução

Descoberta territorial:

```powershell
python scripts/sync_obrasgov_graph.py --entity geometries
```

Detalhes dos projetos descobertos:

```powershell
python scripts/sync_obrasgov_graph.py --entity projects
```

Entidade filha:

```powershell
python scripts/sync_obrasgov_graph.py --entity physical_execution
```

Todos os sincronizadores utilizam paginação, retry, checkpoint, escrita
atômica, payload bruto, URL, horário UTC, SHA-256 e upsert preservador.

## Cargas validadas em 29/07/2026

- 121 códigos IBGE consultados individualmente;
- 1.411 geometrias oficiais;
- 891 projetos de investimento;
- 65 contratos de projeto, após consulta dos 891 projetos, sem erro;
- 825 empenhos de projeto, sem duplicidade da chave oficial `nr_empenho` e sem
  erro;
- 110 eventos de histórico de paralisação/cancelamento, sem duplicidade da chave
  oficial `id_historico_situacao_investimento` e sem erro;
- 331 registros de execução física preservados antes da ambiguidade documentada
  acima.
