# Design

## Context

Veja `proposal.md` para a motivação e `specs/settlements/compensations/spec.md` para o contrato observável. Hoje `Debt` está em `pixu/charges`; `Payment` e os serviços de saldo estão em `pixu/settlements`. `payment_balance` deriva valores dos eventos de pagamento, e operações financeiras bloqueiam a cobrança com `locked_at`. O detalhe da cobrança já renderiza um cartão por dívida com estado e ações HTMX.

## Goals / Non-Goals

**Goals:**

- Manter um único livro de eventos: pagamentos e compensações determinam os saldos, sem criar carteira nem valor monetário materializado.
- Serializar pagamentos e compensações concorrentes usando a mesma ordem de bloqueio: cobranças em ordem crescente de ID, depois dívidas em ordem crescente de ID.
- Fazer da revisão da prévia e do envio uma experiência acessível, traduzível e utilizável com ou sem HTMX.

**Non-Goals:**

- Não implementar histórico/extrato global, dashboard financeiro, temas visuais, compensações triangulares, compensação por mais de duas dívidas ou aprovação por uma segunda pessoa.
- Não integrar banco, Pix, notificações ou armazenamento externo novo.

## Decisions

### Persistir compensações como eventos no app `settlements`

Adicionar `Compensation` com duas FKs protegidas para `Debt`, `amount_cents`, `initiated_by`, `created_at` e uma chave UUID de idempotência única. Constraints garantem valor positivo e dívidas distintas; reciprocidade, estado e relação das pessoas são invariantes de serviço, pois dependem de linhas relacionadas. Não há estado pendente: a ação aceita pelo devedor é aplicada na mesma transação.

Alternativas consideradas: adicionar campos de saldo às dívidas ou representar uma compensação como `Payment`. Ambas foram rejeitadas. Campos acumulados duplicariam a fonte de verdade, e um pagamento falso confundiria uma compensação sem Pix com transferência confirmada.

### Derivar saldo e sugestões dos eventos existentes

Estender `PaymentBalance` com `compensated_cents`; calcular compensações em que a dívida aparece em qualquer lado e então `open = max(original - confirmed - compensated, 0)` e `available = max(open - pending, 0)`. A sugestão procura somente dívidas aceitas, de cobranças ativas e com partes invertidas, e descarta qualquer lado sem disponibilidade. A consulta inicial pode ser simples e paginada pelo par de pessoas, sem uma agregação de dashboard.

Alternativa considerada: armazenar `remaining_amount` e atualizá-lo junto aos eventos. Foi rejeitada para preservar a fórmula da fonte de verdade já definida no briefing.

### Aplicar sob bloqueios ordenados e idempotência de requisição

O serviço carrega as cobranças relacionadas, bloqueia-as em ordem crescente de PK e bloqueia as duas dívidas na mesma ordem. Sob esses bloqueios, revalida ator, estado, reciprocidade e limites derivados dos pagamentos pendentes/confirmados e compensações já gravadas. Insere um evento e define `locked_at` nas duas cobranças dentro da mesma transação. A chave UUID enviada no formulário permite que uma repetição da mesma submissão retorne o mesmo evento; reutilizá-la para conteúdo diferente é erro. A restrição única da chave cobre também colisões concorrentes.

Essa ordem acompanha pagamentos existentes, que bloqueiam primeiro cobrança e depois dívida, evitando deadlock entre fluxos financeiros. Nenhuma alteração ocorre se qualquer validação falhar.

### Integrar uma revisão independente por dívida no detalhe da cobrança

Cada cartão de dívida devida pelo usuário lista suas dívidas recíprocas elegíveis, incluindo o título da outra cobrança e seu limite disponível. Cada opção tem formulário próprio, valor inicial igual ao máximo compensável, uma prévia GET/HTMX não mutável e envio POST. A prévia calcula os dois abatimentos iguais e o Pix restante na dívida escolhida; a validação final é repetida no serviço. Sem JavaScript/HTMX, o valor inicial e o resumo permanecem visíveis e o POST convencional funciona.

Depois do sucesso, a navegação recarrega o detalhe para atualizar tanto o saldo atual quanto sugestões/históricos derivados, inclusive quando a dívida inversa pertence a outra cobrança. O histórico de cada cartão mostra o mesmo evento com referência à dívida oposta, sem classificá-lo como pagamento.

Alternativas consideradas: atualizar somente o cartão HTMX atual ou introduzir uma tela global de compensações. A primeira deixaria a dívida inversa visualmente obsoleta; a segunda criaria um módulo de histórico global fora do escopo. O recarregamento do detalhe é simples e mantém o estado financeiro coerente.

### Testar domínio, requisições e fluxo de navegador

Testes de serviço cobrem saldo, elegibilidade, autorização, validação, repetição e atomicidade. Testes transacionais com PostgreSQL exercitam o bloqueio e a disputa por disponibilidade; SQLite não é evidência suficiente para `select_for_update`. Testes HTTP cobrem CSRF/autorização, prévia HTMX e fallback convencional; um E2E cria as duas cobranças pela infraestrutura isolada e valida a jornada e o layout nos viewports mobile/desktop.

## Risks / Trade-offs

- [Históricos longos aumentam o custo das agregações por dívida] → Consultar somente o par recíproco visível, adicionar índices nas duas FKs do evento e medir antes de criar saldos materializados.
- [Fluxos simultâneos podem travar linhas em ordens diferentes] → Bloquear ambas as cobranças e dívidas sempre por PK ascendente, mantendo a ordem cobrança-antes-de-dívida já usada nos pagamentos.
- [Uma chave de idempotência reutilizada poderia encobrir uma submissão diferente] → Comparar ator, dívidas e valor do evento existente; retornar o mesmo evento apenas se todos coincidirem.
- [Um erro no saldo pode disponibilizar valor já reservado ou compensado] → Compartilhar uma única função de saldo entre UI, sugestão, formulário e serviço e testar limites com pagamentos pendentes/confirmados.

## Migration Plan

1. Criar a tabela de eventos e índices/constraints; nenhuma coluna ou dado financeiro existente será reescrito.
2. Atualizar cálculo de saldo e serviços, preservando saldos anteriores quando não houver compensações.
3. Adicionar formulários, prévia e histórico ao detalhe de cobrança; não há migração operacional nem mudança de storage externo.
4. Reverter o código e remover a tabela somente se nenhum evento tiver sido criado. Depois de compensações reais, não apagar eventos: desabilitar novas ações e preservar a trilha financeira.
