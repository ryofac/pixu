# Proposal

## Why

O Pixu já registra pagamentos por dívida, mas pessoas com obrigações aceitas em sentidos opostos ainda não conseguem compensar parte desses valores. A compensação precisa ser uma ação explícita, auditável e atômica, sem representar transferência Pix nem crédito em carteira.

## What Changes

- Apresentar ao devedor sugestões de dívidas ativas, aceitas e recíprocas, considerando pagamentos confirmados, compensações anteriores e reservas pendentes.
- Permitir que o devedor escolha uma dívida inversa, informe um valor até o limite disponível em ambas e confirme a redução das duas dívidas.
- Persistir cada compensação como evento auditável com as duas dívidas, o valor, a pessoa iniciadora e o momento; aplicar ambas as reduções na mesma transação.
- Incorporar compensações ao cálculo de saldo aberto e disponibilidade para pagamentos, bloqueando a edição das cobranças envolvidas.
- Exibir a sugestão, a prévia do valor compensado, o Pix restante e o histórico na interface pt-BR, responsiva e aprimorada por HTMX.

## Capabilities

### New Capabilities

- `settlements/compensations`: elegibilidade, sugestão, aceite e aplicação atômica de compensações entre duas dívidas recíprocas.

### Modified Capabilities

- `settlements/payments`: refletir compensações no saldo aberto e no valor disponível para pagamento.
- `charges`: bloquear a edição de ambas as cobranças após a primeira compensação aplicada.

## Impact

- Modelos e migração em `pixu/settlements`, consultas de saldo e serviços de pagamentos/compensações.
- Views, URLs, formulários e fragmentos HTMX do detalhe de cobrança para apresentar e executar a compensação.
- Testes Django e E2E para elegibilidade, autorização, valores, atomicidade, idempotência e experiência mobile/desktop.
