## MODIFIED Requirements

### Requirement: Resumo de saldos e compensação potencial

O dashboard autenticado MUST apresentar separadamente **A receber**, **A pagar** e **Já pago**. Os valores em aberto a receber e a pagar MUST somar somente dívidas de cobranças `ACTIVE`, considerando pagamentos confirmados e compensações aplicadas, e MUST permanecer brutos por direção, sem compensar uma direção contra a outra. O valor de **Já pago** MUST somar pagamentos confirmados e compensações aplicadas às dívidas que a pessoa deve, sem contar pagamentos posteriormente revogados. Os três resumos MUST abrir seus extratos correspondentes. O dashboard MUST mostrar até cinco pessoas em cada direção com dívidas ativas, ordenadas pela dívida mais antiga de cada pessoa naquela direção, somando todas as dívidas ativas da mesma direção com aquela pessoa. O potencial de compensação MUST ser sugerido somente no contexto de uma dívida elegível em **A pagar**, sem cartão ou total global de potencial.

#### Scenario: Totais exibem obrigações ativas

- **WHEN** uma pessoa possui dívidas abertas ativas nas duas direções, pagamentos ou compensações e cobranças aguardando aceite
- **THEN** o dashboard mostra os saldos brutos em aberto, o total já liquidado em suas dívidas a pagar e não inclui cobranças ainda não ativas nem pagamentos revogados nos totais

#### Scenario: Saldos já liquidados não são contados

- **WHEN** pagamentos confirmados ou compensações reduzem uma dívida ativa
- **THEN** o dashboard soma somente o saldo ainda aberto em **A pagar** ou **A receber** e contabiliza os eventos liquidados uma única vez em **Já pago** quando reduzem uma dívida da pessoa autenticada

#### Scenario: Potencial não altera os totais

- **WHEN** existem dívidas recíprocas elegíveis para compensação
- **THEN** o dashboard não apresenta cartão nem total global de potencial e pode recomendar a compensação somente junto de uma dívida elegível em **A pagar**, sem alterar os saldos exibidos

#### Scenario: Resumos abrem extratos próprios

- **WHEN** a pessoa seleciona **A pagar**, **A receber** ou **Já pago** no dashboard
- **THEN** o sistema abre o extrato correspondente àquele resumo, inclusive quando não há registros para listar

#### Scenario: Resumo prioriza as pessoas com dívidas mais antigas em cada direção

- **WHEN** a pessoa possui dívidas ativas em uma direção com mais de cinco pessoas
- **THEN** o dashboard apresenta até cinco pessoas nessa direção pela data da dívida ativa mais antiga de cada relação e mostra, para cada uma, a soma de todas as suas dívidas ativas naquela direção com aquela pessoa

#### Scenario: Convidados sem conta não são identificados pelo nome

- **WHEN** várias dívidas a receber pertencem a participações de convidados sem conta Pixu, inclusive com nomes iguais
- **THEN** cada participação convidada permanece uma identidade separada no resumo e o sistema não infere que nomes iguais representam a mesma pessoa

#### Scenario: Nenhuma dívida ativa

- **WHEN** a pessoa não possui dívidas ativas em uma direção
- **THEN** o saldo correspondente aparece como zero e seu atalho continua levando ao estado vazio daquele extrato
