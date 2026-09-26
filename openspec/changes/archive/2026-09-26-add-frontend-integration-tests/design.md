# Design

## Context

Veja a motivação em `proposal.md`. O projeto usa Django com templates renderizados no servidor, HTMX e Tailwind, e já executa testes por `pytest`/`pytest-django` dentro do Compose local. `config.settings.test` já isola e-mail em memória e uploads em storage local, mas ainda não há dependência, comando ou teste que execute JavaScript em um navegador. O repositório está no GitHub e não possui workflow de CI versionado.

## Goals / Non-Goals

**Goals:**

- Executar cenários de interface em Chromium headless com o mesmo `pytest` que já cobre o domínio Django.
- Iniciar um servidor Django de teste por cenário, criar dados isolados e interagir pelo DOM acessível em vez de seletores frágeis de CSS.
- Validar HTMX, navegação, upload, textos pt-BR, autorização visível, estados de pagamento e responsividade mobile/desktop.
- Tornar a execução reproduzível por `just`, Docker local e GitHub Actions, mantendo trace, vídeo e screenshot quando houver falha.

**Non-Goals:**

- Não substituir os testes unitários e de integração HTTP existentes.
- Não executar uma matriz completa de Chromium, Firefox e WebKit neste primeiro lote.
- Não adotar snapshot visual global ou comparação pixel a pixel, que seria frágil para a fase atual da interface.
- Não instalar browser ou dependências de teste na imagem de produção, nem usar contas, e-mails, buckets ou dados de produção.

## Decisions

### Usar `pytest-playwright` com `pytest-django`

Os testes de navegador serão escritos em Python com o plugin oficial `pytest-playwright`, usando a API síncrona e o fixture `page`. O fixture `live_server` do `pytest-django` expõe uma aplicação Django real em thread de fundo e exige acesso transacional ao banco; os cenários criarão seus dados por factories antes de navegar.

Essa decisão mantém modelos, factories, configuração de teste e testes browser-level no mesmo ecossistema. O runner Node do Playwright foi considerado, mas exigiria uma segunda infraestrutura de setup de banco e dados Django para cobrir os mesmos fluxos.

### Isolar Chromium em um alvo Docker E2E

O Dockerfile local receberá um estágio ou alvo específico de E2E que instala o Chromium gerenciado pelo Playwright e suas bibliotecas de sistema. Um serviço `e2e` do Compose usará esse alvo e os serviços locais de PostgreSQL, Redis e Garage somente com configurações de teste; Django e Celery de desenvolvimento continuarão sem browser.

O serviço executará `pytest -m e2e` e o `live_server` servirá a aplicação dentro do próprio processo de testes. O comando `just e2e` primeiro compilará os assets com npm e em seguida chamará o serviço E2E. Em CI, o mesmo comando/container será usado para evitar divergência de browser ou de dependências entre a máquina local e GitHub Actions.

### Organizar fixtures, locators e cenários por fluxo

Uma árvore `tests/e2e/` reunirá fixtures de navegador, helpers de autenticação e cenários transversais. Os testes criarão nomes, e-mails, dívidas e arquivos temporários próprios; nenhuma fixture versionada conterá dados reais. O login será exercitado pela interface nos testes de autenticação; os fluxos posteriores poderão reutilizar um helper autenticado para reduzir custo sem esconder o teste do login.

Locators privilegiarão `get_by_role`, `get_by_label`, texto visível e atributos semânticos. `data-testid` só será introduzido quando não houver alvo acessível estável, especialmente para um estado HTMX. Cada teste de viewport verificará que `scrollWidth` não excede `clientWidth` e que a ação final permanece acessível.

### Manter artefatos somente em falhas

O runner será configurado para trace, screenshot e vídeo em falhas, em diretório ignorado pelo Git. A CI publicará esse diretório como artefato quando um cenário falhar. No desenvolvimento, haverá opção de execução headed e depuração, mas o modo padrão será headless Chromium.

### Cobertura inicial orientada a risco

O primeiro lote automatizará: autenticação e telas de conta em pt-BR; criação de cobrança; prévia de rateio HTMX com vírgula decimal; registro de pagamento; escolha e substituição de comprovante; decisão do recebedor; estados e ações permitidas por papel; e os viewports de 390×844 e 1440×900. Requisições de autorização de baixo nível e concorrência permanecem cobertas pelos testes Django já existentes; os E2E confirmarão sua manifestação na interface.

### Auditoria de conformidade com o design do produto

Antes de concluir a mudança, uma tarefa adicional revisará as telas públicas e autenticadas implementadas contra `docs/product-design.md`, sem introduzir comparação por pixels. Em 390×844, os testes verificarão a navegação inferior fixa e se as ações principais podem ser levadas para uma posição não encoberta; em 1440×900, verificarão a navegação lateral, o desaparecimento da navegação inferior e uma composição que não fique presa a uma moldura de celular. Nos dois viewports, verificarão ausência de rolagem horizontal, textos de interface em pt-BR, links/ações principais e identificação semântica do destino ativo.

Essa auditoria usará locators por papel, rótulo e texto e será limitada às telas que existem nesta mudança; diretrizes futuras, como os temas Claro/Escuro/Sistema da seção 2.4 do `docs/product-design.md`, não serão tratadas como comportamento já implementado. Após a primeira execução, os testes poderão ser ajustados para robustez de locators, espera e fixtures, mas asserções não devem ser enfraquecidas para fazer passar uma divergência confirmada do contrato visual. Divergências reais do produto serão reportadas separadamente para mudança aprovada.

## Risks / Trade-offs

- [Browser e bibliotecas aumentam tempo e tamanho da imagem E2E] → O browser fica em alvo de teste separado, somente Chromium no lote inicial, e o cache de build será reutilizado.
- [Cenários browser-level são mais lentos] → A suíte fica marcada como `e2e` e tem comando próprio; os testes atuais continuam rápidos e independentes de navegador.
- [Dados podem vazar entre servidor em thread e teste] → Usar `live_server`, acesso transacional, factories por cenário e limpeza automática do banco de testes.
- [Seletores ficam frágeis após ajustes visuais] → Preferir semântica acessível e comportamento observável; reservar `data-testid` para casos sem alternativa estável.
- [Falhas são difíceis de reproduzir em CI] → Reter trace, vídeo, screenshot e a saída do teste apenas quando falhar.
- [Upload pode tocar storage externo] → Fixar `config.settings.test`, storage local temporário e arquivos sintéticos válidos.

## Migration Plan

1. Adicionar a dependência e o alvo Docker E2E sem modificar imagem ou Compose de produção.
2. Criar fixtures, marker e comando local; executar primeiro o smoke test de autenticação para validar servidor, browser e assets.
3. Incluir progressivamente os cenários de cobrança e pagamento.
4. Adicionar GitHub Actions que execute o mesmo comando e retenha artefatos de falha.
5. Em caso de regressão de infraestrutura, o rollback remove o serviço/alvo E2E e a dependência de desenvolvimento, sem migração de dados nem efeito no runtime de produção.
