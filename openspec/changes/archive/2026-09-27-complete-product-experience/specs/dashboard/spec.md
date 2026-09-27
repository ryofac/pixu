# dashboard Specification

## Purpose

Apresenta à pessoa autenticada uma visão resumida de suas obrigações e atividades recentes, sem substituir o histórico financeiro das cobranças nem criar um extrato global.

## ADDED Requirements

### Requirement: Resumo de saldos e compensação potencial

O dashboard autenticado MUST apresentar separadamente os valores em aberto a receber e a pagar, somando somente dívidas de cobranças `ACTIVE` e considerando pagamentos confirmados e compensações aplicadas. Os totais MUST permanecer brutos por direção, sem compensar uma direção contra a outra. O potencial de compensação MUST aparecer separado e não ser somado a nenhum total.

#### Scenario: Totais exibem obrigações ativas

- **WHEN** uma pessoa possui dívidas abertas ativas nas duas direções e cobranças aguardando aceite
- **THEN** o dashboard mostra os valores abertos a receber e a pagar sem incluir as cobranças ainda não ativas

#### Scenario: Potencial não altera os totais

- **WHEN** existem dívidas recíprocas elegíveis para compensação
- **THEN** o dashboard apresenta o potencial separadamente e mantém inalterados os totais brutos a receber e a pagar

#### Scenario: Saldos já liquidados não são contados

- **WHEN** pagamentos confirmados ou compensações reduziram uma dívida ativa
- **THEN** o dashboard soma somente o saldo ainda aberto dessa dívida

### Requirement: Convites e cobranças recentes

O dashboard MUST mostrar convites pendentes da pessoa autenticada e listas curtas de cobranças que ela criou e das cobranças em que participa. Cada item MUST levar ao detalhe autorizado da cobrança; os grupos MUST ser identificados sem confundir autoria, participação e recebimento.

#### Scenario: Pessoa tem convites e cobranças

- **WHEN** a pessoa autenticada possui convites pendentes e cobranças criadas ou participadas
- **THEN** o dashboard apresenta essas atividades em seções separadas e permite abrir os itens correspondentes

#### Scenario: Nenhuma atividade recente

- **WHEN** uma seção não possui cobranças ou convites para mostrar
- **THEN** o dashboard exibe um estado vazio orientador sem sugerir que a pessoa possui uma dívida inexistente

#### Scenario: Terceiro tenta abrir cobrança do dashboard

- **WHEN** uma pessoa tenta acessar uma cobrança por link ou requisição não autorizada
- **THEN** a autorização no servidor impede o acesso como nas rotas existentes
