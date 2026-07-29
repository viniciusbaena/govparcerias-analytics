# Arquitetura de plugins

Cada plugin deve declarar sistema oficial, versão, URL-base HTTPS, domínios atendidos, política de paginação, limites, esquema bruto, normalização, validações e estratégia de documentos.

O pipeline obrigatório é: descoberta → coleta → armazenamento bruto → validação → quarentena ou publicação → snapshot → detecção de alterações → indexação documental → regras.

Nenhum conector pode publicar diretamente na camada analítica sem proveniência e validação.
