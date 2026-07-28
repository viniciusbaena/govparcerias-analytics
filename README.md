# GovParcerias Analytics

Plataforma web independente para consulta, organização e análise de dados públicos do TransfereGov, com foco inicial em uma carteira de 121 municípios.

> Projeto experimental e não oficial. Não representa nem possui vínculo institucional com os órgãos responsáveis pelas fontes consultadas.

## Entrega atual

- protótipo navegável e responsivo em `frontend/`;
- publicação automática no GitHub Pages;
- catálogo pesquisável das 28 tabelas do modelo oficial;
- dados demonstrativos claramente identificados;
- exportação CSV;
- base FastAPI para a futura sincronização;
- modelos iniciais de banco PostgreSQL;
- documentação de arquitetura e roadmap.

## Publicação no GitHub Pages

1. Crie um repositório no GitHub.
2. Envie todo o conteúdo deste projeto para a branch `main`.
3. Abra **Settings → Pages**.
4. Em **Build and deployment**, selecione **GitHub Actions**.
5. O workflow `.github/workflows/deploy-pages.yml` publicará a pasta `frontend`.

A URL inicial será semelhante a `https://usuario.github.io/nome-do-repositorio/`. Posteriormente, um domínio personalizado poderá ser configurado sem alterar a aplicação.

## Execução local do protótipo

```bash
cd frontend
python -m http.server 8080
```

Abra `http://localhost:8080`.

## Back-end

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
uvicorn app.main:app --reload
```

## Limitação do GitHub Pages

GitHub Pages hospeda apenas arquivos estáticos. A sincronização com APIs, o banco PostgreSQL e o assistente de IA exigirão um serviço de back-end separado. O protótipo já separa essas responsabilidades para permitir futura migração de domínio e hospedagem.
