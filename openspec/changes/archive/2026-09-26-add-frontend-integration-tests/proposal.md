# Proposal

## Why

Os testes atuais exercitam regras, views e fragmentos HTMX no servidor, mas não repetem interações em um navegador real. Precisamos transformar a validação visual e funcional recente de pagamentos, comprovantes e responsividade em testes determinísticos, reproduzíveis localmente e na integração contínua.

## What Changes

- Adicionar o `pytest-playwright` às dependências de desenvolvimento e preparar Chromium headless somente nos ambientes de teste e desenvolvimento.
- Criar infraestrutura de testes browser-level baseada em `pytest-django`, `live_server`, factories existentes e configurações isoladas de banco, e-mail e storage.
- Disponibilizar comando `just` específico para a suíte E2E, separado do `pytest` rápido, com build dos assets antes da execução.
- Registrar traces, screenshots e vídeo apenas em falhas, sem versionar artefatos gerados.
- Cobrir os fluxos críticos de autenticação, cobrança, prévia HTMX, pagamento, comprovante, autorização, localização pt-BR e responsividade em viewports mobile e desktop.
- Auditar a interface renderizada contra `docs/product-design.md`, com foco explícito na estrutura mobile/desktop, textos pt-BR e navegabilidade, ajustando os testes sem mascarar divergências reais.
- Garantir que os testes de navegador não dependam de conta, arquivo, e-mail, bucket ou banco de produção.

## Capabilities

### New Capabilities

Nenhuma. A mudança adiciona infraestrutura de qualidade e não altera o comportamento contratado do produto.

### Modified Capabilities

Nenhuma. Os requisitos existentes de cobranças e pagamentos permanecem inalterados; esta entrega somente os exercita por navegador.

## Impact

- `pyproject.toml` e `uv.lock` para a dependência de teste.
- Dockerfile local e automação `just` para instalar/executar o browser de teste sem afetar a imagem de produção.
- Configuração pytest, `.gitignore`, fixtures/factories e nova árvore de testes E2E.
- Pipeline de CI futuro para instalar Chromium, compilar assets e publicar artefatos de falha.
