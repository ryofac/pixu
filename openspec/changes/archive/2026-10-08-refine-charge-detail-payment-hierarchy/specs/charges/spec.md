# Spec Delta

## ADDED Requirements

### Requirement: Hierarquia de identidade no detalhe da cobrança

No detalhe autenticado de uma cobrança, a lista de participantes e cotas MUST usar a identidade como hierarquia primária e exclusiva: participações vinculadas a usuários cadastrados aparecem em **Contas Pixu** e participações convidadas sem conta aparecem em **Convites Anônimos**. Uma participação MUST aparecer em apenas um desses grupos e não pode ser repetida em uma lista financeira separada.

Quando a pessoa autenticada é o recebedor, a linha da própria participação, se existir, MUST identificá-la como cota própria e não pode ser apresentada como dívida ou pagamento. As demais linhas MUST mostrar a cota e o estado que a pessoa autenticada tem permissão de acompanhar. A origem da participação MUST permanecer clara pelo título do grupo exclusivo, sem badge redundante em cada linha. O grupo de convite anônimo MUST identificar o nome como autodeclarado sem expor código pessoal, token de acesso ou dados de outras sessões convidadas.

#### Scenario: Recebedor visualiza identidades mistas sem duplicação

- **WHEN** o recebedor abre uma cobrança ativa com participantes de conta Pixu e convidados anônimos
- **THEN** cada pessoa aparece uma única vez em Contas Pixu ou Convites Anônimos com sua cota e origem, sem uma segunda lista de pagamentos concorrente

#### Scenario: Participação do recebedor não parece uma dívida

- **WHEN** o recebedor também participa do rateio
- **THEN** sua linha informa que é uma cota própria e não mostra saldo aberto, ação de pagamento ou ação de confirmação contra si

#### Scenario: Identidade convidada permanece restrita

- **WHEN** o recebedor abre uma linha de Convites Anônimos
- **THEN** vê somente o nome autodeclarado, a origem e o estado financeiro daquela cota, sem código pessoal, token ou dados de acesso do convidado

### Requirement: Ordenação contextual das cotas do recebedor

Para o recebedor autenticado, as cotas devedoras dentro de cada grupo de identidade MUST ser ordenadas pela atenção financeira, sem criar categorias de primeiro nível para pagamentos: primeiro participações que possuem ao menos um Pix `PENDING` a decidir pelo recebedor, depois saldos abertos sem Pix pendente, e por último cotas quitadas. A participação própria do recebedor, quando houver, pode permanecer fixada antes das demais participações de Conta Pixu.

Uma cota com saldo aberto e sem nenhum pagamento registrado MUST exibir **“Em aberto há &lt;duração&gt;”**, calculado desde a criação da dívida. Esse texto MUST descrever tempo em aberto e MUST NOT usar vocabulário de atraso, vencimento, multa ou cobrança vencida. Uma cota com pagamento confirmado ou rejeitado anteriormente, mas ainda com saldo, MUST informar o saldo restante sem ser rotulada como pagamento não iniciado. Cotas liquidadas por Pix confirmado ou compensação MUST informar a quitação de modo compatível com sua forma de liquidação.

#### Scenario: Pix pendente ganha prioridade dentro de Conta Pixu

- **WHEN** uma conta Pixu possui Pix `PENDING` e outra conta Pixu possui somente saldo aberto
- **THEN** ambas permanecem em Contas Pixu e a conta com Pix pendente aparece antes da conta com saldo aberto

#### Scenario: Tempo em aberto não implica atraso

- **WHEN** uma dívida criada há oito dias não tem nenhum pagamento registrado
- **THEN** a linha mostra “Em aberto há 8 dias” e não menciona atraso, vencimento ou penalidade

#### Scenario: Saldo parcial não é tratado como pagamento não iniciado

- **WHEN** uma dívida possui Pix confirmado ou rejeitado no histórico e ainda tem saldo aberto sem Pix pendente
- **THEN** a linha mostra o saldo aberto restante sem usar o texto “Em aberto há” como se nenhum pagamento tivesse sido iniciado

#### Scenario: Cota quitada permanece no grupo de identidade

- **WHEN** uma participação convidada sem conta tem sua dívida integralmente liquidada
- **THEN** ela permanece em Convites Anônimos, depois das cotas que exigem atenção desse grupo, com texto que identifica a quitação

### Requirement: Composição legível da cota com itens extras

No detalhe do recebedor, uma participação com itens extras MUST mostrar a composição exata da sua cota na própria linha: parcela da base comum, cada item extra individual e o total persistido da cota, em uma expressão aritmética equivalente a `base + item + item = total`. Os valores MUST ser formatados em reais e somar exatamente o total da participação; uma cota sem itens extras MUST continuar exibindo somente seu total, sem termos artificiais. O atalho “Ver detalhes da cota” MUST permanecer acessível abaixo da linha e alinhado ao início do conteúdo, sem competir com o valor.

#### Scenario: Cota discrimina dois itens extras

- **WHEN** uma participação possui base de R$ 85,00, itens extras de R$ 5,00 e R$ 6,00 e cota total de R$ 96,00
- **THEN** sua linha mostra a expressão equivalente a `R$ 85,00 + R$ 5,00 (item extra) + R$ 6,00 (item extra) = R$ 96,00` e o atalho de detalhes começa à esquerda

#### Scenario: Cota sem item extra permanece concisa

- **WHEN** uma participação não possui item extra
- **THEN** sua linha mostra somente o valor total da cota e não exibe sinais de soma, parcelas zeradas ou o rótulo “item extra”
