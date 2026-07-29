# Transferegov — Fase 2: perfil dos endpoints

Esta fase não faz carga massiva.

Ela:

1. relê as especificações OpenAPI oficiais;
2. identifica somente endpoints GET;
3. registra parâmetros obrigatórios e opcionais;
4. realiza uma consulta mínima quando for seguro;
5. detecta formato da resposta, chaves e paginação provável;
6. registra endpoints que não podem ser testados sem parâmetros específicos.

## Execução

```cmd
python scripts\profile_transferegov_endpoints.py
```

## Arquivos gerados

- `data/config/transferegov_endpoint_profiles.json`
- `data/published/transferegov/endpoint_profile_status.json`

## Segurança operacional

As consultas de teste usam tamanho de página igual a 1 quando o parâmetro é reconhecido.
A fase não percorre páginas nem baixa conjuntos completos.
