# Continuidade do desenvolvimento

Última atualização: 29/07/2026, branch
`agent/v1.3.0-alpha-modelo-integrado`, PR draft
[#5](https://github.com/viniciusbaena/govparcerias-analytics/pull/5).

## Invariantes obrigatórios

- carteira canônica limitada aos 121 municípios de
  `source-data/Planilha 121 municipios.xlsx`;
- somente fontes oficiais;
- nunca executar carga nacional para filtrar depois;
- não inventar chaves, relacionamentos ou valores;
- usar `Não informado pela fonte` quando a fonte não fornecer o campo;
- execução parcial preserva todos os registros publicados anteriormente;
- preservar integralmente os dados PNCP existentes;
- interromper e documentar respostas com múltiplos registros sem chave oficial
  própria.

## Estado validado

### Carteira e PNCP

- 121 municípios canônicos;
- 3.118 contratos PNCP preservados.

### Transferegov concluído

- 1.935 propostas;
- 1.935 parcerias;
- 2.048 itens de cronograma de desembolso;
- 1.517 empenhos;
- 1.143 documentos hábeis;
- 1.142 ordens de pagamento;
- 1.963 contas de parceria.

As contas possuem 1.963 chaves `id_parceria_conta` únicas, nenhuma chave
ausente e nenhum vínculo órfão com as 1.935 parcerias.

### Transferegov pausado com checkpoint

| Entidade | Registros preservados | Raízes processadas | Total | Erros |
|---|---:|---:|---:|---:|
| Extratos bancários | 21.657 | 837 | 1.963 contas | 0 |
| Metas | 579 | 537 | 1.935 propostas | 0 |
| Análises | 5 | 5 | 1.935 propostas | 0 |
| Indicadores | 0 | 5 | 1.935 propostas | 0 |
| Distribuições de recursos | 0 | 5 | 1.935 propostas | 0 |

Os pilotos comprovaram:

- extratos: `id_extrato_bancario` único e vínculo por
  `id_parceria_conta`;
- metas: `id_meta_proposta` único e vínculo por `id_proposta`;
- análises: `id_analise_proposta` único e vínculo por `id_proposta`;
- indicadores e recursos: as cinco primeiras propostas retornaram conjuntos
  vazios, sem erro. A ausência deve ser preservada como resposta da fonte.

Retomada:

```powershell
python scripts/sync_transferegov_graph.py --entity bank_statements --page-size 200 --min-delay 0.2
python scripts/sync_transferegov_graph.py --entity proposal_goals --page-size 200 --min-delay 0.3
```

Depois, executar pilotos controlados ou retomar pelos checkpoints:

```powershell
python scripts/sync_transferegov_graph.py --entity proposal_analyses --page-size 200 --min-delay 0.3
python scripts/sync_transferegov_graph.py --entity proposal_indicators --page-size 200 --min-delay 0.3
python scripts/sync_transferegov_graph.py --entity proposal_resources --page-size 200 --min-delay 0.3
```

O sincronizador persiste progresso a cada 25 páginas e sempre no encerramento,
erro ou limite solicitado. Se o processo for encerrado entre lotes, as páginas
posteriores ao último checkpoint podem ser consultadas novamente; o upsert pela
chave oficial evita duplicação e nenhum registro publicado é apagado.

### ObrasGov

- 1.411 geometrias;
- 891 projetos;
- 65 contratos de projeto;
- 825 empenhos de projeto;
- 110 eventos de interrupção.

Duas ambiguidades foram rejeitadas e permanecem documentadas:

- execução física do projeto `3106.41-04`;
- estudos de viabilidade do projeto `103239.41-90`.

Em ambos os casos a fonte retornou múltiplos registros sem identificador próprio
além de `id_projeto_investimento`. Não criar chave composta por suposição.

## Implementações já presentes

- retry exponencial para rede, 429 e 5xx;
- paginação, checkpoint, payload bruto, proveniência, SHA-256 e upsert;
- escrita atômica com retry para bloqueios transitórios do Windows;
- projeção integrada para dossiê, finanças, engenharia, documentos, timeline,
  risco e conformidade;
- contas com saldos individualizados por data de referência;
- extratos agregados em créditos, débitos e movimentação líquida, sem descartar
  os registros oficiais;
- busca unificada por contratos, propostas, obras, documentos, ordens e contas;
- metas e análises preparadas para exibição detalhada no dossiê;
- estado de todos os conectores exibido na página de risco.

## Próximas ações

1. concluir extratos e metas a partir dos checkpoints;
2. validar unicidade, chaves pai e totais finais;
3. concluir análises e avaliar indicadores e recursos em toda a carteira;
4. reconstruir `site/data/integrated.json`;
5. executar `python -m pytest -q` e validar `site/assets/app.js`;
6. fazer QA no navegador das páginas financeiras, dossiê, timeline e risco;
7. auditar o catálogo oficial por outros conectores viáveis, sempre por chave
   territorial ou pai da carteira;
8. manter o PR #5 draft até a entrega `v1.3.0-alpha` estar pronta para revisão.

## Arquivos locais que não pertencem à entrega

Não adicionar ao Git sem autorização explícita:

- `PROJECT_BRIEF_GOVPARCERIAS.md`;
- `PROMPT_CODEX_GOVPARCERIAS.txt`;
- `data/published/municipalities_all.json`;
- `data/raw/`;
- `materiais-referencia/`;
- `apresentacao-cultura-ia/`;
- `scripts/sync_all_municipalities.py`;
- logs locais `.transferegov-*.log` e `.obras-*.log`.
