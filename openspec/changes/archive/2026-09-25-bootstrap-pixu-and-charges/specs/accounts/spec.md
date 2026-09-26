## Purpose

Esta capacidade permite que qualquer pessoa crie e administre sua própria conta Pixu, autentique-se e mantenha os dados de perfil necessários para participar de cobranças.

## ADDED Requirements

### Requirement: Pessoa pode criar e acessar sua conta

The system SHALL permitir cadastro público por e-mail, nome de usuário e senha, entrada e saída de sessão. A confirmação e as mensagens da conta SHALL usar o serviço de e-mail configurado no ambiente.

#### Scenario: Cadastro válido
- **WHEN** uma pessoa envia dados válidos e únicos pelo formulário de cadastro
- **THEN** o sistema cria sua conta e inicia o fluxo de confirmação de e-mail configurado

#### Scenario: Dados de cadastro inválidos
- **WHEN** a pessoa envia e-mail ou nome de usuário inválido, duplicado, ou uma senha que não atende às regras configuradas
- **THEN** o cadastro não é criado e o formulário identifica os campos que precisam de correção

#### Scenario: Login e logout
- **WHEN** uma pessoa cadastrada informa credenciais válidas e depois escolhe sair
- **THEN** o sistema cria a sessão autenticada e a encerra no logout

### Requirement: Pessoa pode recuperar o acesso por e-mail

The system SHALL oferecer recuperação de senha por e-mail configurado sem enviar ou expor a senha existente.

#### Scenario: Redefinição concluída
- **WHEN** uma pessoa solicita recuperação para seu endereço cadastrado e usa um link válido dentro de sua validade
- **THEN** o sistema permite definir uma nova senha e a pessoa consegue autenticar-se com ela

#### Scenario: Link inválido ou expirado
- **WHEN** uma pessoa usa um link de recuperação inválido, expirado ou já utilizado
- **THEN** o sistema não altera a senha e orienta a pessoa a solicitar outra recuperação

### Requirement: Pessoa pode editar seus próprios dados de perfil

The system SHALL permitir que uma pessoa autenticada edite seu perfil e cadastre ou altere uma chave Pix informada por ela. O Pixu SHALL deixar claro que não verifica a chave junto à instituição financeira.

#### Scenario: Atualização do próprio perfil
- **WHEN** a pessoa autenticada salva dados válidos de seu perfil e chave Pix
- **THEN** os dados ficam associados à sua própria conta e são persistidos

#### Scenario: Tentativa de alterar perfil alheio
- **WHEN** uma pessoa tenta alterar o perfil ou a chave Pix de outra conta
- **THEN** o servidor nega a ação e não modifica os dados

### Requirement: Formulários de conta validam e protegem os dados

The system SHALL validar os dados de conta no servidor em requisições convencionais e HTMX, exigir CSRF, escapar texto renderizado e apresentar erros acionáveis sem persistir dados inválidos.

#### Scenario: Submissão inválida por HTMX
- **WHEN** um formulário HTMX de conta contém dados inválidos ou não inclui um token CSRF válido
- **THEN** o servidor rejeita a requisição, não persiste alterações e retorna erros associados ao formulário

#### Scenario: Texto de perfil é exibido
- **WHEN** um campo de perfil contém caracteres interpretáveis como marcação HTML
- **THEN** a página apresenta o texto escapado sem executá-lo como marcação ou script
