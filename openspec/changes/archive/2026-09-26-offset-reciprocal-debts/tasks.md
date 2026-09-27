# Tasks

## 1. Eventos e cálculo de saldo

- [x] 1.1 Criar o modelo `Compensation` com duas dívidas protegidas, iniciador, valor, data, chave idempotente única e constraints; gerar a migração e verificar `makemigrations --check` e `migrate --check` no ambiente local.
- [x] 1.2 Incluir o total compensado em `PaymentBalance` e calcular saldo aberto/disponível considerando pagamentos confirmados, compensações e reservas pendentes; cobrir os cálculos com testes de serviço para cada combinação de estados.

## 2. Elegibilidade e aplicação no domínio

- [x] 2.1 Implementar consulta de dívidas recíprocas elegíveis para o devedor, filtrando cobranças ativas, participações aceitas e disponibilidade positiva nos dois lados; testar dívidas pendentes, quitadas, reservadas e elegíveis.
- [x] 2.2 Implementar `apply_compensation` com autorização do devedor, validação de reciprocidade e valor, bloqueios ordenados de cobranças e dívidas, criação atômica do evento, bloqueio de ambas as cobranças e idempotência; testar erro sem mutações, repetição e saldo dos dois lados.
- [x] 2.3 Exercitar disputa concorrente no PostgreSQL com teste transacional para confirmar que pagamento e compensação não consomem a mesma disponibilidade nem produzem saldo negativo.

## 3. Fluxo acessível no detalhe da cobrança

- [x] 3.1 Adicionar formulário pt-BR para escolher dívida inversa e valor, prévia GET/HTMX não mutável com os dois abatimentos e Pix restante, e POST convencional/HTMX protegido por CSRF e validação do serviço; cobrir autorização, erros, prévia e redirecionamento de sucesso em testes HTTP.
- [x] 3.2 Atualizar cartões de dívida para discriminar saldo compensado, sugerir eventos elegíveis e exibir histórico sem confundir compensação com Pix; verificar navegação por teclado, textos pt-BR, ausência de overflow e alcance das ações nos breakpoints mobile e desktop.

## 4. Validação integrada e roadmap

- [x] 4.1 Adicionar teste E2E que crie pela aplicação duas cobranças aceitas em sentidos opostos, revise uma compensação parcial, confirme-a, recarregue e confira os dois saldos e o histórico nos viewports de 390×844 e 1440×900.
- [x] 4.2 Atualizar `TODO.md` para refletir os lotes já arquivados e esta mudança; validar `openspec validate offset-reciprocal-debts --strict`, suíte Django relevante, `just e2e` e `git diff --check`.
