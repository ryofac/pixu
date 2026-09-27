# charges Specification

## Purpose

Preserva a integridade histórica das cobranças ao impedir alterações estruturais depois que uma operação financeira foi iniciada.

## Requirements

### Requirement: Bloqueio após pagamento

Desde o primeiro pagamento registrado, inclusive quando estiver `PENDING` e mesmo que seja rejeitado depois, a cobrança MUST bloquear definitivamente alterações do valor total, participantes, cotas e recebedor. A tentativa de edição MUST falhar no servidor e não alterar nenhuma participação ou dívida.

#### Scenario: Pagamento pendente bloqueia edição

- **WHEN** o criador tenta mudar cota, participante ou recebedor depois que um pagamento foi registrado e permanece pendente
- **THEN** o servidor recusa a edição com mensagem explicativa e preserva os valores anteriores

#### Scenario: Rejeição não desbloqueia

- **WHEN** o único pagamento registrado é rejeitado e o criador tenta editar a cobrança
- **THEN** a edição continua recusada, pois o bloqueio é definitivo nesta versão

#### Scenario: Cobrança sem operação permanece editável

- **WHEN** o criador edita uma cobrança ativa ou aguardando aceite sem pagamento registrado nem compensação aplicada
- **THEN** as regras anteriores de aceites e cotas continuam sendo aplicadas e a alteração válida é persistida

### Requirement: Bloqueio de edição após compensação

Ao aplicar uma compensação, o sistema MUST bloquear definitivamente a edição estrutural das duas cobranças envolvidas, incluindo total, participantes, cotas e recebedor, mantendo o histórico e os valores das dívidas coerentes.

#### Scenario: Compensação bloqueia as duas cobranças

- **WHEN** uma compensação é aplicada entre dívidas de cobranças distintas
- **THEN** ambas as cobranças ficam bloqueadas para edição e tentativas posteriores são recusadas pelo servidor sem alterar dados

#### Scenario: Repetição não altera o bloqueio

- **WHEN** o pedido de compensação já aplicado é reenviado
- **THEN** nenhuma cobrança é alterada novamente e o bloqueio permanece associado às duas operações financeiras registradas

### Requirement: Valores monetários em pt-BR

Os formulários de criação, prévia e edição de cobrança MUST aceitar a representação monetária pt-BR com vírgula decimal, como `150,00`, e MUST normalizar o valor no servidor para centavos inteiros. A interface MUST exibir valores em reais com duas casas e vírgula decimal; erros de entrada MUST ser apresentados em pt-BR. A validação MUST continuar server-side em POST convencional e HTMX.

#### Scenario: Prévia aceita vírgula decimal

- **WHEN** a pessoa informa `150,00` e solicita a prévia do rateio por HTMX
- **THEN** o servidor aceita o valor, calcula as cotas sobre 15000 centavos e a prévia mostra `150,00` sem erro em inglês

#### Scenario: Valor inválido permanece localizado

- **WHEN** a pessoa informa um valor que não pode ser convertido em dinheiro
- **THEN** o formulário preserva os demais campos e mostra uma mensagem de erro em pt-BR, sem criar ou alterar cobrança

### Requirement: Pluralização de contagens

As contagens visíveis de pessoas convidadas, participantes e contas disponíveis MUST usar a forma singular para uma pessoa e plural para mais de uma, de maneira traduzível pelo sistema de internacionalização do Django.

#### Scenario: Uma pessoa disponível

- **WHEN** existe exatamente uma conta disponível para convite ou uma participação na cobrança
- **THEN** a interface mostra `1 pessoa` ou `1 pessoa disponível`, sem o plural `pessoas`

#### Scenario: Várias pessoas

- **WHEN** existem duas ou mais contas disponíveis ou participações
- **THEN** a interface mostra a quantidade e a forma plural `pessoas`

### Requirement: Composição responsiva da cobrança

As telas de criação, prévia e detalhe de cobrança MUST adaptar sua composição aos breakpoints nativos do Tailwind: conteúdo em uma coluna e navegação inferior no mobile; navegação lateral e colunas de conteúdo em telas largas. A composição MUST evitar overflow horizontal, preservar uma área segura para a navegação fixa e manter ações e campos alcançáveis por rolagem e teclado.

#### Scenario: Criação em viewport móvel

- **WHEN** a pessoa abre a criação de cobrança em viewport estreita e percorre o formulário até o final
- **THEN** nenhum campo ou ação fica permanentemente coberto pela navegação inferior e não existe rolagem horizontal

#### Scenario: Detalhe em viewport desktop

- **WHEN** a pessoa abre o detalhe em viewport larga
- **THEN** a navegação lateral, o resumo, os participantes e os pagamentos permanecem alinhados em uma composição própria para desktop, sem moldura de telefone
