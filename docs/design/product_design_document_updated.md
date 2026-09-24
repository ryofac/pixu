# Pixu: Product Design & UX Decisions

**Estado:** Documento de Design e Jornadas
**Contexto:** MVP de rateio e acompanhamento de dívidas (OpenSpec)

Este documento mapeia as jornadas dos usuários, descreve os estados das telas e registra as decisões de design de experiência (UX) vinculadas às regras de negócio (R01-R16) da especificação.

---

## 1. Mapeamento de Jornadas

### Jornada do Criador (ex: Ryan)
1. **Autenticação (R01):** Acessa o app e visualiza o *Dashboard*.
2. **Criação da Cobrança (R04, R05):** Inicia "Nova Cobrança", insere título ("Churrasco"), valor total e adiciona participantes (Ana e Bruno). O sistema pré-calcula a divisão igualitária.
3. **Ajuste e Confirmação (R06):** Edita cotas se necessário (não aplicável no fluxo padrão) e salva. O sistema gera a cobrança e bloqueia a edição após a primeira movimentação financeira (R07).
4. **Acompanhamento (R15):** Visualiza a tela de *Detalhe da Cobrança*. Aguarda os aceites e pagamentos.
5. **Auditoria e Confirmação (R09, R10):** Recebe notificação/visualiza no dashboard que Ana registrou um Pix. Verifica na sua conta bancária real e clica em "Confirmar recebimento".
6. **Quitação:** Visualiza a dívida de Ana como liquidada (R14).

### Jornada do Participante/Pagador (ex: Ana)
1. **Autenticação (R01):** Acessa o app.
2. **Revisão e Aceite (R02):** Visualiza notificação no *Dashboard* sobre a nova cobrança de Ryan. Acessa os detalhes e clica em "Aceitar Participação", gerando a dívida oficial.
3. **Análise de Opções (R11):** Acessa *Minhas Dívidas*. O sistema acusa que ela deve R$ 50 para Ryan, mas possui um crédito potencial (Ryan deve R$ 30 a ela).
4. **Compensação (R12, R13):** Clica no card de sugestão de compensação. Revisa a operação e confirma. Sua dívida cai instantaneamente para R$ 20.
5. **Pagamento (R03, R08):** Clica em "Pagar Pix". Copia a chave Pix de Ryan, realiza o pagamento no app do seu banco e, de volta ao Pixu, confirma o valor enviado. O status vai para `Pendente`.
6. **Quitação:** Aguarda Ryan confirmar. Após confirmação, a dívida desaparece da aba de ativas.

---

## 2. Diretivas de Experiência e UI/UX (Aesthetic Sakura)

A interface do Pixu é projetada rigorosamente com a abordagem **Mobile-First**, garantindo que as jornadas financeiras sejam resolvidas com o polegar de forma rápida e fluida.

### Identidade Visual e Paleta "Sakura Blossom"
O nome "PiXu" atua como um trocadilho lúdico e nipônico. A interface funde o utilitarismo financeiro do Pix com a estética japonesa da flor de cerejeira (Sakura).

*   **Main Brand (Crimson):** `#EC275F` (Usado para botões primários, ícones ativos e destaque do "X" na logo).
*   **Gradient/Accent (Dark Pink):** `#F25477` (Usado para hover de botões e transições).
*   **Highlights (Salmon):** `#FFA7A6` (Usado para badges, links textuais e destaques secundários).
*   **Subtle Elements (Blue):** `#D4E0EE` (Usado para backgrounds de avatares, cards inativos e o frame da logo).
*   **Light Mode Background:** `#FFF4F3` (Um tom extremamente suave e quente para substituir o branco puro).

### Comportamentos de Interface (Dark/Light Mode)
*   A aplicação suporta nativamente temas **Claro** e **Escuro**. 
*   No modo escuro, o fundo principal muda para `#121212` e as superfícies (cards) assumem a cor `#1E1A1D` (um tom cinza/marrom bem escuro, mantendo a temperatura da paleta Sakura). 
*   O contraste das tipografias inverte para `#FFF4F3`, garantindo legibilidade.

### Princípios Específicos das Regras OpenSpec
*   **Distinção Visual de Saldos (R08, R14):** O sistema *nunca* subtrai um "Pix Pendente" do "Saldo em Aberto" visualmente. O valor pendente é mostrado como um balão de reserva (ex: `Saldo: R$ 50 (R$ 20 em análise)`).
*   **Compensação Proativa (R11, R12):** A ação de abater dívidas não é automática. O "Smart Banner" sugere a ação no detalhe da dívida, permitindo ao usuário simular a compensação e ver o *De -> Para* dos saldos.
*   **Prevenção de Duplicidade (R09):** Ao registrar um pagamento, o botão primário muda imediatamente de estado, indicando "Aguardando Confirmação" e bloqueando envios duplicados em tela.