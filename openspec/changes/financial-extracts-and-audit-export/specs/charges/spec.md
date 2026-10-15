## ADDED Requirements

### Requirement: Lista de cobranças priorizada por saldo financeiro

A lista autenticada de cobranças MUST separar cobranças com dívidas ativas, aceitas e com saldo aberto positivo em **A pagar primeiro** ou **A receber primeiro**, conforme a relação financeira da pessoa autenticada. Cada grupo MUST ordenar as cobranças pela dívida aberta mais antiga, com desempate estável. Uma cobrança a receber com mais de uma dívida aberta MUST aparecer uma vez e somar os saldos dessas dívidas no valor apresentado. Cobranças visíveis sem saldo aberto elegível, incluindo cobranças aguardando aceite, quitadas ou canceladas, MUST permanecer acessíveis em **Outras cobranças**, ordenadas das mais recentes para as mais antigas. Todos os cartões MUST continuar abrindo o detalhe existente e autorizado da cobrança.

#### Scenario: Dívidas a pagar aparecem primeiro pela mais antiga

- **WHEN** a pessoa possui cobranças com dívidas ativas e saldos abertos a pagar
- **THEN** a aba **Cobranças** lista essas cobranças em **A pagar primeiro**, começando pela dívida aberta mais antiga

#### Scenario: Dívidas a receber são separadas e somadas por cobrança

- **WHEN** a pessoa credora tem mais de uma dívida aberta em uma cobrança ativa
- **THEN** a aba **Cobranças** lista a cobrança uma vez em **A receber primeiro** e apresenta a soma dos saldos abertos

#### Scenario: Histórico permanece acessível

- **WHEN** a cobrança está aguardando aceite, quitada, cancelada ou sem saldo aberto elegível para a pessoa
- **THEN** ela permanece em **Outras cobranças**, sem aparecer duplicada nos grupos prioritários
