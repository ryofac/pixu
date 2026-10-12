# Tasks

## 1. Publicação e seleção das imagens

- [x] 1.1 Publicar Django, PostgreSQL, Nginx e Traefik como pacotes GHCR privados multi-arquitetura (`linux/amd64` e `linux/arm64`) com `GITHUB_TOKEN`, permissões mínimas e tags `main` e `sha-<commit>`.
- [x] 1.2 Apontar `docker-compose.vm.yml` para os pacotes GHCR por padrão, preservar overrides para imagens locais e manter Redis no Docker Hub.
- [x] 1.3 Documentar no README como configurar leitura privada no Portainer, fixar uma tag SHA, fazer redeploy manual e usar o bundle local como fallback.

## 2. Verificação e contingência

- [x] 2.1 Executar o workflow GHCR e verificar publicação privada dos quatro pacotes com as tags e arquiteturas esperadas, conforme validação registrada na change arquivada `publish-vm-images-to-private-ghcr`.
- [x] 2.2 Confirmar a sintaxe do script local `scripts/build-vm-images.sh` com `bash -n` e manter o bundle e seus overrides disponíveis como fallback.
- [ ] 2.3 Validar nesta execução um build local completo do bundle e o pull autenticado/redeploy manual na VM pelo Portainer; requer Docker disponível e execução no ambiente de deploy.
