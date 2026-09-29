# Social Authentication Specification

## Purpose

Permite entrar e criar uma conta Pixu com Google ou GitHub, mantendo a autenticação local disponível e limitando o uso dos dados OAuth ao necessário para identificar a pessoa.

## Requirements

### Requirement: Entrada social com Google e GitHub

O sistema MUST permitir que uma pessoa inicie a entrada ou o cadastro com Google ou GitHub quando as credenciais do respectivo provedor estiverem configuradas no ambiente. A tela MUST apresentar os botões sociais antes do formulário tradicional, com rótulos “Continuar com Google” e “Continuar com GitHub”, ícones SVG locais, área de toque de ao menos 48px e foco visível nos temas claro e escuro. A autenticação MUST usar o fluxo OAuth mantido pelo provedor e pelo allauth, com proteção CSRF e sem armazenar tokens de acesso. Quando um provedor não estiver configurado, seu botão MUST ficar oculto e a entrada tradicional MUST continuar disponível.

#### Scenario: Pessoa inicia entrada com provedor configurado

- **WHEN** a pessoa envia o botão de um provedor configurado
- **THEN** o Pixu inicia o fluxo OAuth correspondente por uma requisição POST protegida por CSRF e retorna ao fluxo do Pixu após o callback

#### Scenario: Provedor sem credenciais disponíveis

- **WHEN** as credenciais de um provedor não estão configuradas no ambiente
- **THEN** o botão desse provedor não é apresentado e a pessoa ainda pode entrar ou se cadastrar com e-mail e senha

#### Scenario: Erro ou cancelamento no provedor

- **WHEN** a pessoa cancela a autorização ou o provedor retorna uma falha
- **THEN** o Pixu mostra uma mensagem em pt-BR que explica que a entrada não foi concluída e oferece um caminho para tentar novamente ou usar a entrada tradicional

### Requirement: Conta social autenticada por e-mail confirmado

O sistema MUST exigir um endereço de e-mail para novas contas sociais. Um e-mail que Google ou GitHub informa como verificado MAY autenticar uma conta Pixu existente com o mesmo endereço, sem criar outra conta. Essa autenticação por e-mail verificado MUST NOT persistir uma associação de provedor à conta local preexistente. Contas novas criadas por um provedor MUST manter a identidade social necessária para permitir logins futuros. Endereços sem confirmação do provedor MUST passar pela confirmação de e-mail configurada para cadastro tradicional. O sistema MUST NOT armazenar tokens OAuth.

#### Scenario: Novo cadastro social permitido

- **WHEN** uma pessoa conclui o OAuth de Google ou GitHub com um e-mail confirmado que ainda não pertence a uma conta Pixu e o cadastro está aberto
- **THEN** o Pixu cria uma conta usando os dados de perfil disponíveis, inicia uma sessão e encaminha a pessoa ao onboarding de primeiro acesso

#### Scenario: E-mail confirmado corresponde a uma conta local

- **WHEN** uma pessoa autentica com Google ou GitHub e o provedor confirma um e-mail já associado a uma conta Pixu
- **THEN** o Pixu autentica a conta existente sem criar uma conta duplicada nem salvar uma associação permanente de provedor

#### Scenario: Cadastro social fechado

- **WHEN** uma pessoa sem conta Pixu tenta entrar por Google ou GitHub enquanto o cadastro está fechado
- **THEN** o sistema não cria a conta e apresenta uma mensagem em pt-BR que orienta a pessoa sobre a indisponibilidade do cadastro

### Requirement: Entrada tradicional continua disponível

O sistema MUST preservar o cadastro tradicional, a entrada por nome de usuário ou e-mail e senha, a confirmação de e-mail, o logout e a recuperação de senha. A inclusão de provedores MUST NOT tornar credenciais sociais obrigatórias.

#### Scenario: Entrada com e-mail ou nome de usuário

- **WHEN** uma pessoa informa e-mail ou nome de usuário e senha válidos
- **THEN** o Pixu autentica a conta local e aplica o redirecionamento de primeiro acesso quando necessário

#### Scenario: Recuperação da conta local

- **WHEN** uma pessoa solicita redefinição de senha para uma conta local
- **THEN** o fluxo existente de recuperação por e-mail continua disponível e não revela se um endereço está cadastrado
