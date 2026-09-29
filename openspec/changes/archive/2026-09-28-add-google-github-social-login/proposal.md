# Proposal

## Why

O Pixu já usa django-allauth, mas oferece somente autenticação por senha. A tela de entrada aprovada prevê Google e GitHub e um primeiro acesso para concluir nome de exibição, `@username` e, se a pessoa quiser, sua chave Pix.

## What Changes

- Habilitar login e criação de contas por Google e GitHub através do django-allauth existente, com credenciais OAuth fornecidas pelo ambiente.
- Integrar os botões sociais à tela de autenticação aprovada, mantendo cadastro, entrada por senha, confirmação de e-mail e recuperação de acesso.
- Encaminhar contas novas — tradicionais ou sociais — ao onboarding de primeiro acesso; permitir salvar a chave Pix ou deixá-la para depois.
- Avisar no dashboard quando a chave Pix estiver ausente e contextualizar sua falta ao criar uma cobrança em que a própria pessoa será recebedora.
- Usar somente e-mail confirmado pelos provedores para autenticar uma conta local correspondente; não persistir tokens OAuth nem associar silenciosamente um novo provedor a uma conta local preexistente.

## Capabilities

### New Capabilities

- `accounts/social-authentication`: entrada e cadastro com Google e GitHub usando django-allauth.
- `accounts/first-access-onboarding`: conclusão do primeiro acesso para contas tradicionais e sociais, com username e chave Pix opcional.

### Modified Capabilities

## Impact

Afeta `config/settings/`, `pixu/accounts/`, os templates allauth e do dashboard, a configuração de ambiente local e os exemplos de produção. A versão fixada de django-allauth já inclui `socialaccount`; não é necessária nova dependência. Credenciais e URIs de callback dos aplicativos OAuth dependem de configuração nos consoles Google e GitHub e no ambiente de execução.
