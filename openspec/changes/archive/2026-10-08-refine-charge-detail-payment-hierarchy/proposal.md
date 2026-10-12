# Proposal

## Why

O detalhe da cobrança apresenta hoje pagamentos e participantes em blocos separados. Isso faz o estado financeiro competir com a identidade de cada pessoa e obriga o cobrador a correlacionar informações repetidas para saber quem precisa de atenção.

O protótipo revisado e aprovado consolida essa leitura: a identidade — conta Pixu ou convite anônimo — é a hierarquia estável; o estado do pagamento apenas ordena e complementa cada pessoa.

## What Changes

- Reorganizar o detalhe da cobrança, na visão autenticada do cobrador/recebedor, em um único cartão de participantes e cotas.
- Separar o cartão em **Contas Pixu** e **Convites Anônimos**, sem duplicar pessoas em uma lista financeira independente.
- Ordenar os pagantes dentro de cada grupo por atenção financeira: pagamento Pix pendente de confirmação manual, saldo sem Pix pendente e cota quitada. A participação do próprio recebedor permanece identificada como cota própria, quando existir.
- Exibir o atalho **Confirmar recebimento** somente ao recebedor para cada Pix `PENDING`, preservando a confirmação manual e a ação de rejeição já autorizada.
- Exibir **“Em aberto há …”** somente quando não há Pix iniciado para a cota; o texto descreve o tempo em aberto, não atraso ou vencimento.
- Quando uma cota tiver itens extras, exibir sua composição aritmética — base comum, cada item extra e total — na própria linha, e alinhar à esquerda o atalho de abrir os detalhes da cota.
- Manter a origem de cada pessoa legível no grupo correspondente e preservar o escopo restrito das identidades temporárias convidadas.
- Atualizar as diretrizes visuais e o protótipo aprovado como referência de implementação.

## Capabilities

### New Capabilities

_Nenhuma._

### Modified Capabilities

- `charges`: altera a apresentação e a ordenação operacional de participantes e cotas no detalhe autenticado da cobrança.
- `settlements/payments`: adiciona a apresentação contextual de Pix pendentes e o atalho de confirmação manual no detalhe da cobrança para o recebedor autorizado.

## Impact

- Templates do detalhe de cobrança e seus fragmentos HTMX.
- Contexto de consulta da cobrança para associar participação, dívida, reservas e pagamentos sem consultas por linha.
- Ações existentes de confirmar/rejeitar pagamento, incluindo seus testes de autorização e atualização HTMX.
- `docs/product-design.md`, o protótipo estático de referência e testes de integração/E2E do detalhe da cobrança.
