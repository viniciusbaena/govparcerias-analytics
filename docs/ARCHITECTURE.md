# Arquitetura

```mermaid
flowchart LR
  U[Usuário] --> S[Site público]
  S --> A[API própria]
  A --> D[(PostgreSQL)]
  A --> C[Conectores públicos]
  A --> I[Serviço de IA]
  C --> P[Gestão de Parcerias]
  C --> E[Transferências Especiais]
  C --> B[IBGE]
```

A pasta `site` é uma entrega estática segura. A pasta `frontend` contém a base da futura SPA em React. O backend centraliza integrações, cache, consultas estruturadas e proteção de credenciais.
