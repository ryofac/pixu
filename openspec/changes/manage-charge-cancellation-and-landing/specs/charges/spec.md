# Spec Delta

## ADDED Requirements

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
