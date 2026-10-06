# Spec Delta

## Purpose

Permite que pessoas sem conta Pixu entrem dinamicamente em uma cobrança identificada por nome e acessem somente sua cota por um link compartilhado, sem obter identidade ou acesso global no produto.

## ADDED Requirements

### Requirement: Cota com total fixo para pagamento imediato

Ao habilitar convidados anônimos, a cobrança MUST guardar o total explícito de participantes informado pelo criador. Esse total MUST incluir participações de contas e vagas anônimas, ser maior ou igual ao conjunto inicial e servir como denominador estável da base comum. A tela do convidado MUST exibir que a cota foi calculada sobre esse total.

Uma participação convidada com total fixo MUST poder ser confirmada e pagar enquanto as entradas continuam abertas. A abertura do link não pode bloquear a ativação da cobrança quando existir ao menos uma participação aceita; convites registrados ainda pendentes não bloqueiam a dívida da pessoa anônima. Vagas declaradas mas ainda não ocupadas não criam dívidas e não podem alterar a cota já confirmada. O fluxo de cobranças sem total fixo (dados legados) mantém a exigência de fechamento antes da confirmação.

#### Scenario: Cota é calculada sobre o total informado

- **WHEN** uma cobrança de R$ 400,00 declara quatro pessoas e somente duas entram inicialmente
- **THEN** cada participação recebe a parcela da base de quatro pessoas, enquanto as duas vagas restantes ficam reservadas sem dívida

#### Scenario: Pagamento imediato com link aberto

- **WHEN** o convidado confirma sua cota fixa antes de o criador fechar as entradas
- **THEN** a cobrança fica apta a registrar o pagamento da dívida daquele convidado, mantendo o link aberto para as vagas restantes

### Requirement: Link compartilhado e temporário da cobrança

Depois de criar uma cobrança com entradas anônimas habilitadas, o criador MUST poder copiar um link compartilhado com token aleatório forte. O token MUST ser imprevisível, limitado à cobrança correspondente e revogável/renovável pelo criador; o link compartilhado MUST permanecer válido somente enquanto as entradas estiverem abertas e MUST ser invalidado no cancelamento. Um identificador público da cobrança, isoladamente, MUST NOT autorizar entrada, visualização de cota ou registro de pagamento.

#### Scenario: Criador compartilha o convite

- **WHEN** o criador abre o resumo após criar uma cobrança com convidados
- **THEN** a interface oferece o link e o código da mesma cobrança e explica que qualquer pessoa com a credencial poderá entrar com um nome enquanto houver vagas

#### Scenario: Código público não concede acesso

- **WHEN** uma pessoa tenta acessar dados de convidado usando somente um identificador público da cobrança, sem a credencial secreta
- **THEN** o servidor não revela cotas nem permite entrada ou registro de pagamento

#### Scenario: Credencial expira, é revogada ou a cobrança é cancelada

- **WHEN** uma pessoa usa um link vencido, revogado, renovado ou referente a uma cobrança cancelada
- **THEN** o servidor nega o acesso de convidado e não revela dados da cota ou comprovantes

### Requirement: Entrada e código pessoal

Uma pessoa sem conta MUST poder informar um nome autodeclarado e criar uma nova participação usando o link compartilhado válido. O nome MUST NOT funcionar como prova de identidade ou localizar uma conta Pixu, e MUST NOT conceder acesso a qualquer outra participação. A entrada MUST retornar um código pessoal e uma sessão restrita à participação criada. Nomes repetidos MUST ser aceitos; cada participação MUST ter credencial pessoal distinta. O código pessoal MUST permanecer válido até a quitação da dívida ou até a expiração configurável (default de sete dias, contada da entrada e estendida para sete dias após o fechamento quando necessário), o que ocorrer primeiro.

#### Scenario: Convidado entra com seu nome

- **WHEN** uma pessoa apresenta a credencial da cobrança e confirma um nome
- **THEN** o sistema cria uma participação, recalcula a cobrança e abre uma sessão temporária limitada àquela cota

#### Scenario: Nome não cria ou autentica conta Pixu

- **WHEN** o nome informado coincide com username, nome de exibição ou e-mail de uma conta existente
- **THEN** o sistema trata a entrada como participação convidada da cobrança e não autentica, altera nem vincula a conta existente

#### Scenario: Link fechado ou nome inválido

- **WHEN** uma pessoa tenta entrar sem link válido ou depois do fechamento
- **THEN** o servidor nega a entrada, não cria participação nem revela cotas de outras pessoas

#### Scenario: Conta Pixu integra a cobrança pelo login

- **WHEN** uma pessoa escolhe entrar em sua conta Pixu pelo fluxo do convite e existe uma participação registrada para essa conta
- **THEN** a participação só é exibida ou aceita depois da autenticação dessa conta, e passa a integrar seu dashboard pelas regras normais de aceite

### Requirement: Acesso de convidado restrito à própria cota

Uma sessão convidada válida MUST mostrar somente o título e o total da cobrança, o nome do recebedor, a chave Pix informada pelo recebedor e a cota criada para aquela entrada, incluindo sua base comum e itens atribuídos. A sessão MUST NOT mostrar dashboard, chaves de outras pessoas, outras cotas, dívidas recíprocas, comprovantes de terceiros ou ações de criador, participante cadastrado ou recebedor. A interface MUST informar que o nome é autodeclarado e que o acesso temporário depende de quem possui o link e o código pessoal.

#### Scenario: Convidado visualiza apenas sua cota

- **WHEN** o convidado abre a cobrança por sua sessão válida
- **THEN** vê sua cota discriminada e as informações necessárias para pagar ao recebedor, sem dados de outras participações

#### Scenario: Convidado tenta acessar outra cota ou cobrança

- **WHEN** o convidado altera identificadores na URL ou envia requisição para outra participação ou cobrança
- **THEN** o servidor nega o acesso sem retornar dados de terceiros

#### Scenario: Convidado tenta administrar ou decidir pagamentos

- **WHEN** o convidado tenta editar a cobrança, aceitar outra participação ou confirmar/rejeitar um pagamento
- **THEN** o servidor recusa a ação e preserva cobrança, pagamentos e saldos
