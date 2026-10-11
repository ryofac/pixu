# Spec Delta

## MODIFIED Requirements

### Requirement: Confirmação e rejeição manuais

Somente o recebedor da dívida MUST poder decidir sobre pagamento `PENDING`. Por padrão, a confirmação MUST ser manual: confirmar MUST alterar o estado para `CONFIRMED`, registrar quem confirmou e quando e reduzir o saldo uma única vez; rejeitar MUST alterar para `REJECTED`, liberar a reserva e manter o saldo. O recebedor MAY ativar, para uma dívida específica e por ação autenticada própria, a confirmação automática no Pixu de pagamentos futuros declarados pelo devedor autenticado. Ao registrar um pagamento válido para uma dívida assim configurada, o sistema MUST aplicar as mesmas validações, reservas, limites, autorização e atomicidade existentes, persistir diretamente o pagamento como `CONFIRMED` e registrar data e origem automática da confirmação sem atribuí-la a uma ação manual do recebedor. Pagamentos parciais MUST seguir a mesma regra. Pagamentos de convidados sem conta Pixu MUST permanecer `PENDING` para decisão manual, mesmo se a dívida estiver configurada. Desativar a opção MUST afetar somente declarações futuras e MUST NOT reverter pagamentos já confirmados. Comprovantes nunca constituem verificação bancária; o Pixu MUST NOT executar ou verificar a transferência externa. O sistema MUST manter decisões e registros idempotentes, sem dupla liquidação.

#### Scenario: Recebedor confirma

- **WHEN** a dívida não está configurada para confirmação automática e o recebedor confirma um pagamento pendente de R$ 20,00
- **THEN** o pagamento fica `CONFIRMED`, registra usuário e data da confirmação, o saldo aberto passa de R$ 50,00 para R$ 30,00 e uma segunda confirmação não altera o saldo

#### Scenario: Recebedor habilita confirmação para uma dívida

- **WHEN** o recebedor autenticado ativa confirmação automática em uma dívida de uma conta Pixu
- **THEN** somente declarações futuras para aquela dívida ficam elegíveis e a preferência é identificada como própria daquela cota

#### Scenario: Pagamento integral declarado por conta autenticada é confirmado

- **WHEN** o pagador autenticado registra um pagamento válido para uma dívida com confirmação automática ativa
- **THEN** o sistema aplica as validações existentes e salva o pagamento como `CONFIRMED` com data e origem automática, sem ação manual posterior

#### Scenario: Pagamento parcial é confirmado automaticamente

- **WHEN** o pagador autenticado registra R$ 20,00 de uma dívida de R$ 50,00 com confirmação automática ativa
- **THEN** o pagamento é confirmado com origem automática, o saldo aberto passa para R$ 30,00 e o restante continua disponível pelas regras existentes

#### Scenario: Convidado não autenticado permanece no fluxo manual

- **WHEN** uma participação convidada sem conta Pixu declara pagamento para uma dívida com confirmação automática ativa
- **THEN** o pagamento permanece `PENDING` e somente o recebedor pode confirmá-lo ou rejeitá-lo manualmente

#### Scenario: Desativação não reverte confirmação anterior

- **WHEN** o recebedor desativa confirmação automática depois de um pagamento ser confirmado automaticamente
- **THEN** o pagamento confirmado e sua liquidação permanecem finais, mas novas declarações voltam a aguardar confirmação manual

#### Scenario: Recebedor rejeita

- **WHEN** o recebedor rejeita um pagamento pendente que não foi confirmado automaticamente
- **THEN** o pagamento fica `REJECTED`, a reserva é liberada, o saldo aberto permanece igual e o pagador pode registrar novo pagamento disponível

#### Scenario: Pagador não confirma o próprio Pix

- **WHEN** o pagador ou terceiro tenta confirmar ou rejeitar manualmente um pagamento `PENDING`
- **THEN** o servidor responde acesso negado e mantém o estado pendente
