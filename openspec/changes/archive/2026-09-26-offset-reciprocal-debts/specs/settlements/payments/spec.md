# Spec Delta

## MODIFIED Requirements

### Requirement: Saldos e concorrência

Para cada dívida, o sistema MUST manter `saldo_aberto = valor_original - pagamentos CONFIRMED - compensações aplicadas`; reservas de pagamentos `PENDING` não podem exceder o saldo aberto, e `disponível = saldo_aberto - reservas PENDING`. Persistência de pagamento, rejeição ou compensação e qualquer atualização de saldo materializado MUST ocorrer na mesma transação, com bloqueio suficiente para que operações simultâneas não produzam saldo negativo ou dupla liquidação.

#### Scenario: Duas tentativas concorrentes

- **WHEN** duas requisições tentam reservar ou confirmar a mesma parcela disponível ao mesmo tempo
- **THEN** no máximo o valor disponível é liquidado; uma requisição conclui e a outra recebe conflito ou erro de valor indisponível sem saldo negativo

#### Scenario: Histórico sobrevive à rejeição

- **WHEN** um pagamento pendente é rejeitado
- **THEN** o histórico conserva o registro como `REJECTED`, mas a fonte de saldo não o subtrai e a reserva deixa de contar

#### Scenario: Compensação reduz a disponibilidade das duas dívidas

- **WHEN** uma compensação de R$ 20,00 é aplicada entre duas dívidas com disponibilidade suficiente
- **THEN** o valor compensado é subtraído do saldo aberto de ambas e as reservas pendentes continuam discriminadas sem exceder o novo saldo
