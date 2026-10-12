# Deploy em VM

Este guia descreve o procedimento de publicação do Pixu em uma VM com imagens privadas, proxy HTTPS e uma plataforma de gerenciamento de containers. Ele não registra identificadores do ambiente nem credenciais de operação.

## Pré-requisitos

- Um hostname público apontando para o IP da VM.
- Portas 80 e 443 liberadas para a VM.
- Docker e a plataforma de gerenciamento de containers funcionando na VM.
- Acesso de leitura ao registry privado de imagens.

## Configuração

1. Copie [`.env.vm.example`](../../.env.vm.example) para `.env.vm`, preencha os segredos e importe-o como variáveis da stack. Nunca versione esse arquivo.
2. Configure o hostname e o e-mail de emissão do certificado no proxy HTTPS usado pela stack. Mantenha essa configuração na VM, fora do repositório, quando ela identificar o ambiente.
3. Cadastre a credencial de leitura do registry privado na plataforma de containers. Use token de escopo mínimo; ele pertence às credenciais do registry, nunca ao `.env.vm` ou ao Compose.

## Publicação e atualização

O pipeline de integração publica as imagens da stack para as arquiteturas suportadas, com uma tag de acompanhamento e tags imutáveis associadas ao commit.

Crie uma stack a partir de [`docker-compose.vm.yml`](../../docker-compose.vm.yml), associe a credencial do registry e habilite o pull das imagens no deploy. Prefira uma tag imutável no `PIXU_IMAGE_TAG` para um deploy reproduzível; a tag de acompanhamento serve apenas para atualizar ao estado mais recente.

Após o primeiro deploy — e sempre que houver migrações — execute no container Django:

```sh
python manage.py migrate
```

O proxy HTTPS emite e renova o certificado. Inclua os volumes persistentes do banco, dos comprovantes e dos certificados na estratégia de backup da VM.

## Alternativa sem registry

Em uma máquina com Docker, Buildx, Node.js e npm:

```sh
./scripts/build-vm-images.sh
sha256sum -c pixu-vm-images.tar.gz.sha256
tar -xzf pixu-vm-images.tar.gz
docker load -i images.tar
```

Defina os overrides de imagem documentados no Compose para que a stack use as imagens carregadas localmente.
