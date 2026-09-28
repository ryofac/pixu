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

### Requirement: Cancelamento lógico pelo criador

O criador MUST poder cancelar logicamente uma cobrança ativa ou aguardando aceite pela página de detalhe, informando um motivo opcional. Somente o criador pode executar essa ação. Se houver qualquer compensação aplicada a uma dívida da cobrança, o cancelamento MUST ser recusado sem alterar estados financeiros. Quando permitido, a cobrança MUST passar ao estado `CANCELLED`, sair dos totais e ações ativos e permanecer visível como histórico para o criador, recebedor e participantes; convites pendentes MUST ser invalidados. Todos os pagamentos vinculados MUST permanecer no histórico com estado `REVOKED`, sem estorno de transferências externas ou recriação das dívidas. O sistema MUST guardar quem cancelou, quando e o motivo informado; se preenchido, o motivo MUST aparecer no histórico visível às pessoas autorizadas da cobrança.

#### Scenario: Criador cancela cobrança sem compensações

- **WHEN** o criador confirma o cancelamento de uma cobrança ativa que não possui compensações
- **THEN** a cobrança aparece como cancelada no histórico dos envolvidos, deixa de integrar totais e ações ativos, e seus pagamentos permanecem como revogados com seus comprovantes

#### Scenario: Cancelamento de convite ainda pendente

- **WHEN** o criador cancela uma cobrança que ainda aguarda respostas
- **THEN** os convites pendentes deixam de poder ser aceitos ou recusados e a cobrança aparece como cancelada no histórico dos envolvidos

#### Scenario: Motivo de cancelamento opcional

- **WHEN** o criador cancela uma cobrança sem preencher o motivo
- **THEN** o cancelamento é concluído e o histórico registra autor e data sem exigir texto

#### Scenario: Motivo informado aparece no histórico

- **WHEN** o criador cancela uma cobrança e informa um motivo
- **THEN** as pessoas autorizadas a consultar o histórico veem o motivo junto do estado cancelado

#### Scenario: Participante tenta cancelar

- **WHEN** alguém que não é o criador tenta cancelar uma cobrança por requisição convencional ou HTMX
- **THEN** o servidor nega a operação e preserva cobrança, convites, pagamentos e saldos

#### Scenario: Cobrança com compensação não pode ser cancelada

- **WHEN** o criador tenta cancelar uma cobrança que possui ao menos uma compensação aplicada em qualquer dívida vinculada
- **THEN** o servidor recusa a ação, informa que a compensação impede o cancelamento e não altera o histórico financeiro

#### Scenario: Histórico permanece acessível após cancelamento

- **WHEN** o criador, recebedor ou participante abre uma cobrança cancelada
- **THEN** a tela identifica o estado cancelado e preserva os dados históricos, sem ações de aceite, pagamento, compensação ou edição estrutural

### Requirement: Exclusão absoluta auditada pelo superusuário

Somente um superusuário MUST poder excluir absolutamente uma cobrança pela área administrativa. A exclusão MUST ser bloqueada se qualquer dívida da cobrança participar de compensação. Quando permitida e confirmada, MUST remover a cobrança, suas participações, dívidas, pagamentos e comprovantes privados vinculados, sem deixar arquivos órfãos acessíveis pela aplicação. Antes de concluir, MUST persistir uma auditoria mínima contendo o identificador da cobrança excluída, o superusuário responsável, a data e hora e o motivo opcional; a auditoria MUST sobreviver à exclusão e MUST NOT copiar título, valores, comprovantes ou outros dados da cobrança.

#### Scenario: Superusuário exclui cobrança sem compensação

- **WHEN** um superusuário confirma a exclusão absoluta de uma cobrança sem compensações
- **THEN** a cobrança e os dados vinculados deixam de existir, os comprovantes são removidos do storage privado e uma auditoria mínima permanece

#### Scenario: Motivo da exclusão absoluta é opcional

- **WHEN** o superusuário confirma a exclusão sem informar motivo
- **THEN** a exclusão é concluída e a auditoria registra identificador, ator e data sem exigir texto

#### Scenario: Usuário sem privilégio tenta exclusão absoluta

- **WHEN** uma conta que não é superusuário tenta excluir absolutamente uma cobrança
- **THEN** a área administrativa nega o acesso e nenhum dado ou arquivo é removido

#### Scenario: Superusuário tenta excluir cobrança compensada

- **WHEN** o superusuário solicita exclusão absoluta de uma cobrança ligada a compensação
- **THEN** o sistema impede a exclusão, preserva os dois lados do histórico financeiro e informa o motivo do bloqueio
