# Tasks

## 1. Publicação privada no GHCR

- [x] 1.1 Substituir o workflow de artifact por publicação autenticada no GHCR das imagens Django, PostgreSQL, Nginx e Traefik para `linux/amd64` e `linux/arm64`; usar `GITHUB_TOKEN` com `contents: read` e `packages: write`, tags `sha-<commit>` e `main`, e verificar sintaxe/permissões do workflow.
- [x] 1.2 Adicionar `org.opencontainers.image.source` às quatro imagens.

## 2. Compose e operação da VM

- [x] 2.1 Alterar os padrões de imagem do `docker-compose.vm.yml` para `ghcr.io/ryofac/...:${PIXU_IMAGE_TAG:-main}`, mantendo overrides locais `PIXU_*_IMAGE`; validar `docker compose config` tanto com o padrão GHCR como com as tags locais.
- [x] 2.2 Atualizar README e `.env.vm.example` com seleção de tag, configuração de registry privado `ghcr.io` no Portainer usando credencial somente de leitura `read:packages`, pull/deploy manual e fallback pelo bundle local; conferir os comandos contra o Compose e não incluir credencial em arquivo versionado.

## 3. Verificação integrada

- [x] 3.1 Executar o workflow no GitHub e confirmar que os quatro pacotes permanecem privados, estão ligados ao repositório e foram publicados com tags `main` e `sha-<commit>` e manifests que incluem amd64/arm64.
- [ ] 3.2 Validar pull autenticado pelo caminho documentado no Portainer/VM e redeploy manual usando uma tag SHA; confirmar que o caminho local de bundle com overrides permanece disponível para rollback.
