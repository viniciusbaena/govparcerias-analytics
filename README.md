# GovParcerias Analytics

Plataforma independente e open source para consulta, organização e análise de dados públicos de parcerias e transferências.

> Projeto experimental e não oficial. Não representa nem possui vínculo institucional com os órgãos responsáveis pelas fontes consultadas.

## Publicação imediata

O GitHub Actions publica a pasta `site/`. Ela já contém a aplicação funcional e não exige compilação.

1. Remova os arquivos antigos do repositório.
2. Envie **todo o conteúdo desta pasta**, incluindo `.github`, `site`, `frontend`, `backend`, `database`, `docs`, `scripts` e `tests`.
3. Em Settings → Pages, mantenha Source = GitHub Actions.
4. Abra Actions e acompanhe `Publicar aplicação`.

## Estrutura

- `site/`: versão pública pronta para GitHub Pages.
- `frontend/`: evolução React + TypeScript + Vite.
- `backend/`: API FastAPI.
- `database/`: modelo PostgreSQL inicial.
- `docs/`: arquitetura, catálogo e decisões.

## Segurança

Não coloque chaves de IA ou credenciais no frontend. O assistente real será executado no backend.
