# Tasks

## 1. Modelo financeiro e rateio itemizado

- [x] 1.1 Permitir participação por conta ou por nome convidado, com entradas dinâmicas, limite default 10 e constraints de identidade; preservar participações existentes e validar a migração com `just pytest pixu/charges/test_migrations.py pixu/charges/tests.py`.
- [x] 1.2 Persistir itens vinculados a participações e calcular base, itens e cotas em centavos no serviço de domínio; cobrir resíduos, item acima do total, responsável inválido e soma exata com `just pytest pixu/charges/tests.py`.
- [x] 1.3 Aplicar recálculo durante entradas abertas, fechamento/reabertura antes de pagamento e bloqueio atômico de itens e cotas no primeiro pagamento; testar com `just pytest pixu/charges/tests.py`.

## 2. Identidade e pagamento de convidados

- [x] 2.1 Implementar credencial compartilhada e código pessoal com segredo de alta entropia armazenado como digest, TTL configurável default de sete dias, revogação/renovação e invalidação no cancelamento; testar credencial inválida, fechada, vencida e repetição de ações em `just pytest pixu/charges/tests.py`.
- [x] 2.2 Implementar entrada atômica por nome, aceitando duplicidades, criar sessão temporária fixa a uma participação e testar que username/nome de conta não vincula identidade com `just pytest pixu/charges/tests.py`.
- [x] 2.3 Adaptar dívida e pagamento para participantes sem conta sem criar usuário Pixu; permitir apenas registro de pagamento na própria dívida, conservar reserva/concorrência/confirmação manual e provar regressões das contas em `just pytest pixu/settlements/tests.py pixu/dashboard/tests.py`.
- [x] 2.4 Autorizar acesso ao comprovante convidado exclusivamente pela sessão válida da mesma participação, mantendo storage privado e autorização atual do pagador/recebedor/criador; testar troca de IDs, token revogado e arquivo inválido em `just pytest pixu/settlements/tests.py`.

## 3. Fluxo visual e documentação do produto

- [x] 3.1 Atualizar `docs/product-design.md` com a jornada de criação itemizada, participantes por conta/nome, link compartilhado, sessão restrita, expiração, estados de erro e aviso explícito de nome autodeclarado; verificar coerência lendo lado a lado o design, os specs e o protótipo HTML, e validar formatação com `git diff --check`.
- [x] 3.2 Atualizar formulários e templates Django para itens extras, responsáveis, convidados por nome, prévia do rateio e revisão acessível; manter cálculo autoritativo no servidor, erros associados aos campos, uso por POST/HTMX e testar renderização/validação em `just pytest pixu/charges/tests.py`.
- [x] 3.3 Implementar resumo com link/código e rotacionar/revogar, tela pública de entrada e tela de pagamento do convidado com sua cota, chave Pix e comprovante privado; validar autorização com a suíte pytest.

## 4. Integração

- [x] 4.1 Executar `just pytest` e corrigir regressões em cobrança, pagamentos, compensações, dashboard e contas.
- [x] 4.2 Confirmar que templates e fragmentos HTMX não dependem de Tailwind CDN e que o fluxo server-rendered funciona com conta e convidado; a verificação automatizada desta rodada permanece em `just pytest`, conforme solicitado.

## 5. Total explícito e pagamento imediato de convidados

- [x] 5.1 Persistir `guest_total_participants` com validação condicional ao modo anônimo, incluindo migração e regra de que o total não pode ser menor que as participações iniciais; manter cobranças sem convidados inalteradas.
- [x] 5.2 Calcular cotas anônimas novas sobre o total fixo, liberar confirmação/pagamento com o link aberto e preservar o fluxo de fechamento para cobranças legadas sem total; cobrir vagas não ocupadas, concorrência e saída antes da confirmação.
- [x] 5.3 Atualizar formulário, resumo, entrada e tela pessoal para explicar o total declarado e permitir pagamento imediato; testar validação server-rendered com `just pytest`.
