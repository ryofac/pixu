# Spec Delta

## Purpose

Define como as imagens próprias usadas no deploy da VM Oracle são publicadas e disponibilizadas ao operador, com versão reproduzível e uma alternativa local para contingência.

## ADDED Requirements

### Requirement: Publicação privada das imagens de produção da VM
O sistema SHALL publicar as imagens Django, PostgreSQL, Nginx e Traefik usadas pela VM no GHCR como pacotes privados, para `linux/amd64` e `linux/arm64`, usando uma tag identificada pelo SHA completo do commit e uma tag conveniente para a branch principal.

#### Scenario: Publicação bem-sucedida em main
- **WHEN** uma execução de publicação da branch principal termina com sucesso
- **THEN** os quatro pacotes privados ficam disponíveis no GHCR com tags `main` e `sha-<commit>` para as duas arquiteturas suportadas

#### Scenario: Publicação não altera a visibilidade
- **WHEN** o workflow publica ou atualiza os pacotes
- **THEN** não altera a visibilidade configurada dos pacotes nem publica credenciais de produção

### Requirement: Pull autenticado pelo operador
O sistema SHALL permitir que o Compose da VM use os pacotes GHCR por padrão e SHALL permitir que o operador configure credenciais de leitura fora dos arquivos versionados para o Portainer baixar os pacotes privados.

#### Scenario: Implantação fixada por SHA
- **WHEN** o operador define `PIXU_IMAGE_TAG` com uma tag `sha-<commit>` e configura a credencial privada no Portainer
- **THEN** o Compose seleciona a mesma tag para as quatro imagens próprias e o Portainer pode baixá-las com a credencial de leitura

### Requirement: Fallback por bundle local
O sistema SHALL manter o procedimento de build e importação local do bundle como alternativa ao GHCR, sem exigir que o workflow GHCR publique um artifact do bundle.

#### Scenario: Uso das imagens locais
- **WHEN** o operador constrói e carrega o bundle local na VM
- **THEN** os overrides de imagem do Compose permitem iniciar os serviços Pixu com as imagens carregadas, sem depender de pull do GHCR
