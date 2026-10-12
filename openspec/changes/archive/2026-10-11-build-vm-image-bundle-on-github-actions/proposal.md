# Proposal

## Why

O fluxo inicial de artifact exigia baixar um bundle, transferi-lo à VM Oracle e carregar as imagens manualmente. Para o deploy pelo Portainer, adotamos a publicação das imagens no GHCR privado: a Stack pode baixar uma tag versionada diretamente, enquanto o bundle local continua como alternativa de contingência.

## What Changes

- Publicar automaticamente no GHCR privado as imagens Django, PostgreSQL, Nginx e Traefik usadas pela VM, para `linux/amd64` e `linux/arm64`.
- Identificar cada publicação por `sha-<commit>` e manter a tag móvel `main` para conveniência.
- Fazer o Compose da VM usar o GHCR por padrão, mantendo overrides para imagens locais.
- Documentar a credencial de leitura do GHCR no Portainer, o deploy manual com tag SHA e o fallback pelo bundle local.
- Não publicar Redis no GHCR, expor os pacotes, guardar credenciais no repositório, nem automatizar deploy/migrações na Oracle.

## Capabilities

### New Capabilities

- `deployment/vm-image-publishing`: publicação e consumo operacional das imagens da VM.

### Modified Capabilities

Nenhuma.

## Impact

- Workflow GitHub Actions, Dockerfiles, `docker-compose.vm.yml`, `README.md` e `scripts/build-vm-images.sh`.
- A publicação do artifact deixa de ser o destino do workflow; o script de bundle local permanece como fallback.
- O deploy na VM continua sendo iniciado manualmente pelo Portainer, sem acesso da automação à instância ou aos seus segredos.
