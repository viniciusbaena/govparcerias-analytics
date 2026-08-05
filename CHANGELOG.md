# Changelog

## v3.8.0-alpha

- Centraliza a versão da aplicação em `APP_VERSION`.
- Estabelece versionamento obrigatório: toda melhoria publicada deve incrementar a versão e atualizar este changelog.
- Atualiza o selo e os nomes de exportação para a versão vigente.

## v3.4.0-alpha

- Reorganiza o detalhe municipal para iniciar por contratos/convênios e deixar propostas como referência complementar.
- Adiciona pesquisa por município, IBGE, projeto e contrato na página Obras e engenharia.
- Adiciona pesquisa e links de fonte no Centro de documentos e na Timeline integrada.

## v3.3.0-alpha

- Integra 1.276 PVLs oficiais do SADIPEM, consultados por `id_ente` nos 121 municípios.
- Corrige o sincronizador atual do ObrasGov para usar `id_execucao_fisica`, chave declarada no OpenAPI, e conclui 512 registros de execução física.
- Audita o serviço de metadados IBGE; o endpoint HTTPS retornou 403 e não foi publicado sem resposta JSON verificável.

## v3.2.0-alpha

- Adiciona auditoria determinística da release, verificando carteira, política official-only, sincronizações, integridade e ambiguidades documentadas.

## v2.8.0-alpha

- Atualiza o inventário de conectores para refletir o grafo completo de Transferências Especiais e as pendências de SICONFI/ObrasGov.
- Torna explícitos os critérios de não publicação quando a fonte não fornece chave oficial.

## v2.6.0-alpha

- Publica 10 programas oficiais referenciados pelos planos de ação de Transferências Especiais da carteira.
- Mantém a consulta restrita aos `id_programa` encontrados nos 1.392 planos já carregados.

## v2.5.0-alpha

- Publica 6.125 eventos oficiais de histórico de pagamento das 1.276 ordens de Transferências Especiais.
- Mantém o vínculo exclusivamente por `id_op_ob`, com retry, paginação, hash, proveniência e upsert preservador.

## v2.4.0-alpha

- Integra 2.989 análises de planos de trabalho e 41 pendências de órgãos das Transferências Especiais, sempre por `id_plano_trabalho` oficial.
- Mantém proveniência, checkpoint, retry, paginação e upsert preservador; a carga continua restrita à carteira dos 121 municípios.
- Registra explicitamente a ambiguidade inicial das chaves e só publica após confirmação no OpenAPI oficial.

## v1.8.0-alpha

- Adiciona sincronizador oficial de Transferências Especiais por CNPJ da carteira.
- Publica 1.392 planos de ação com paginação, retry, checkpoint, hash e upsert preservador.
- Percorre por lotes os relacionamentos oficiais e publica 1.367 executores, 1.368 planos de trabalho e 1.404 empenhos.
- Publica 123 relatórios de gestão e 582 novos relatórios relacionados aos planos de ação.
- Publica 1.337 documentos hábeis e 1.276 ordens bancárias por relações oficiais encadeadas.
- Publica 1.367 finalidades e 3.830 metas vinculadas aos executores oficiais.

## v1.5.0-alpha

- Inicia a etapa de auditoria funcional pós-merge da v1.4.0-alpha.
- Mantém o inventário oficial, a proveniência e os bloqueios de fontes ambíguas.

## v1.4.0-alpha

- Conclui o grafo Transferegov restrito às 1.935 propostas da carteira: 2.019 metas, 1.912 análises, 52 indicadores, 1.885 distribuições de recursos, 1.963 contas e 30.634 lançamentos bancários.
- Integra indicadores e recursos oficiais ao dossiê da proposta e à inteligência financeira, mantendo fonte, URL e SHA-256.
- Valida unicidade de todas as chaves oficiais e ausência de vínculos órfãos antes da publicação.
- Audita SICONFI e Transferências Especiais com pilotos restritos; documenta e bloqueia cargas quando a fonte não permite confirmar a chave ou o relacionamento territorial oficial.

## v1.3.0-alpha

- Adiciona sincronizador incremental do grafo Transferegov com 11 entidades relacionadas por IDs oficiais.
- Gera visão integrada por proposta, parceria, município e execução financeira.
- Torna funcionais o dossiê contratual, inteligência financeira, centro de proveniência, timeline e conformidade.
- Mantém checkpoint, retry, paginação, raw, upsert preservador e bloqueio de relações ambíguas.
- Adiciona descoberta territorial ObrasGov por `cod_ibge` e grafo de projetos por identificador oficial.
- Publica 1.935 parcerias, 2.048 itens de cronograma, 1.517 empenhos, 1.143 documentos hábeis, 1.142 ordens de pagamento e 1.963 contas do Transferegov.
- Exibe contas e saldos individualmente, preservando as datas de referência da fonte e evitando agregações enganosas.
- Publica 1.411 geometrias, 891 projetos, 65 contratos e 825 empenhos do ObrasGov.
- Separa valores financeiros por fonte para impedir dupla contagem entre empenhos de parcerias e de obras.
- Marca sincronizações parciais na interface e documenta a ausência de chave própria nas múltiplas medições de execução física.

## v1.2.0-alpha

- Corrige paginação, navegação interna, cartões, abas, paleta e demais botões bloqueados pela CSP.
- Centraliza ações da interface sem manipuladores JavaScript inline.
- Exibe a contagem PNCP já sincronizada na gestão territorial.
- Torna a coleta de contratos PNCP incremental e preservadora.
- Adiciona retry exponencial para 429/5xx, checkpoint, janelas de data e upsert por `numeroControlePNCP`.

## v1.1.0-alpha

- Integra 1.935 propostas oficiais do Transferegov à interface publicada.
- Amplia a consulta unificada para propostas, contratos e municípios.
- Adiciona propostas ao perfil municipal e detalhe com proveniência.
- Mantém os 45 contratos PNCP existentes.

## v1.0.0-alpha

- Validação da carteira canônica de 121 municípios.
- Primeiro sincronizador incremental de propostas do Transferegov.
- Retry exponencial, paginação, checkpoint, raw e upsert preservador.
- Carga oficial controlada de Maringá antes da expansão para toda a carteira.

## 0.9.0-alpha

- Cadastro integral dos 121 municípios da carteira v1.
- Pesquisa por município, CNPJ e código IBGE.
- Perfil municipal 360° com proveniência do cadastro.
- Nova jornada gerencial por município e território.
- Preservação do dossiê completo por contrato como núcleo operacional.
- Separação explícita entre carteira administrativa e base pública oficial.
- Manifesto de importação com SHA-256, contagem e validações.
- Esquema PostgreSQL para versionamento da carteira.

## 0.8.0-alpha

- Time Machine, timeline, grafo, centro documental, agentes especialistas e plugins.
