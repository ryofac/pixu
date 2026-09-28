# Proposal

## Why

Foi relatado que uma pessoa selecionada tanto como recebedora da cobrança quanto como convidada não viu o convite pendente. O código separa os papéis de recebedor e participante; precisamos reproduzir a jornada completa e fechar uma regressão que garanta que a participação escolhida chegue à caixa de convites.

## What Changes

- Reproduzir a criação pelo formulário quando a mesma conta é escolhida em “Quem recebe” e em “Convidar pessoas cadastradas”, acompanhando o POST até a lista de convites dessa conta.
- Garantir que a seleção explícita como participante gere uma participação `PENDING` visível à pessoa convidada, mesmo quando ela também é a recebedora.
- Preservar a regra de que a recebedora não deve a si mesma e que escolher alguém apenas como recebedor não cria um convite nem uma participação para essa pessoa.
- Cobrir a jornada com testes de view e E2E; não introduzir envio de convites por e-mail ou link externo.

## Capabilities

### New Capabilities

### Modified Capabilities

- `charges`: especificar a visibilidade do convite quando recebedor e participante são a mesma pessoa, preservando a independência entre essas seleções.

## Impact

Afeta o fluxo de criação e consulta de convites em `pixu/charges/` e os testes associados, incluindo a jornada E2E. A inspeção inicial encontrou criação de participações `PENDING` a partir da lista explícita de convidados e consulta de convites por usuário nesse estado; a causa da ocorrência relatada ainda precisa ser isolada pela reprodução. Nenhuma alteração de modelo, dependência, e-mail ou protocolo externo é prevista.
