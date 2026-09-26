# Tasks

## 1. Toolchain E2E isolada

- [x] 1.1 Adicionar `pytest-playwright` ao grupo de desenvolvimento, atualizar `uv.lock` e instalar Chromium somente no alvo de teste; verificar `uv sync --locked --group dev` e `python -m playwright install --list` no ambiente E2E.
- [x] 1.2 Criar estágio Docker e serviço Compose `e2e` separados do Django/Celery de desenvolvimento e da imagem de produção; verificar `docker compose -f docker-compose.local.yml config` e que o alvo E2E consegue executar Chromium headless.
- [x] 1.3 Configurar marker, diretório ignorado de artefatos e opções de trace/screenshot/vídeo em falhas; adicionar `just e2e` e documentar sua execução, depuração headed e localização dos artefatos no README; verificar `just --list` e o comando documentado.

## 2. Base dos testes de navegador

- [x] 2.1 Criar `tests/e2e/` com fixtures de `live_server`, banco transacional, factories/dados sintéticos, arquivos temporários válidos e helper de autenticação; verificar que um smoke test abre a aplicação de teste sem acessar storage, e-mail ou banco externos.
- [x] 2.2 Criar helpers para locators acessíveis, espera de fragmentos HTMX, captura de estado e checagem de overflow; verificar os helpers em teste que intencionalmente exercita atualização HTMX e os viewports 390×844 e 1440×900.

## 3. Conta, localização e navegação

- [x] 3.1 Automatizar cadastro, login, logout e solicitação de recuperação de senha pelo navegador, usando dados isolados e validando mensagens em pt-BR; verificar `pytest -m e2e tests/e2e/test_authentication.py`.
- [x] 3.2 Cobrir perfil, gerenciamento de e-mail e navegação ativa em mobile e desktop, incluindo ausência de texto padrão em inglês e alcance do conteúdo acima da navegação fixa; verificar o arquivo de teste de contas em Chromium nos dois viewports.

## 4. Cobranças e HTMX

- [x] 4.1 Cobrir a criação de cobrança pelo navegador e a prévia HTMX com `150,00`, incluindo erro localizado para entrada inválida e persistência apenas após envio válido; verificar o cenário em `tests/e2e/test_charges.py`.
- [x] 4.2 Cobrir detalhe de cobrança em mobile e desktop, pluralização e ausência de overflow horizontal em formulário longo e cartão de participantes; verificar asserções de viewport no mesmo arquivo de teste.

## 5. Pagamentos e comprovantes

- [x] 5.1 Cobrir registro de pagamento parcial, chave Pix, seleção de comprovante, nome de arquivo exibido, substituição e remoção enquanto pendente; verificar `tests/e2e/test_payments.py` com arquivo sintético PDF/JPEG/PNG válido.
- [x] 5.2 Cobrir a decisão manual pelo recebedor, estados pendente/confirmado/rejeitado, restrição visual de ações por papel e acesso privado ao comprovante; verificar os cenários com pagador, recebedor e terceiro autenticados.

## 6. Execução contínua e validação integrada

- [x] 6.1 Adicionar workflow GitHub Actions que compila assets, prepara o alvo E2E, executa `just e2e` e publica `test-results/` somente em falhas; verificar a sintaxe do workflow e que ele não usa segredos nem serviços de produção.
- [x] 6.2 Executar a suíte rápida existente, a suíte E2E Chromium e `git diff --check`; verificar que artefatos passam em sucesso, falhas preservam trace/screenshot/vídeo e a imagem de produção não recebeu dependências de browser.

## 7. Auditoria da interface conforme `docs/product-design.md`

- [x] 7.1 Criar testes E2E de conformidade para telas públicas e autenticadas, cobrindo em 390×844 a composição mobile, a navegação inferior fixa e o alcance das ações; em 1440×900, a navegação lateral e a ausência da navegação inferior. Validar também textos visíveis em pt-BR, navegação entre páginas/estado ativo e ausência de overflow horizontal, usando locators semânticos.
- [x] 7.2 Corrigir os testes introduzidos na auditoria após executá-los: ajustar locators, esperas, fixtures ou asserções frágeis sem reduzir cobertura nem aceitar divergências de `docs/product-design.md`; repetir a suíte E2E e a rápida e registrar separadamente qualquer divergência real do produto que exija mudança fora do escopo desta tarefa.
