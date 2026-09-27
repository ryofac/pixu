# Tasks

## 1. Atualizar contrato de produto

- [x] 1.1 Atualizar `docs/product-design.md` com os estados cancelado/revogado, permissões distintas de criador e recebedor, acesso a comprovantes na lista de pagantes, exclusão restrita ao superusuário e narrativa de três seções; verificar que não contradiz as specs da mudança.

## 2. Estados e cancelamento lógico

- [x] 2.1 Adicionar estados `CANCELLED` à cobrança e participação e `REVOKED` ao pagamento, metadados de cancelamento e constraints/migração correspondentes; verificar `makemigrations --check` e testes dos modelos.
- [x] 2.2 Implementar serviço transacional para cancelamento pelo criador, invalidar convites pendentes e revogar pagamentos sem apagar registros nem comprovantes; testar pagamento pendente/confirmado, motivo vazio/preenchido, repetição, autorização e recusa quando existir compensação em qualquer lado.
- [x] 2.3 Excluir cobranças canceladas e pagamentos revogados de ações e totais ativos, preservando a cobrança no histórico visível aos envolvidos; cobrir listas, convites, dashboard e tentativa de novas operações em testes de serviço/view.

## 3. Exclusão absoluta administrativa

- [x] 3.1 Implementar auditoria mínima independente e serviço transacional de exclusão absoluta, com fila transitória e limpeza idempotente/repetível dos comprovantes no storage; testar remoção de cobrança, participações, dívidas, pagamentos e arquivos, persistência da auditoria e bloqueio por compensação.
- [x] 3.2 Adicionar confirmação administrativa para exclusão absoluta, motivo opcional e autorização efetiva exclusiva para superusuários; testar superusuário, staff sem privilégio, tentativa por URL/POST e ausência de dados da cobrança na auditoria.

## 4. Acesso do criador aos comprovantes

- [x] 4.1 Autorizar leitura privada para o criador da cobrança e servir o arquivo como prévia inline, sem ampliar permissões de escrita ou decisão; testar pagador, recebedor, criador não recebedor, terceiro e conteúdo de `Content-Disposition`.
- [x] 4.2 Exibir, na linha de cada pagante, links para seus comprovantes disponíveis durante o histórico, sem botões de confirmar/rejeitar para o criador não recebedor; verificar com testes de view/template e autorização direta da URL.

## 5. Interface de cancelamento

- [x] 5.1 Adicionar ao detalhe da cobrança do criador a confirmação simples de cancelamento com motivo opcional, mensagens para bloqueio por compensação e estado de histórico sem ações financeiras; validar POST convencional e HTMX, autorização, acessibilidade e textos localizados.

## 6. Landing page em narrativa vertical

- [x] 6.1 Reorganizar a landing em três seções sequenciais para rateio/aceite, pagamento/comprovante/confirmação e saldos/compensações/cancelamento; preservar marca, CTAs e temas, usar exemplos abstratos sem “demo”/“demonstração” e verificar build Tailwind e testes de conteúdo.
- [x] 6.2 Cobrir rolagem natural, visibilidade das seções, legibilidade e ausência de overflow em mobile e desktop nos temas claro e escuro; validar por Playwright sem scroll trapping nem animações obrigatórias.

## 7. Regressão integrada

- [x] 7.1 Rodar `just pytest` e `just e2e`; confirmar fluxos financeiros anteriores, upload privado local/S3-like, landing autenticada versus pública, migrações e ausência de regressões.
- [x] 7.2 Marcar as mensagens literais de feedback restantes nas views de cobranças e pagamentos com a API de tradução do Django, cobrindo notificações convencionais e mensagens de estado HTMX.
- [x] 7.3 Gerar um `favicon.ico` com tamanhos 16, 32 e 48 px a partir do símbolo SVG local aprovado e referenciá-lo no template-base.
