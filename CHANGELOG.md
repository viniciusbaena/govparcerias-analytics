# Changelog

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
