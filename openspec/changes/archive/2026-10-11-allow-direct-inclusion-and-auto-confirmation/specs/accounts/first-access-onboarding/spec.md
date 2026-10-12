# Spec Delta

## MODIFIED Requirements

### Requirement: Onboarding no primeiro acesso de conta nova

Contas recém-criadas por cadastro tradicional ou social MUST entrar em um onboarding dedicado antes de acessar as demais páginas autenticadas, mesmo quando o fluxo de login solicitar um destino de retorno. Contas existentes antes da mudança MUST continuar acessando a aplicação sem repetir o onboarding. O onboarding MUST solicitar nome de exibição e um `@username` único, apresentar uma sugestão editável a partir do nome informado e preservar os valores enviados quando houver erro. O onboarding MUST também recomendar que a pessoa considere permitir inclusão direta em cobranças e informar que essa permissão fica desativada até ser ativada por ela no perfil; o onboarding MUST NOT ativá-la automaticamente.

#### Scenario: Primeiro acesso após cadastro tradicional

- **WHEN** uma pessoa entra pela primeira vez em uma conta recém-criada pelo formulário tradicional
- **THEN** o Pixu exibe o onboarding com o nome e o `@username` que já existirem como valores iniciais, permite ajustar ambos e recomenda considerar a permissão de inclusão direta sem ativá-la

#### Scenario: Primeiro acesso após cadastro social

- **WHEN** uma pessoa conclui o primeiro login de uma conta social recém-criada
- **THEN** o Pixu exibe o onboarding com os dados de perfil disponíveis, permite confirmar ou corrigir o `@username` sugerido e informa que a inclusão direta fica desativada até a pessoa ativá-la no perfil

#### Scenario: Destino de retorno informado antes da autenticação

- **WHEN** uma conta nova inicia a autenticação para acessar uma página protegida diferente do onboarding
- **THEN** o Pixu encaminha primeiro a conta ao onboarding antes de exibir a página solicitada

#### Scenario: Conta anterior à mudança

- **WHEN** uma conta existente entra no Pixu depois da implantação
- **THEN** a pessoa segue para a aplicação sem ser obrigada a repetir o onboarding
