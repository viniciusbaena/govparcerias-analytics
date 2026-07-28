# GovParcerias Analytics

Plataforma **independente, experimental e open source** para consulta e análise de dados públicos relacionados a parcerias e transferências governamentais.

> Status: `0.2.0-alpha`. A versão publicada atualmente utiliza dados demonstrativos e não substitui as fontes oficiais.

## Demonstração

A interface estática pode ser publicada no GitHub Pages. Ela não contém login, anúncios, cookies de rastreamento, scripts de terceiros ou coleta de credenciais.

## Funcionalidades atuais

- Dashboard demonstrativo
- Pesquisa de municípios e parcerias
- Alertas visuais de vigência
- Exportação CSV
- Catálogo pesquisável do modelo de dados
- Área demonstrativa do assistente de IA
- Páginas públicas de privacidade, termos e segurança

## Estrutura

```text
frontend/       Aplicação estática publicada no GitHub Pages
backend/        Fundação da API FastAPI para implantação futura
docs/           Requisitos, arquitetura e catálogo técnico
.github/        Publicação e validações automatizadas
```

## Publicação no GitHub Pages

1. Envie o conteúdo para a branch `main`.
2. Em **Settings > Pages**, selecione **GitHub Actions**.
3. O workflow `.github/workflows/deploy-pages.yml` publicará a pasta `frontend`.

## Segurança

- Nunca coloque chaves de API no frontend.
- Não versione arquivos `.env`.
- Dados reais deverão indicar fonte e data de atualização.
- Vulnerabilidades devem ser relatadas pelo procedimento descrito em [SECURITY.md](SECURITY.md).

## Roadmap

Consulte [ROADMAP.md](ROADMAP.md).

## Licença

MIT. Consulte [LICENSE](LICENSE).
