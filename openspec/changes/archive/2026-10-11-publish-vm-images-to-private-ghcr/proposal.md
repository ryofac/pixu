# Proposal

## Why

O deploy atual exige transferir e carregar manualmente um bundle de imagens na VM Oracle. Publicar as imagens de produção no GHCR privado permite que a VM as obtenha diretamente durante o deploy, mantendo o script local de bundle como alternativa operacional.

## What Changes

- Substituir a publicação do artifact do GitHub Actions pelo push das imagens Pixu ao GHCR privado.
- Publicar as quatro imagens próprias usadas pelo Compose da VM, identificadas pelo SHA do commit e por uma tag de branch conveniente; manter Redis no Docker Hub.
- Produzir imagens multi-arquitetura `linux/amd64` e `linux/arm64` para permitir pull pela arquitetura da instância Oracle.
- Atualizar `docker-compose.vm.yml` e o README para puxar do GHCR e explicar como conceder acesso privado ao Portainer/VM sem armazenar credenciais no `.env.vm`.
- Manter `scripts/build-vm-images.sh` para builds locais e criação de bundle sem publicar no registry.
- Não executar deploy, login ou operações remotas na Oracle/Portainer pelo workflow.

## Capabilities

### New Capabilities

Nenhuma. Esta mudança altera o fluxo interno de publicação e operação do deploy, não requisitos funcionais do produto.

### Modified Capabilities

Nenhuma.

## Impact

- Workflow GitHub Actions, com `GITHUB_TOKEN` restrito a `contents: read` e `packages: write`.
- Dockerfiles das quatro imagens, para metadados de origem e vínculo dos pacotes ao repositório.
- `docker-compose.vm.yml`, README e procedimento de autenticação GHCR no Portainer/VM.
- A change `build-vm-image-bundle-on-github-actions` fica substituída para o fluxo do Actions; o bundle local permanece disponível como fallback.
