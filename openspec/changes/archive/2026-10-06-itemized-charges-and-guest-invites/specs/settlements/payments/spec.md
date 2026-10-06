# Spec Delta

## ADDED Requirements

### Requirement: Registro de pagamento por convidado

Uma pessoa com sessão convidada válida MUST poder registrar pagamento parcial ou integral positivo, em centavos inteiros, somente para a dívida da sua própria participação em cobrança `ACTIVE`, depois da confirmação da cota e até o valor disponível para liquidar. O convidado MAY anexar comprovante nos mesmos formatos e limites dos demais pagamentos. O registro MUST ficar `PENDING`, reservar o valor sem reduzir o saldo aberto e usar as mesmas regras de validação, armazenamento privado, idempotência e concorrência dos pagamentos existentes. A decisão de confirmar ou rejeitar MUST continuar exclusiva do recebedor autenticado.

#### Scenario: Convidado registra pagamento parcial

- **WHEN** o convidado registra R$ 20,00 para sua dívida ativa de R$ 50,00
- **THEN** o sistema cria pagamento `PENDING`, reserva R$ 20,00 e mantém o saldo aberto em R$ 50,00, deixando R$ 30,00 disponíveis

#### Scenario: Convidado envia comprovante válido

- **WHEN** o convidado registra pagamento com comprovante permitido e dentro do limite configurado
- **THEN** o comprovante fica privado, visível somente ao acesso convidado da própria cota e às pessoas autenticadas já autorizadas pelo pagamento

#### Scenario: Convidado excede disponibilidade ou usa acesso vencido

- **WHEN** o convidado tenta registrar valor acima do disponível, usar uma dívida alheia, ou agir por link expirado, revogado ou de cobrança cancelada
- **THEN** o servidor recusa a operação sem criar pagamento, persistir arquivo ou alterar saldos

#### Scenario: Recebedor mantém confirmação manual

- **WHEN** um convidado registra pagamento e anexa comprovante
- **THEN** o pagamento permanece `PENDING` até que o recebedor autenticado o confirme ou rejeite manualmente

### Requirement: Acesso convidado ao próprio comprovante

Uma sessão convidada válida MUST poder consultar somente comprovantes dos pagamentos da própria participação, enquanto a credencial e a sessão estiverem válidas. O acesso MUST usar entrega privada após autorização do servidor; a URL do arquivo MUST NOT ser pública nem permitir acesso a pagamentos de outra participação. O recebedor e o criador autorizado continuam podendo consultar o comprovante pelos fluxos autenticados existentes.

#### Scenario: Convidado acessa comprovante da própria cota

- **WHEN** o convidado abre um comprovante vinculado a pagamento de sua dívida por uma sessão válida
- **THEN** o servidor entrega o arquivo privado sem expor armazenamento ou metadados a visitantes

#### Scenario: Convidado ou terceiro acessa comprovante alheio

- **WHEN** o convidado troca o identificador do pagamento ou um terceiro usa uma URL conhecida
- **THEN** o servidor nega o acesso sem entregar arquivo ou metadados
