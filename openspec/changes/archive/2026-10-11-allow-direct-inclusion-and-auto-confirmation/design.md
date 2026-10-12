# Design

## Context

O Pixu já representa pessoas selecionadas como participações pendentes e cria uma dívida após o aceite. Pagamentos informados por pagadores são sempre gravados como pendentes; o recebedor confirma ou rejeita dentro de uma transação que bloqueia a cobrança e a dívida. Esta mudança introduz duas autorizações independentes sem alterar o fluxo de dinheiro externo.

## Goals / Non-Goals

**Goals:**

- Persistir a preferência de inclusão direta na conta, desativada por padrão, editável somente pela titular.
- Converter em aceitas, no ato da criação da cobrança, somente as participações de contas que previamente autorizaram inclusão direta.
- Permitir ao recebedor ativar confirmação automática em uma dívida individual, deixando o comportamento manual como padrão.
- Registrar a origem de cada confirmação para que eventos manuais e automáticos sejam distinguíveis no histórico.
- Manter autorização, validação de cota, reserva, atomicidade e valores em centavos inteiros.

**Non-Goals:**

- Grupos de cobrança, convites permanentes por grupo, pagamentos bancários verificados ou execução de transferências.
- Confirmação automática para convidado sem conta Pixu, leitura/validação de comprovantes ou reversão de uma confirmação concluída.
- Alteração retroativa de participações ou pagamentos ao mudar as preferências.

## Decisions

1. **Preferência de inclusão no usuário.** Adicionar um booleano à conta Pixu, default `False`. O onboarding apenas recomenda considerar a ativação; a configuração editável fica no formulário do perfil. Não adicionar um controle ao formulário de criação de cobrança: o criador não pode consentir pela pessoa selecionada.
   - Alternativa considerada: uma tabela de preferências separada. Descartada porque há uma preferência escalar por conta, sem ciclo de vida ou relações próprias.

2. **Aceite direto no serviço de criação.** No mesmo `transaction.atomic()` que cria cobrança e participações, consultar as preferências das contas selecionadas. Persistir cada uma como `ACCEPTED` com `accepted_at`; criar a dívida, exceto quando o participante for o recebedor. Contas sem autorização continuam `PENDING`. Ativar a cobrança somente quando todos os aceites necessários e as regras atuais de cotas/total forem satisfeitos; cobranças com entradas convidadas preservam seu estado e transições atuais.
   - Alternativa considerada: criar convites pendentes e aprová-los em tarefa posterior. Descartada porque a autorização explícita já satisfaz o aceite no momento da criação e o estado intermediário abriria uma janela inconsistente.

3. **Preferência por dívida.** Adicionar `auto_confirm_payments=False` à dívida. Somente o recebedor autenticado daquela dívida pode alterá-la, enquanto a cobrança estiver ativa. A opção controla declarações futuras e não altera pagamentos existentes.
   - Alternativa considerada: confiança global entre duas contas. Descartada por ser mais ampla, difícil de compreender e incompatível com a decisão de granularidade por pagamento/dívida.

4. **Auditoria no pagamento.** Adicionar origem explícita de confirmação (`MANUAL` ou `AUTOMATIC`) no registro do pagamento. Para pagamento automático, manter `confirmed_by` nulo e gravar `confirmed_at`; confirmação manual continua registrando recebedor e data. O próprio estado confirmado e o campo de origem ficam persistidos na mesma gravação atômica.
   - Alternativa considerada: usar somente `confirmed_by=NULL` como sinal automático. Descartada porque registros legados e dados inconsistentes não teriam uma interpretação inequívoca.

5. **Bloqueio e validação do pagamento.** `record_payment` continua bloqueando cobrança e dívida, valida identidade do pagador, estado ativo, centavos positivos, comprovante e disponibilidade. Se o pagador for uma conta Pixu e a dívida estiver optada, criar o pagamento diretamente como confirmado com origem automática. O ramo de sessão convidada permanece sempre `PENDING`, pois sua identidade não é autenticada pela conta Pixu. Nenhuma integração bancária será chamada.

6. **Controle de interface no detalhe da cobrança.** Exibir a configuração em cada linha de dívida apenas na visão do recebedor e para dívidas com pagador cadastrado. O formulário usa POST/CSRF, rótulo persistente, explicação do efeito/finalidade e tamanho de toque acessível. A resposta HTMX atualiza o detalhe; POST convencional também redireciona com mensagem. No registro de pagamento, a confirmação imediata deve ter mensagem diferente de “aguardando confirmação”.

## Risks / Trade-offs

- [Uma confirmação automática pode aceitar uma declaração incorreta] → A opção começa desligada, exige ação do recebedor por dívida, informa claramente o efeito, só se aplica a pagamentos futuros e deixa origem/data auditáveis; não se afirma verificação bancária.
- [Uma mudança de preferência pode causar corrida com uma nova cobrança] → A autorização é consultada durante a criação atômica, e o valor capturado no estado da participação torna o resultado estável para aquela cobrança.
- [A UI pode sugerir que o Pixu observou o dinheiro] → Usar sempre “pagamento declarado” e explicitar que transferência e conferência ocorrem fora do Pixu.
- [Registros antigos podem não ter origem] → A migração define `MANUAL` para dados existentes, preservando compatibilidade histórica.

## Migration Plan

1. Migrar novas preferências de conta e dívida com valor falso; classificar pagamentos históricos como confirmação manual.
2. Publicar serviços e controles protegidos por autenticação e autorização existentes.
3. Se for necessário rollback de código, manter as colunas e dados: desabilitar o fluxo automático por código antes de uma migração destrutiva. Não reverter nem reinterpretar pagamentos já confirmados.

## Open Questions

Nenhuma.
