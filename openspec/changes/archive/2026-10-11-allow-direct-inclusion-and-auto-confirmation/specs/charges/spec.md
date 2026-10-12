# Spec Delta

## MODIFIED Requirements

### Requirement: Convite visível quando a recebedora também participa

Ao criar uma cobrança, o sistema MUST criar uma participação `PENDING` e exibi-la na lista de convites para cada pessoa ativa explicitamente selecionada como participante cuja preferência de inclusão direta esteja desativada, inclusive quando essa mesma pessoa for também a recebedora da cobrança. O convite MUST apresentar o título da cobrança, quem a criou, quem recebe e a cota da pessoa, e MUST permitir que somente essa pessoa aceite ou recuse. Para cada conta selecionada cuja titular ativou a preferência de inclusão direta, o sistema MUST criar a participação como `ACCEPTED`, sem convite nem aceite individual, usando a cota calculada pelas regras existentes e criando uma dívida somente quando a pessoa for diferente do recebedor. Selecionar alguém somente como recebedor MUST NOT criar uma participação nem um convite: a seleção de recebedor não substitui a seleção explícita de participantes. A cobrança MUST permanecer aguardando aceite enquanto existir qualquer convite pendente; quando todas as participações atuais estiverem aceitas e as regras de total e cotas forem satisfeitas, MUST tornar-se ativa.

#### Scenario: Recebedora selecionada também como convidada

- **WHEN** o criador escolhe uma conta ativa sem inclusão direta como recebedora e participante e confirma a cobrança
- **THEN** essa conta vê um convite `PENDING` em “Convites” com cobrança, criador, recebedora e cota, podendo aceitar ou recusar

#### Scenario: Participante com preferência ativada entra diretamente

- **WHEN** o criador seleciona uma conta ativa cuja titular ativou inclusão direta e confirma a cobrança
- **THEN** a participação é criada como `ACCEPTED`, não aparece como convite pendente e sua dívida é criada conforme as regras existentes se o recebedor for outra pessoa

#### Scenario: Recebedora aceita sua participação

- **WHEN** a recebedora aceita um convite pendente criado para sua própria participação
- **THEN** sua participação passa a `ACCEPTED`, nenhuma dívida é criada contra ela mesma e a cobrança só fica ativa depois que as demais participações pendentes forem aceitas

#### Scenario: Recebedora com inclusão direta não recebe dívida contra si

- **WHEN** o criador seleciona como participante uma conta que também é recebedora e cuja titular autorizou inclusão direta
- **THEN** sua participação é criada como aceita sem convite e nenhuma dívida é criada contra ela mesma

#### Scenario: Preferência desativada após participação direta

- **WHEN** uma pessoa desativa inclusão direta depois de ter sido incluída e aceita em uma cobrança existente
- **THEN** sua participação continua aceita e a dívida existente não é revertida

#### Scenario: Recebedora não foi selecionada como participante

- **WHEN** o criador seleciona uma conta somente como recebedora, sem selecioná-la entre os participantes
- **THEN** essa conta não recebe uma participação nem um convite; somente as pessoas explicitamente selecionadas no rateio recebem participação

#### Scenario: Participantes mudam antes da atualização da prévia do rateio

- **WHEN** o criador adiciona ou remove participantes e envia a cobrança antes de a prévia HTMX atualizar as cotas para a seleção atual
- **THEN** o sistema recalcula a divisão igualitária para as contas atualmente selecionadas, cria participações aceitas ou convites conforme a preferência própria de cada conta e não bloqueia a criação por campos de cota desatualizados
