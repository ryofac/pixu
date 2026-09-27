# Spec Delta

## ADDED Requirements

### Requirement: Bloqueio de edição após compensação

Ao aplicar uma compensação, o sistema MUST bloquear definitivamente a edição estrutural das duas cobranças envolvidas, incluindo total, participantes, cotas e recebedor, mantendo o histórico e os valores das dívidas coerentes.

#### Scenario: Compensação bloqueia as duas cobranças

- **WHEN** uma compensação é aplicada entre dívidas de cobranças distintas
- **THEN** ambas as cobranças ficam bloqueadas para edição e tentativas posteriores são recusadas pelo servidor sem alterar dados

#### Scenario: Repetição não altera o bloqueio

- **WHEN** o pedido de compensação já aplicado é reenviado
- **THEN** nenhuma cobrança é alterada novamente e o bloqueio permanece associado às duas operações financeiras registradas
