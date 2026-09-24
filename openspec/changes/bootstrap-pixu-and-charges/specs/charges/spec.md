## Purpose

Esta capacidade permite criar cobranças compartilhadas e converter convites aceitos em dívidas com cotas inteiras em centavos, mantendo a cobrança inativa enquanto faltarem respostas.

## ADDED Requirements

### Requirement: Criador pode criar cobrança com rateio exato

The system SHALL permitir a uma pessoa autenticada criar uma cobrança com título, descrição opcional, valor positivo em centavos e usuários já cadastrados. O criador SHALL ser incluído automaticamente como participante e único recebedor. Uma pessoa não pode aparecer mais de uma vez na mesma cobrança.

#### Scenario: Prévia e criação de cobrança
- **WHEN** o criador informa dados válidos e seleciona participantes existentes
- **THEN** o sistema mostra a cobrança e as cotas antes de salvá-la e cria os convites correspondentes após a confirmação

#### Scenario: Divisão com centavos residuais
- **WHEN** o valor não pode ser dividido igualmente em centavos inteiros
- **THEN** o sistema distribui os centavos residuais por uma ordem determinística dos participantes, e a soma das cotas permanece igual ao total

#### Scenario: Criador não deve a si mesmo
- **WHEN** o sistema calcula a cota do criador
- **THEN** a cota é incluída no rateio e nenhuma dívida é criada do criador para si próprio

#### Scenario: Dados inválidos ou participante repetido
- **WHEN** o criador informa valor não positivo, título inválido, usuário inexistente ou participante duplicado
- **THEN** a cobrança não é criada e o formulário mostra o erro correspondente

### Requirement: Participantes podem aceitar ou recusar convite

The system SHALL apresentar convites recebidos como `PENDING` e permitir que somente o destinatário do convite os aceite ou recuse. Um aceite SHALL criar uma única dívida ligada à participação; convite recusado não cria dívida.

#### Scenario: Aceite cria dívida uma única vez
- **WHEN** o destinatário aceita um convite pendente
- **THEN** sua participação passa a `ACCEPTED` e uma dívida correspondente é criada uma vez

#### Scenario: Aceite repetido
- **WHEN** o destinatário repete uma ação de aceite ou envia duas requisições concorrentes para o mesmo convite
- **THEN** não é criada uma segunda dívida e o estado final continua coerente

#### Scenario: Recusa permite substituição
- **WHEN** o destinatário recusa antes de qualquer operação financeira
- **THEN** a participação fica `DECLINED`, não gera dívida e o criador pode substituí-la por outro usuário e ajustar cotas ainda não aceitas

#### Scenario: Pessoa não convidada tenta responder
- **WHEN** uma pessoa tenta aceitar ou recusar convite endereçado a outro usuário
- **THEN** o servidor nega a ação e não altera a participação

### Requirement: Cobrança só ativa após todos os convites atuais serem aceitos

The system SHALL manter uma cobrança com convites ativos ainda sem resposta no estado `AWAITING_ACCEPTANCE`. Enquanto estiver nesse estado, suas dívidas não participam dos totais e não podem ser pagas. A cobrança SHALL passar para `ACTIVE` somente quando todos os convites ativos forem aceitos e a soma das cotas válidas corresponder ao total.

#### Scenario: Convite pendente impede ativação
- **WHEN** pelo menos um convite ativo continua `PENDING`
- **THEN** a cobrança permanece `AWAITING_ACCEPTANCE` e suas dívidas não aparecem como valores a pagar ou a receber

#### Scenario: Último aceite ativa cobrança
- **WHEN** todos os convites ativos são aceitos e as cotas válidas somam o total da cobrança
- **THEN** a cobrança passa para `ACTIVE` e suas dívidas passam a integrar os totais

#### Scenario: Cobrança sem convidados ativos
- **WHEN** uma cobrança contém somente a participação do criador
- **THEN** ela fica `ACTIVE` sem criar dívida contra o próprio criador

### Requirement: Criador só pode ajustar cotas ainda não aceitas

The system SHALL permitir ao criador alterar sua própria cota e cotas de participações pendentes antes de qualquer pagamento registrado ou compensação aplicada. A soma SHALL permanecer igual ao total e nenhuma cota pode ser negativa. A cota de participante aceito SHALL permanecer imutável nesta mudança.

#### Scenario: Ajuste de cotas pendentes válido
- **WHEN** o criador altera cotas próprias e pendentes para valores não negativos cuja soma é o total
- **THEN** o sistema salva o novo rateio sem alterar cotas já aceitas

#### Scenario: Ajuste que não fecha o total
- **WHEN** a soma das cotas editadas é diferente do valor da cobrança ou uma cota é negativa
- **THEN** o sistema rejeita a alteração e explica como corrigir o rateio

#### Scenario: Tentativa de alterar cota aceita
- **WHEN** o criador tenta editar a cota de uma participação aceita
- **THEN** o servidor preserva a cota e informa que ela não pode ser alterada

### Requirement: Acesso e formulários de cobrança são protegidos no servidor

The system SHALL exigir autenticação para acessar cobranças e convites, autorizar cada ação pela identidade e papel da pessoa em toda requisição convencional ou HTMX, validar entradas no backend, exigir CSRF, escapar texto renderizado e limitar título, descrição e referência.

#### Scenario: Pessoa não participante consulta cobrança
- **WHEN** uma pessoa autenticada que não é criadora nem participante tenta acessar uma cobrança
- **THEN** o servidor nega acesso sem revelar detalhes privados da cobrança

#### Scenario: Formulário HTMX inválido
- **WHEN** uma requisição HTMX de cobrança contém valor ou cotas inválidos, ou token CSRF inválido
- **THEN** o servidor rejeita a alteração, não persiste dados inválidos e retorna erros acionáveis

#### Scenario: Descrição contém marcação
- **WHEN** a descrição da cobrança contém texto interpretável como marcação HTML
- **THEN** a interface o exibe escapado sem executá-lo

#### Scenario: Atualização interativa
- **WHEN** uma ação válida atualiza convite, cota ou estado da cobrança por HTMX
- **THEN** o fragmento retornado apresenta o novo estado e mantém o mesmo controle de autorização e validação da requisição convencional
