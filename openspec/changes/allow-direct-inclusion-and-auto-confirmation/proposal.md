# Proposal

## Why

Contas Pixu precisam poder autorizar previamente sua inclusão em novas cobranças, reduzindo convites repetitivos sem retirar o controle da própria pessoa. Recebedores também precisam poder automatizar a confirmação no Pixu de pagamentos declarados por uma conta em uma dívida específica, sem sugerir que a transferência externa foi verificada.

## What Changes

- Adicionar à conta uma preferência opcional para inclusão direta em cobranças futuras, desativada por padrão, com orientação no onboarding e edição no próprio perfil.
- Aceitar imediatamente a participação selecionada quando a preferência daquela conta estiver ativada; manter convites normais para as demais contas e não alterar participações existentes quando a preferência mudar.
- Permitir que o recebedor habilite confirmação automática no Pixu separadamente para cada dívida, mantendo a confirmação manual como padrão.
- Confirmar automaticamente pagamentos futuros válidos declarados por pagadores autenticados para uma dívida habilitada, inclusive valores parciais, registrando a origem automática da confirmação.
- Manter pagamentos de convidados no fluxo de confirmação manual e não adicionar verificação bancária, execução de transferência ou reversão automática.

## Capabilities

### New Capabilities

- `accounts/charge-preferences`: preferência da própria conta para autorizar inclusão direta em cobranças futuras.

### Modified Capabilities

- `accounts/first-access-onboarding`: o onboarding recomenda considerar a nova preferência, mas a mantém desativada e editável depois no perfil.
- `charges`: a criação respeita a autorização explícita de cada conta selecionada, aceitando sua participação sem convite e mantendo o aceite normal para as demais.
- `settlements/payments`: confirmação automática controlada pelo recebedor em cada dívida, para futuras declarações de pagamento autenticadas, com confirmação manual como padrão e rastreabilidade da origem.

## Impact

- Modelos Django e migrações em `pixu.accounts`, `pixu.charges` e `pixu.settlements`.
- Templates de perfil/onboarding e detalhe da cobrança, criação de cobranças, configuração de dívidas e serviços/views de registro de pagamentos.
- Sem dependências novas, API pública, integração bancária, movimentação de dinheiro ou processamento em segundo plano.
