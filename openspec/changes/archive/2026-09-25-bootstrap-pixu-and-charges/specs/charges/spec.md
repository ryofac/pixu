## Purpose

Esta capacidade permite criar cobranças compartilhadas e converter convites aceitos em dívidas com cotas inteiras em centavos, mantendo a cobrança inativa enquanto faltarem respostas.

## ADDED Requirements

### Requirement: Criador pode criar cobrança com rateio exato

The system SHALL permitir a uma pessoa autenticada criar uma cobrança com título, descrição opcional, valor positivo em centavos e usuários já cadastrados. O recebedor único SHALL ser selecionável entre contas ativas, inicialmente o criador. A participação do criador SHALL ser opcional e marcada por padrão; desmarcá-la não transfere autoria nem permissão de edição. Uma pessoa não pode aparecer mais de uma vez na mesma cobrança e o rateio SHALL conter ao menos uma pessoa.

#### Scenario: Prévia e criação de cobrança
- **WHEN** o criador informa dados válidos e seleciona participantes existentes
- **THEN** o sistema mostra a cobrança e as cotas antes de salvá-la e cria os convites correspondentes após a confirmação

#### Scenario: Divisão com centavos residuais
- **WHEN** o valor não pode ser dividido igualmente em centavos inteiros
- **THEN** o sistema distribui os centavos residuais por uma ordem determinística dos participantes, e a soma das cotas permanece igual ao total

#### Scenario: Recebedor não deve a si mesmo
- **WHEN** uma participação do recebedor é aceita
- **THEN** a cota é incluída no rateio e nenhuma dívida é criada contra ele mesmo

#### Scenario: Criador fora do rateio
- **WHEN** o criador desmarca sua participação e seleciona outras pessoas
- **THEN** somente as pessoas selecionadas dividem o total e o criador mantém autoria e acesso à cobrança

#### Scenario: Criador participante com outro recebedor
- **WHEN** o criador participa e escolhe outra conta ativa como recebedor
- **THEN** sua cota é aceita na criação e gera uma dívida própria para o recebedor escolhido; os demais convites continuam pendentes

#### Scenario: Cotas manuais na criação
- **WHEN** o criador ajusta as cotas na prévia para valores não negativos cuja soma fecha o total
- **THEN** esses valores são persistidos sem recalcular o rateio igualitário

#### Scenario: Prévia sem JavaScript
- **WHEN** o criador solicita conferir cotas por POST convencional
- **THEN** o sistema apresenta campos editáveis e não persiste cobrança até a confirmação

#### Scenario: Cotas ou recebedor inválidos
- **WHEN** cotas manuais não fecham o total, faltam participantes ou o recebedor não é uma conta ativa cadastrada
- **THEN** o sistema preserva as entradas, mostra erros e não cria cobrança, participações nem dívidas

#### Scenario: Dados inválidos ou participante repetido
- **WHEN** o criador informa valor não positivo, título inválido, usuário inexistente ou participante duplicado
- **THEN** a cobrança não é criada e o formulário mostra o erro correspondente

### Requirement: Participantes podem aceitar ou recusar convite

The system SHALL apresentar convites recebidos como `PENDING`, incluindo o recebedor e a cota, e permitir que somente o destinatário do convite os aceite ou recuse. Um aceite SHALL criar uma única dívida ligada à participação para o recebedor selecionado, exceto quando o participante é o próprio recebedor; convite recusado não cria dívida.

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

#### Scenario: Convite aberto antes de alteração dos termos
- **WHEN** o destinatário tenta aceitar uma cota ou recebedor diferente do que foi exibido em seu convite
- **THEN** o servidor preserva o convite pendente, exibe os termos atuais e pede nova conferência, sem criar dívida

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
- **THEN** ela fica `ACTIVE` e só cria dívida se o recebedor for outra pessoa

### Requirement: Criador só pode ajustar cotas ainda não aceitas

The system SHALL permitir ao criador alterar sua própria cota e cotas de participações pendentes antes de qualquer pagamento registrado ou compensação aplicada. A soma SHALL permanecer igual ao total e nenhuma cota pode ser negativa. A cota de outra pessoa que aceitou SHALL permanecer imutável nesta mudança. A dívida do próprio criador, quando existente, SHALL acompanhar ajustes permitidos na mesma transação.

#### Scenario: Ajuste de cotas pendentes válido
- **WHEN** o criador altera cotas próprias e pendentes para valores não negativos cuja soma é o total
- **THEN** o sistema salva o novo rateio sem alterar cotas já aceitas

#### Scenario: Ajuste que não fecha o total
- **WHEN** a soma das cotas editadas é diferente do valor da cobrança ou uma cota é negativa
- **THEN** o sistema rejeita a alteração e explica como corrigir o rateio

#### Scenario: Tentativa de alterar cota aceita
- **WHEN** o criador tenta editar a cota de uma participação aceita
- **THEN** o servidor preserva a cota e informa que ela não pode ser alterada

### Requirement: Recebedor pode ser alterado antes dos aceites

The system SHALL permitir ao criador trocar o recebedor por outra conta ativa somente antes do aceite de qualquer outra pessoa e antes de operação financeira. A troca SHALL ser atômica com os ajustes de cota e dívida própria, usando o mesmo bloqueio da cobrança que os aceites.

#### Scenario: Troca antes dos aceites
- **WHEN** o criador escolhe outro recebedor sem aceites de outras pessoas nem operação financeira
- **THEN** a cobrança e eventual dívida do criador passam a apontar ao novo recebedor, sem gerar dívida contra si mesmo

#### Scenario: Troca depois de aceite ou bloqueio
- **WHEN** o criador tenta trocar o recebedor depois do aceite de outra pessoa ou de operação financeira
- **THEN** o servidor rejeita a troca sem alterar o recebedor, as cotas ou as dívidas

#### Scenario: Aceite simultâneo com troca de recebedor
- **WHEN** aceite e troca de recebedor são enviados concorrentemente
- **THEN** as operações são serializadas e nenhuma dívida aceita permanece apontando a um recebedor diferente da cobrança

### Requirement: Acesso e formulários de cobrança são protegidos no servidor

The system SHALL exigir autenticação para acessar cobranças e convites, autorizar cada ação pela identidade e papel da pessoa em toda requisição convencional ou HTMX, validar entradas no backend, exigir CSRF, escapar texto renderizado e limitar título, descrição e referência.

#### Scenario: Recebedor fora do rateio consulta cobrança
- **WHEN** o recebedor selecionado não é criador nem participante e abre a cobrança
- **THEN** o servidor permite leitura, mas recusa edição de cotas, troca de recebedor e substituição de convidados

#### Scenario: Pessoa não participante consulta cobrança
- **WHEN** uma pessoa autenticada que não é criadora, recebedora nem participante tenta acessar uma cobrança
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
