# Pixu

<p align="center">
  <img src="pixu/static/images/pixu-logo.svg" alt="Símbolo da marca Pixu" width="112">
  <br><strong style="font-size: 2rem">PiXu</strong>
</p>

<p align="center"><strong>Divida despesas com clareza e acompanhe cada obrigação.</strong></p>

O Pixu organiza rateios, cobranças e pagamentos informados entre pessoas. O dinheiro não passa pela aplicação: cada transferência é feita no banco e o Pixu registra o estado informado pelas participantes.

## O que o Pixu faz

- Cria cobranças com contas Pixu ou convidadas externas por link.
- Calcula e acompanha cotas, inclusive itens extras e pagamentos parciais.
- Permite registrar Pix, anexar comprovante privado e confirmar ou rejeitar o pagamento.
- Sugere compensações entre dívidas recíprocas.
- Oferece inclusão direta e confirmação automática somente quando a pessoa recebedora ativa essas preferências de confiança.

O Pixu não valida chaves Pix nem verifica transferências junto a bancos. A confirmação automática apenas registra a confiança configurada pela recebedora; não é comprovação bancária.

## Desenvolvimento local

Requisitos: Docker com Compose, Node.js 20.19+ e npm. Para comandos Python fora do container, use Python 3.14 e `uv`.

```sh
npm ci
npm run build
docker compose -f docker-compose.local.yml up --build --renew-anon-volumes --force-recreate
```

A aplicação fica em `http://localhost:8000`. Para recompilar o CSS durante a edição, execute `npm run css:watch` em outro terminal. O e-mail local é exibido nos logs do Django.

```sh
just pytest
just e2e
just manage check
just logs django
```

`just pytest` executa a suíte Python. `just e2e` compila os assets e executa a suíte Playwright isolada. Para usar comandos Python fora do Docker:

```sh
uv sync --locked --group dev
```

## Configuração

O ambiente local lê `.envs/.local/` e `.env`; produção com domínio usa `.envs/.production/`; a stack de VM usa `.env.vm`, importado pela plataforma de gerenciamento. Valores concretos e segredos ficam somente em arquivos ignorados pelo Git ou no cofre de segredos do ambiente.

Os exemplos versionados são a referência para variáveis de OAuth, SMTP, PostgreSQL, Redis/Celery e armazenamento privado de comprovantes:

- [`.env.vm.example`](.env.vm.example) para a VM;
- [`.envs/.production/.django.example`](.envs/.production/.django.example) e [`.envs/.production/.postgres.example`](.envs/.production/.postgres.example) para produção com domínio.

## Deploy

O caminho recomendado para VM usa a stack Compose com imagens em um registry privado. Consulte o [guia de deploy em VM](docs/operations/deploy-vm.md).

## Documentação do projeto

- [Changelog](CHANGELOG.md)
- [Decisões de produto e interface](docs/product-design.md)
- [Requisitos vigentes](openspec/specs/)
- [Histórico de mudanças](openspec/changes/archive/)
- [Instruções de contribuição e arquitetura](AGENTS.md)
