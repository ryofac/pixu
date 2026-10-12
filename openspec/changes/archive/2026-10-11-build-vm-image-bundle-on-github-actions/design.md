# Design

## Context

O deploy da VM Oracle usa `docker-compose.vm.yml` e Portainer. O caminho de bundle local já existia, mas baixar/carregar imagens manualmente não era o fluxo principal desejado. A solução adotada publica as imagens próprias no GHCR privado e permite que o Portainer faça pull durante um redeploy manual. Redis continua vindo do Docker Hub.

## Goals / Non-Goals

**Goals:**

- Publicar as quatro imagens próprias da VM como imagens multi-arquitetura `linux/amd64` e `linux/arm64`.
- Disponibilizar tags reproduzíveis por SHA completo do commit e uma tag `main` conveniente.
- Permitir que Portainer/VM leia os pacotes privados sem colocar credenciais em arquivos versionados ou no workflow.
- Preservar o bundle local como fallback e rollback.

**Non-Goals:**

- Publicar Redis no GHCR, tornar pacotes públicos, executar deploy remoto ou migrações automaticamente.
- Remover o procedimento local `scripts/build-vm-images.sh` e os overrides de imagens locais.
- Fazer o GitHub Actions acessar a VM Oracle, o Portainer ou segredos de produção.

## Decisions

### Publicar as imagens no GHCR com o token da execução

O workflow autentica no GHCR com `GITHUB_TOKEN` e permissões mínimas para ler o conteúdo e publicar pacotes (`contents: read`, `packages: write`). Publica Django, PostgreSQL, Nginx e Traefik com Buildx para as duas arquiteturas. Os pacotes permanecem privados e associados ao repositório por metadados OCI. Redis não é reconstruído nem publicado.

### Usar tags SHA e `main`

Cada publicação de `main` recebe `sha-<commit>` e `main`. O Compose usa `PIXU_IMAGE_TAG` para selecionar uma versão e assume `main` quando não há override; um deploy reproduzível fixa o SHA. A tag `main` é mutável e não deve ser usada quando for necessário reproduzir exatamente uma implantação.

### Manter credenciais de pull separadas das credenciais de publicação

O workflow usa seu `GITHUB_TOKEN` apenas para publicar. O operador configura no Portainer um acesso de leitura ao GHCR, por PAT GitHub com `read:packages` e acesso aos pacotes privados. Esse token não entra em `.env.vm`, no Compose, em workflow secrets nem no repositório.

### Preservar fallback de bundle local

`scripts/build-vm-images.sh` continua construindo as imagens locais e empacotando-as para `docker load`. Os overrides `PIXU_*_IMAGE` do Compose permitem usar as imagens carregadas localmente. O bundle não é um artifact automático do workflow GHCR.

## Risks / Trade-offs

- [Pull privado falha sem credencial ou autorização de pacote] → Configurar `ghcr.io` no Portainer com leitura e selecionar a credencial para a Stack.
- [A tag `main` muda com cada publicação] → Disponibilizar e documentar a tag imutável `sha-<commit>`.
- [Build multi-arquitetura falha em uma plataforma] → Manter validação do workflow antes de considerar uma publicação bem-sucedida e o bundle local como alternativa.
- [Pacotes podem ficar públicos por configuração manual] → O workflow não altera visibilidade; manter e conferir a configuração privada no GitHub.

## Migration Plan

1. Publicar as quatro imagens privadas no GHCR para ambas as arquiteturas com tags `main` e `sha-<commit>`.
2. Apontar os padrões do Compose da VM para o GHCR e manter os overrides locais.
3. Configurar a credencial de leitura no Portainer e fazer o redeploy manual com uma tag SHA.
4. Para contingência, voltar a uma tag SHA anterior ou carregar o bundle local e selecionar os overrides correspondentes.
