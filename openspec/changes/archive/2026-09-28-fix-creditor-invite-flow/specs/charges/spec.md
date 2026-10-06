# Spec Delta

## ADDED Requirements

### Requirement: Convite visível quando a recebedora também participa

Ao criar uma cobrança, o sistema MUST criar uma participação `PENDING` e exibi-la na lista de convites da conta para cada pessoa ativa explicitamente selecionada como participante, mesmo quando essa mesma pessoa for também a recebedora da cobrança. O convite MUST apresentar o título da cobrança, quem a criou, quem recebe e a cota da pessoa, e MUST permitir que somente essa pessoa aceite ou recuse. Selecionar alguém somente como recebedor MUST NOT criar uma participação nem um convite: a seleção de recebedor não substitui a seleção explícita de participantes. Ao aceitar uma participação, a pessoa recebedora MUST NOT receber uma dívida contra si mesma; a cobrança MUST aguardar o aceite das demais participações pendentes antes de ativar.

#### Scenario: Recebedora selecionada também como convidada

- **WHEN** o criador escolhe a mesma conta ativa como recebedora e como participante e confirma a criação da cobrança
- **THEN** essa conta vê um convite `PENDING` em “Convites” com a cobrança, o criador, a recebedora e sua cota, podendo aceitar ou recusar

#### Scenario: Recebedora aceita sua participação

- **WHEN** a recebedora aceita o convite criado para sua própria participação
- **THEN** sua participação passa a `ACCEPTED`, nenhuma dívida é criada contra ela mesma e a cobrança só fica ativa depois que as demais participações atuais forem aceitas

#### Scenario: Recebedora não foi selecionada como participante

- **WHEN** o criador seleciona uma conta somente como recebedora, sem selecioná-la entre os participantes
- **THEN** essa conta não recebe uma participação nem um convite; somente as pessoas explicitamente selecionadas no rateio recebem convites

#### Scenario: Participantes mudam antes da atualização da prévia do rateio

- **WHEN** o criador adiciona ou remove participantes e envia a cobrança antes de a prévia HTMX atualizar as cotas para a seleção atual
- **THEN** o sistema recalcula a divisão igualitária para os participantes atuais, cria a cobrança e emite convites somente às pessoas selecionadas, sem bloquear a criação por campos de cota desatualizados
