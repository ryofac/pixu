# Spec Delta

## Purpose

Permite que uma pessoa reduza obrigações aceitas em sentidos opostos por uma compensação explícita, auditável e aplicada às duas dívidas sem movimentar dinheiro.

## ADDED Requirements

### Requirement: Sugestão de dívidas recíprocas disponíveis

O sistema MUST sugerir ao devedor de uma dívida ativa outras dívidas ativas, aceitas e opostas entre as mesmas duas pessoas. A disponibilidade de cada lado MUST considerar pagamentos confirmados, compensações aplicadas e pagamentos pendentes reservados. A sugestão MUST mostrar a dívida inversa e o limite compensável, sem reservar ou alterar qualquer valor.

#### Scenario: Dívida inversa elegível é sugerida

- **WHEN** a pessoa deve R$ 50,00 a Ryan e Ryan deve R$ 30,00 a ela em dívidas ativas e aceitas, sem reservas pendentes
- **THEN** o sistema sugere a dívida inversa com limite de R$ 30,00 e mantém ambos os saldos inalterados até a pessoa confirmar uma compensação

#### Scenario: Reserva pendente reduz o limite sugerido

- **WHEN** uma dívida inversa de R$ 30,00 possui R$ 10,00 reservados por pagamento pendente
- **THEN** a sugestão considera somente R$ 20,00 disponíveis naquela dívida

#### Scenario: Dívida sem disponibilidade não é elegível

- **WHEN** uma dívida inversa pertence a cobrança ainda não ativa, participação não aceita, está quitada ou tem toda sua disponibilidade reservada
- **THEN** ela não é oferecida como opção de compensação

### Requirement: Aceite e aplicação atômica

Somente o devedor da dívida escolhida MUST poder iniciar a compensação com uma dívida inversa distinta, ativa, aceita e pertencente ao mesmo par de pessoas em sentido oposto. O valor MUST ser um inteiro positivo em centavos e não pode exceder a menor disponibilidade das duas dívidas. Ao aceitar, o sistema MUST registrar um evento com ambas as dívidas, o valor, a pessoa iniciadora e o momento, e reduzir ambas pelo mesmo valor atomicamente. A ação não representa Pix, carteira ou crédito independente.

#### Scenario: Devedor aceita uma compensação parcial

- **WHEN** Ana deve R$ 50,00 a Ryan, Ryan deve R$ 30,00 a Ana e Ana aceita compensar R$ 20,00
- **THEN** o histórico registra uma compensação iniciada por Ana e os saldos abertos das duas dívidas são reduzidos em R$ 20,00 cada

#### Scenario: Valor inválido ou acima da disponibilidade

- **WHEN** a pessoa informa zero, valor negativo ou valor maior que o limite de qualquer dívida
- **THEN** o servidor recusa a operação e não cria evento nem altera qualquer saldo

#### Scenario: Disponibilidade muda antes da confirmação

- **WHEN** um pagamento pendente ou outra compensação consome a disponibilidade depois que o formulário foi exibido
- **THEN** o servidor recalcula os dois limites sob bloqueio e recusa um valor que não cabe mais, sem alterar as dívidas

#### Scenario: Dívidas não são recíprocas ou estão inativas

- **WHEN** a requisição aponta para a própria dívida, para dívidas de outro par ou para cobrança que não esteja ativa
- **THEN** o servidor recusa a operação e não cria evento

### Requirement: Autorização e idempotência da compensação

Toda aplicação MUST exigir uma pessoa autenticada que seja devedora da dívida escolhida e validar novamente titularidade, estado e disponibilidade no servidor, inclusive em requisições HTMX. Uma repetição da mesma submissão MUST retornar o evento já aplicado ou recusá-la sem duplicar a redução. Terceiros e recebedores que não sejam o devedor escolhido MUST ser recusados.

#### Scenario: Terceiro tenta aceitar compensação

- **WHEN** uma pessoa que não deve a dívida escolhida envia a requisição convencional ou HTMX
- **THEN** o servidor responde acesso negado e mantém ambas as dívidas e o histórico inalterados

#### Scenario: Submissão repetida

- **WHEN** o mesmo pedido de compensação é reenviado após uma resposta perdida
- **THEN** o sistema não cria uma segunda compensação nem reduz os saldos novamente

### Requirement: Exibição e revisão da compensação

A tela da dívida MUST apresentar a opção elegível com identificação da dívida inversa, permitir informar valor até o limite disponível e mostrar antes do aceite quanto será abatido de cada dívida e quanto restará disponível para Pix na dívida escolhida. Após aplicar, o detalhe MUST exibir o valor compensado no saldo e o evento no histórico. Os textos MUST ser localizados em pt-BR, e a ação e seus resultados MUST permanecer alcançáveis por teclado e por rolagem em mobile e desktop. HTMX pode atualizar a tela, mas não pode substituir validação ou autorização no servidor.

#### Scenario: Pessoa revisa a prévia antes de aceitar

- **WHEN** a pessoa altera o valor da compensação no formulário
- **THEN** a interface mostra o mesmo abatimento previsto para as duas dívidas e o valor ainda disponível para Pix, sem persistir a operação

#### Scenario: Histórico distingue Pix de compensação

- **WHEN** uma pessoa consulta uma dívida depois da compensação
- **THEN** a tela discrimina o valor compensado e o evento de histórico sem apresentá-lo como Pix confirmado ou pagamento recebido
