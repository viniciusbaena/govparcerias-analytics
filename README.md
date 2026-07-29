# GovParcerias Intelligence

Plataforma web independente e experimental para consulta e análise de dados públicos de transferências e parcerias.

## Versão 0.6.0-alpha

Inclui:

- aplicação estática publicada no GitHub Pages;
- dashboard, municípios, parcerias, financeiro e catálogo de dados;
- página municipal com indicadores e linha do tempo;
- cronograma público consolidado;
- importador local de carteira municipal em CSV;
- modelo CSV pronto para os 121 municípios;
- API FastAPI demonstrativa com filtros;
- catálogo de 28 entidades do modelo oficial;
- workflows de publicação e qualidade.

## Executar o site localmente

Abra `site/index.html` com um servidor HTTP local. Exemplo:

```bash
python -m http.server 8000 --directory site
```

## Executar a API

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .
uvicorn app.main:app --reload
```

Documentação local: `http://127.0.0.1:8000/docs`.

## Importar a carteira

A interface pública possui o módulo **Preparar carteira**. Também é possível usar:

```bash
python scripts/import_municipalities.py scripts/modelo-carteira.csv
```

A versão pública não possui login nem coleta credenciais. Os dados atuais são demonstrativos.


## Módulos de inteligência v0.6

A versão inclui sincronização incremental demonstrativa, histórico de alterações, central de alertas, qualidade dos dados, relatórios, notificações, paleta de comandos, modo escuro, comparador, mapa, radar e copiloto contextual. As integrações reais dependem da ativação do back-end hospedado e das fontes oficiais.
