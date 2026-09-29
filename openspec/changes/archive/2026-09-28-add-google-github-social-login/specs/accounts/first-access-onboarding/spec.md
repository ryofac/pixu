# Spec Delta

## Purpose

Orienta novas contas Pixu, criadas por cadastro tradicional ou social, a confirmar sua identificação e decidir se já querem cadastrar uma chave Pix.

## ADDED Requirements

### Requirement: Onboarding no primeiro acesso de conta nova

Contas recém-criadas por cadastro tradicional ou social MUST entrar em um onboarding dedicado antes de acessar as demais páginas autenticadas, mesmo quando o fluxo de login solicitar um destino de retorno. Contas existentes antes da mudança MUST continuar acessando a aplicação sem repetir o onboarding. O onboarding MUST solicitar nome de exibição e um `@username` único, apresentar uma sugestão editável a partir do nome informado e preservar os valores enviados quando houver erro.

#### Scenario: Primeiro acesso após cadastro tradicional

- **WHEN** uma pessoa entra pela primeira vez em uma conta recém-criada pelo formulário tradicional
- **THEN** o Pixu exibe o onboarding com o nome e o `@username` que já existirem como valores iniciais e permite ajustar ambos

#### Scenario: Primeiro acesso após cadastro social

- **WHEN** uma pessoa conclui o primeiro login de uma conta social recém-criada
- **THEN** o Pixu exibe o onboarding com os dados de perfil disponíveis e permite confirmar ou corrigir o `@username` sugerido

#### Scenario: Destino de retorno informado antes da autenticação

- **WHEN** uma conta nova inicia a autenticação para acessar uma página protegida diferente do onboarding
- **THEN** o Pixu encaminha primeiro a conta ao onboarding antes de exibir a página solicitada

#### Scenario: Conta anterior à mudança

- **WHEN** uma conta existente entra no Pixu depois da implantação
- **THEN** a pessoa segue para a aplicação sem ser obrigada a repetir o onboarding

### Requirement: Cadastro opcional da chave Pix no onboarding

O onboarding MUST permitir que a pessoa salve uma chave Pix em texto livre ou escolha “Fazer depois”. A ação “Salvar e continuar” MUST exigir uma chave não vazia; “Fazer depois” MUST persistir nome e `@username`, manter a chave Pix vazia e permitir o uso normal da aplicação. O formulário MUST informar: “A chave Pix é informada por você. O Pixu não verifica a chave junto ao banco.” O Pixu MUST NOT afirmar que verificou a chave.

#### Scenario: Pessoa salva a chave Pix

- **WHEN** a pessoa envia nome, `@username` único e chave Pix pela ação “Salvar e continuar”
- **THEN** o Pixu salva os dados na própria conta, conclui o onboarding e encaminha ao dashboard

#### Scenario: Pessoa deixa a chave Pix para depois

- **WHEN** a pessoa envia nome e `@username` válido pela ação “Fazer depois”
- **THEN** o Pixu salva nome e `@username`, mantém a chave vazia, conclui o onboarding e encaminha ao dashboard

#### Scenario: Username inválido ou já utilizado

- **WHEN** a pessoa envia um `@username` inválido ou já associado a outra conta
- **THEN** o Pixu não conclui o onboarding, mantém os valores enviados e apresenta um erro junto ao campo correspondente

### Requirement: Aviso contextual de chave Pix ausente

Quando a conta autenticada não tiver chave Pix, o dashboard MUST exibir um aviso de que a pessoa pode participar de cobranças, mas precisa cadastrar uma chave para recebê-las, com ação “Configurar chave Pix”. Ao criar uma cobrança em que a própria pessoa autenticada será a recebedora, o formulário MUST apresentar um aviso contextual sobre a ausência de chave. A ausência da chave MUST NOT impedir participação em cobranças nem bloquear a criação da cobrança.

#### Scenario: Dashboard de pessoa sem chave Pix

- **WHEN** uma pessoa autenticada acessa o dashboard sem chave Pix cadastrada
- **THEN** o dashboard explica a limitação para receber pagamentos e oferece a ação de configurar a chave

#### Scenario: Cobrança com a própria pessoa como recebedora

- **WHEN** uma pessoa sem chave Pix inicia uma cobrança em que ela própria é a recebedora
- **THEN** o formulário informa que a chave está ausente e oferece o perfil como caminho para configurá-la, sem bloquear o formulário

#### Scenario: Pessoa participa sem chave Pix

- **WHEN** uma pessoa sem chave Pix é convidada a participar de uma cobrança recebida por outra pessoa
- **THEN** ela pode consultar e responder ao convite normalmente
