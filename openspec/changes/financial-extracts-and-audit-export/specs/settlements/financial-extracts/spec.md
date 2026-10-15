## ADDED Requirements

### Requirement: Extratos de dívidas em aberto

O sistema MUST disponibilizar extratos autenticados de **A pagar** e **A receber**. **A pagar** MUST consultar somente dívidas em que a pessoa autenticada é devedora; **A receber** MUST consultar somente dívidas em que ela é credora. Ambos MUST limitar a cobrança a `ACTIVE`, a participação a `ACCEPTED` e o saldo aberto a valores positivos. O saldo aberto MUST ser calculado em centavos como valor original menos pagamentos atualmente confirmados e compensações aplicadas aos dois lados da dívida; pagamentos pendentes MUST reservar disponibilidade sem reduzir o saldo aberto.

#### Scenario: Escopo por relação financeira

- **WHEN** uma pessoa consulta os extratos de dívidas
- **THEN** **A pagar** lista somente suas dívidas como devedora e **A receber** lista somente suas dívidas como credora, sem conceder acesso por ser criadora da cobrança

#### Scenario: Saldo considera pagamentos e compensações

- **WHEN** uma dívida ativa e aceita tem pagamentos confirmados, pagamentos pendentes ou compensações
- **THEN** o saldo aberto desconta os pagamentos confirmados e as compensações aplicadas aos dois lados, mas não desconta pagamentos pendentes

#### Scenario: Dívidas aparecem agrupadas por pessoa

- **WHEN** uma pessoa possui mais de uma dívida aberta com a mesma conta
- **THEN** o extrato agrupa as dívidas sob essa conta, mantém uma linha individual por dívida e abre o detalhe autorizado da cobrança ao selecionar a linha

#### Scenario: Convidados permanecem separados

- **WHEN** dívidas a receber pertencem a participações distintas de convidados sem conta, inclusive com nomes iguais
- **THEN** cada participação permanece como grupo próprio, sem inferir identidade pelo nome

#### Scenario: Ordem e busca dos saldos abertos

- **WHEN** uma pessoa abre ou filtra **A pagar** ou **A receber**
- **THEN** as dívidas mais antigas aparecem primeiro, com desempate estável, e a busca considera pessoa ou título da cobrança sem ampliar o escopo autorizado

### Requirement: Linha do tempo de valores liquidados

O extrato autenticado **Já pago** MUST mostrar uma linha por pagamento confirmado e uma linha por compensação aplicada que reduza dívidas da pessoa autenticada como devedora. Um pagamento atualmente `REVOKED` MUST continuar visível como revogado somente quando possuir `confirmed_at`; ele MUST permanecer fora de qualquer total liquidado. Pagamentos revogados sem `confirmed_at` MUST ser omitidos. Cada compensação MUST aparecer uma única vez por pessoa e referenciar as duas cobranças envolvidas.

#### Scenario: Pagamentos confirmados e compensações

- **WHEN** pagamentos são confirmados manual ou automaticamente e uma compensação é aplicada a uma dívida devedora da pessoa
- **THEN** **Já pago** mostra cada pagamento e cada compensação uma vez, com estado e metadados do evento

#### Scenario: Pagamento confirmado depois revogado

- **WHEN** um pagamento que já tinha `confirmed_at` é revogado pelo cancelamento da cobrança
- **THEN** **Já pago** mantém a linha com estado revogado e data efetiva da confirmação, mas exclui seu valor do total liquidado

#### Scenario: Revogação sem confirmação

- **WHEN** um pagamento revogado nunca teve `confirmed_at`
- **THEN** o evento não aparece em **Já pago**

#### Scenario: Data, ordem e período do extrato

- **WHEN** uma pessoa consulta **Já pago** sem filtros ou informa datas inicial e final
- **THEN** pagamentos usam `confirmed_at`, compensações usam `created_at`, o intervalo inclui ambos os dias no fuso configurado, e os eventos são ordenados do mais recente para o mais antigo com desempate estável

#### Scenario: Busca no extrato de liquidações

- **WHEN** uma pessoa busca em **Já pago**
- **THEN** a busca considera a pessoa ou os títulos das cobranças relacionadas sem sair das dívidas em que a pessoa é devedora

### Requirement: Exportação auditável dos extratos

O sistema MUST permitir baixar todos os registros que correspondem aos filtros atuais de cada extrato, sem limitar a exportação à página HTML atual. O CSV MUST usar UTF-8 com BOM e separador `;`, preservar identificadores estáveis, valores exatos em centavos, datas e metadados de pagamento ou compensação, e neutralizar texto livre que possa iniciar fórmulas de planilha. O PDF MUST ser estilizado, conter tipo de extrato, filtros, data de geração, totais, linhas de resultado, cabeçalho repetido e paginação. A autorização MUST ser aplicada também às rotas de download.

#### Scenario: Exportar resultados completos com os filtros atuais

- **WHEN** uma pessoa exporta CSV ou PDF a partir de um extrato paginado e filtrado
- **THEN** o arquivo contém todos os registros autorizados que correspondem à busca e ao período atuais, independentemente da página visível

#### Scenario: Metadados de auditoria

- **WHEN** um arquivo inclui pagamento ou compensação
- **THEN** ele identifica o tipo e o registro de origem, dívida e cobrança, data efetiva e de registro, situação, valor em centavos e metadados aplicáveis, incluindo origem, referência, indicador de comprovante e cobrança pareada

#### Scenario: Proteção de comprovantes e fórmulas

- **WHEN** um arquivo de auditoria contém referência, nome ou outro texto controlado por usuário
- **THEN** o CSV neutraliza prefixos de fórmula e nenhum formato expõe conteúdo ou URL privada de comprovante

#### Scenario: Autorização nos downloads

- **WHEN** uma pessoa tenta baixar um extrato
- **THEN** o arquivo inclui somente registros em que ela é parte financeira autorizada, e um criador sem relação devedor-credor não obtém acesso
