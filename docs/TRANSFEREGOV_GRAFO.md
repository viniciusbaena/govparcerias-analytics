# Grafo incremental do Transferegov

## Fronteira da coleta

O sincronizador nunca consulta uma entidade do módulo Gestão de Parcerias sem
uma chave pai. As raízes são exclusivamente os 1.935 `id_proposta` coletados
para os códigos IBGE da carteira canônica.

Relações oficiais implementadas:

```text
proposta
├── parceria
│   ├── empenho
│   ├── documento hábil
│   │   └── ordem de pagamento
│   └── conta da parceria
│       └── extrato bancário
├── meta
├── cronograma de desembolso
├── análise
├── indicador
└── distribuição de recursos
```

Cada endpoint é chamado com o identificador pai documentado no OpenAPI oficial.
O registro retornado só é publicado quando repete exatamente esse identificador
e possui sua chave primária oficial. Divergências são registradas e não geram
ligações.

## Entidades

O script `scripts/sync_transferegov_graph.py` implementa:

- `partnerships`;
- `proposal_goals`;
- `disbursement_schedule`;
- `proposal_analyses`;
- `proposal_indicators`;
- `proposal_resources`;
- `commitments`;
- `payable_documents`;
- `partnership_accounts`;
- `payment_orders`;
- `bank_statements`.

## Segurança operacional

- paginação automática;
- retry exponencial para falhas de rede, 429 e 5xx;
- checkpoint independente por entidade;
- upsert pela chave oficial de cada entidade;
- escrita atômica;
- preservação de registros anteriores em execuções parciais;
- payload bruto, URL, horário UTC e SHA-256 por página;
- relatório de erros e status por entidade.

## Execução

Piloto controlado:

```powershell
python scripts/sync_transferegov_graph.py --entity partnerships --max-roots 5
```

Uma entidade completa:

```powershell
python scripts/sync_transferegov_graph.py --entity partnerships
```

Grafo completo, respeitando a ordem das dependências:

```powershell
python scripts/sync_transferegov_graph.py --entity all
python scripts/build_integrated_dataset.py
```

O arquivo `site/data/integrated.json` é uma projeção publicada sem payloads
brutos. Ele alimenta os módulos de dossiê, inteligência financeira, timeline,
proveniência e conformidade.

## Cargas validadas em 29/07/2026

- 1.935 propostas da carteira;
- 1.935 vínculos proposta → parceria, sem erro;
- 2.048 itens de cronograma de desembolso, vinculados às 1.935 propostas e
  concluídos sem erro;
- total do cronograma publicado: R$ 608.395.187,71.
- 1.517 empenhos, vinculados às 1.935 parcerias, sem chave duplicada, sem vínculo
  órfão e sem erro;
- total empenhado publicado: R$ 422.753.821,00.
- 1.143 documentos hábeis, vinculados às 1.935 parcerias, sem chave duplicada,
  sem vínculo órfão e sem erro;
- total dos documentos hábeis publicado: R$ 300.621.710,00.
- 1.142 ordens de pagamento, vinculadas aos 1.143 documentos hábeis, sem chave
  duplicada, sem vínculo órfão e sem erro;
- total das ordens de pagamento publicado: R$ 299.975.085,00.
- 1.963 contas de parceria, vinculadas às 1.935 parcerias, sem chave duplicada,
  sem vínculo órfão e sem erro.

Os saldos das contas não são somados entre si: as datas de referência informadas
pela fonte podem divergir. A interface preserva e exibe cada saldo com sua
respectiva data.

Essas contagens descrevem somente a carteira dos 121 municípios. Não houve
consulta nacional seguida de filtragem.
