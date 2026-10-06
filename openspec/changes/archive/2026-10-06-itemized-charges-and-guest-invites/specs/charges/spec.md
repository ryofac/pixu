# Spec Delta

## ADDED Requirements

### Requirement: Rateio de itens individuais

 Ao criar uma cobrança, o criador MUST poder registrar zero ou mais itens individuais com descrição, valor positivo em centavos e uma pessoa participante como responsável. O valor total dos itens MUST ser menor ou igual ao total da cobrança. O restante MUST formar a base comum, dividida igualmente entre todas as participações incluídas ou, no modo anônimo com total declarado, entre o total fixo de pessoas informado pelo criador; cada cota MUST somar sua parcela da base e os itens atribuídos àquela pessoa. O cálculo MUST usar centavos inteiros, distribuir resíduos de forma determinística e manter a soma das cotas persistidas e das vagas futuras exatamente igual ao total. O servidor MUST recalcular e validar os itens e as cotas em submissões convencionais e HTMX.

#### Scenario: Itens extras são somados à base comum

- **WHEN** Ryan cria uma cobrança de R$ 470,00 para quatro pessoas, atribuindo itens de R$ 50,00 a Meireles e R$ 20,00 a Roberto
- **THEN** o sistema divide a base de R$ 400,00 em quatro cotas e apresenta R$ 100,00 para Ryan e Ruan, R$ 150,00 para Meireles e R$ 120,00 para Roberto

#### Scenario: Resíduo da base comum é determinístico

- **WHEN** a base comum de R$ 100,00 é dividida entre três participações
- **THEN** as cotas da base são R$ 33,34, R$ 33,33 e R$ 33,33 em uma ordem estável, e somam exatamente R$ 100,00

#### Scenario: Itens excedem o total

- **WHEN** o criador envia itens cuja soma excede o total da cobrança
- **THEN** o servidor rejeita a cobrança com erro localizado, sem persistir cobrança, itens ou participações

#### Scenario: Item aponta para pessoa fora do rateio

- **WHEN** o criador atribui um item a uma pessoa não incluída entre as participações
- **THEN** o servidor rejeita a submissão e não cria a cobrança

### Requirement: Entrada convidada identificada por nome

O criador MUST poder habilitar entradas anônimas na criação, com limite configurável e default 10, inclusive quando ainda não houver participantes além dele (ou quando optar por não participar). Enquanto as entradas estiverem abertas, cada envio de nome MUST criar uma nova participação convidada na cobrança, sem tratar o nome como username global nem associá-lo automaticamente a uma conta Pixu existente. Nomes podem se repetir na mesma cobrança; cada entrada é diferenciada por uma credencial pessoal. Participações convidadas MUST integrar o cálculo e a soma das cotas como as demais participações, mas MUST NOT criar acesso a dashboard ou a outras cobranças.

#### Scenario: Convidado sem conta participa da cobrança

- **WHEN** uma pessoa acessa o link aberto e confirma o nome “Meireles”
- **THEN** o sistema cria uma participação convidada com nome e cota recalculada, sem exigir e-mail, senha ou username Pixu

#### Scenario: Nome de convidado coincide com username existente

- **WHEN** o criador adiciona um convidado cujo nome coincide com o username de uma conta Pixu
- **THEN** o sistema mantém a participação como convidada, sem conflito de username, associação automática ou acesso à conta existente

#### Scenario: Nomes iguais têm identidades diferentes

- **WHEN** duas pessoas entram com o mesmo nome na mesma cobrança
- **THEN** o sistema cria duas participações independentes com códigos pessoais diferentes

### Requirement: Total explícito no modo anônimo

Quando o criador habilitar entradas anônimas, ele MUST informar explicitamente o total de pessoas que participarão da conta. O total MUST incluir as contas já selecionadas, o criador quando incluído e as vagas que ainda serão ocupadas por pessoas anônimas; MUST ser positivo, limitado a 100 pessoas e não pode ser menor que as participações já selecionadas. O campo e sua validação MUST existir somente para o modo anônimo; cobranças sem entradas anônimas não podem exigir esse valor nem alterar seu fluxo.

O total declarado MUST fixar o denominador da base comum desde a criação. Uma entrada anônima confirmada MUST poder gerar dívida e registrar pagamento enquanto o link compartilhado ainda estiver aberto, sem aguardar o fechamento das entradas. Vagas anônimas ainda não ocupadas não geram dívida, mas preservam a cota reservada no rateio.

#### Scenario: Modo anônimo exige total explícito

- **WHEN** o criador marca entradas anônimas sem informar quantas pessoas participarão
- **THEN** o servidor rejeita a criação com erro no campo do total, sem criar a cobrança

#### Scenario: Total inclui contas selecionadas e vagas anônimas

- **WHEN** o criador participa e convida uma conta, informa total 4 e habilita entradas anônimas
- **THEN** as duas participações atuais recebem suas cotas sobre quatro pessoas e o link pode receber somente as vagas restantes dentro do limite configurado

#### Scenario: Convidado paga antes do fechamento

- **WHEN** uma pessoa entra em uma cobrança com total fixo, confirma a cota e o link ainda está aberto
- **THEN** o sistema libera a dívida para pagamento imediato, sem exigir que o criador feche as entradas

### Requirement: Fechamento e recálculo de entradas

Enquanto as entradas estiverem abertas, cada entrada ou saída MUST recalcular a base comum e as cotas em centavos, mantendo a soma igual ao total. O criador MUST poder fechar as entradas explicitamente; depois do fechamento novos nomes MUST ser recusados e somente identidades já criadas poderão confirmar sua cota. Antes de qualquer pagamento, o criador MUST poder reabrir as entradas para corrigir participantes ou itens e recalcular as cotas.

#### Scenario: Cobrança nasce sem participantes convidados

- **WHEN** o criador habilita entradas anônimas e salva uma cobrança sem nenhuma entrada
- **THEN** a cobrança permanece aguardando entradas, sem permitir pagamento ou fechamento com zero participantes

#### Scenario: Nova entrada recalcula a base

- **WHEN** o total fixo de R$ 470,00 recebe uma nova entrada
- **THEN** a nova participação recebe a parcela da base correspondente ao total declarado, sem alterar as cotas já confirmadas, e a soma das cotas atuais mais as vagas reservadas permanece R$ 470,00

#### Scenario: Fechamento bloqueia novas entradas

- **WHEN** o criador fecha as entradas
- **THEN** o link compartilhado deixa de aceitar novos nomes e os códigos pessoais existentes continuam válidos para confirmação e pagamento

#### Scenario: Reabertura antes do pagamento

- **WHEN** uma pessoa não confirma sua cota e ainda não existe pagamento
- **THEN** o criador pode reabrir e ajustar o conjunto de entradas antes de fechar novamente

### Requirement: Edição de cobrança itemizada antes do pagamento

Em uma cobrança itemizada, enquanto não houver operação financeira, o criador MUST poder revisar os participantes, responsáveis pelos itens, valores dos itens e total pelas regras existentes de edição. A prévia e a cobrança persistida MUST recalcular em conjunto base, itens e cotas. Depois do primeiro pagamento, o sistema MUST manter imutáveis os itens, responsáveis e cotas itemizadas; correções posteriores exigem uma nova cobrança.

#### Scenario: Criador revisa cobrança ainda sem aceite

- **WHEN** o criador altera um item ou participante antes de qualquer aceite ou operação financeira
- **THEN** o sistema recalcula base e cotas, preserva a soma igual ao total e salva a revisão atomicamente

#### Scenario: Aceite protege itens e cotas

- **WHEN** existe um pagamento registrado para qualquer participação
- **THEN** o servidor recusa alterações posteriores dos itens, responsáveis e cotas sem mudar o histórico da cobrança
