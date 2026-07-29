# Política de dados oficiais e não fabricação

1. A plataforma opera em modo `official_only`.
2. Nenhum dado sintético, estimado ou demonstrativo pode aparecer em ambiente publicado.
3. Campo ausente deve permanecer nulo e ser apresentado como “Não informado pela fonte”.
4. Todo valor exibido deve possuir `source_record_id`, sistema, endpoint, identificador externo, horário de coleta e hash do payload.
5. Cálculos da plataforma devem ser rotulados como derivados e preservar os registros oficiais usados.
6. O copiloto só responde quando recuperar evidência oficial; sem evidência, responde que não localizou a informação.
7. Documentos mascarados permanecem mascarados. Não se tenta reconstruir identificadores.
8. Documentos de obras, vistorias, medições e licitações são indexados somente quando públicos e provenientes de fonte oficial.
