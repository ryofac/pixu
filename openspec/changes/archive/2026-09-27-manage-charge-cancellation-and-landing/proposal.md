# Proposal

## Why

O Pixu já mantém cobranças, pagamentos, comprovantes e compensações, mas ainda não oferece um caminho seguro para encerrar uma cobrança nem permite que seu criador consulte comprovantes enviados por participantes quando não é o recebedor. A landing page também não explica, em uma sequência curta e responsiva, como os fluxos reais se conectam.

## What Changes

- Permitir que o criador cancele logicamente uma cobrança, com motivo opcional, preservando a cobrança e os pagamentos no histórico e marcando-os como revogados; a ação não faz estorno nem recria dívidas.
- Invalidar convites pendentes e retirar cobranças canceladas de totais e ações ativas, mantendo-as visíveis para as pessoas envolvidas como histórico.
- Permitir exclusão absoluta somente por superusuário no Django Admin, removendo a cobrança, dívidas, pagamentos e comprovantes vinculados e registrando uma auditoria mínima com identificador, autor, data e motivo opcional.
- Bloquear ambas as formas de cancelamento quando houver compensação vinculada à cobrança, preservando o histórico financeiro entre dívidas recíprocas.
- Dar ao criador acesso somente de leitura aos comprovantes dos pagamentos da cobrança e apresentar o comprovante em prévia no navegador, sem conceder poder de confirmação ou rejeição.
- Atualizar a landing page para contar em seções verticais sequenciais como criar rateios, acompanhar pagamentos e saldos e gerenciar cobranças. Usar exemplos abstratos da interface, sem chamar o conteúdo de “demo” ou “demonstração”, e descrever somente capacidades implementadas.
- Atualizar `docs/product-design.md` para manter a apresentação pública e as telas de cobrança coerentes com os fluxos entregues.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `charges`: adicionar cancelamento lógico pelo criador, exclusão absoluta auditada por superusuário e bloqueio quando houver compensações.
- `settlements/payments`: ampliar o acesso de leitura a comprovantes para o criador da cobrança e abrir arquivos em prévia, mantendo confirmação exclusiva do recebedor.
- `product-experience/landing-page`: substituir os cartões atuais por uma narrativa vertical responsiva, atualizada com funcionalidades disponíveis e exemplos abstratos.

## Impact

- Apps Django `pixu.charges`, `pixu.settlements` e `pixu.dashboard`, suas migrações, views, serviços, formulários, templates, rotas do admin e testes.
- Armazenamento privado local/S3-like dos comprovantes: exclusão absoluta deve remover os objetos associados; cancelamento lógico os conserva enquanto o pagamento permanecer no histórico.
- `docs/product-design.md`, a landing page em `pixu/templates/pages/landing.html` e testes de regressão mobile/desktop, temas e autorização.
