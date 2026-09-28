# Spec Delta

## MODIFIED Requirements

### Requirement: Comprovante privado gerenciável

O sistema MUST validar tipo e tamanho configurados do comprovante, criar o objeto em storage privado compatível com backends locais ou S3-like e servir seu conteúdo somente após autorização do pagador, do recebedor da dívida ou do criador da cobrança à qual o pagamento pertence. O acesso do criador MUST ser somente de leitura e MUST permanecer disponível enquanto o pagamento permanecer no histórico. A interface MUST oferecer ao criador um link para cada comprovante na lista de pagantes da cobrança. O conteúdo MUST ser entregue com disposição de prévia no navegador quando suportada pelo formato, sem tornar o arquivo público. Enquanto o pagamento estiver `PENDING`, somente o pagador MUST poder substituir/editar ou remover seu comprovante; cada operação MUST atualizar os metadados persistidos e remover o objeto anterior quando aplicável. URLs públicas, fixtures com arquivos reais e acesso de terceiros MUST ser proibidos. A remoção do comprovante não altera o estado ou o saldo do pagamento.

#### Scenario: Pagador e recebedor visualizam comprovante

- **WHEN** um pagamento com comprovante possui registro no histórico e o pagador, o recebedor ou o criador da cobrança solicita o arquivo
- **THEN** o servidor entrega o arquivo após verificar a relação autorizada com a dívida ou cobrança, em disposição de prévia no navegador

#### Scenario: Criador acessa comprovante pela lista de pagantes

- **WHEN** o criador abre o detalhe da cobrança e uma pessoa pagante tem comprovante anexado a um de seus pagamentos
- **THEN** a linha dessa pessoa oferece um link para abrir aquele comprovante sem expor o arquivo a visitantes ou outros participantes

#### Scenario: Criador não decide sobre pagamento

- **WHEN** o criador da cobrança não é o recebedor e tenta confirmar ou rejeitar um pagamento usando seu acesso ao comprovante
- **THEN** o servidor nega a decisão e mantém o pagamento inalterado

#### Scenario: Terceiro não acessa comprovante

- **WHEN** outro usuário tenta abrir o comprovante por uma URL conhecida
- **THEN** o servidor responde acesso negado ou não encontrado sem revelar metadados do arquivo

#### Scenario: Tipo ou tamanho inválido

- **WHEN** o usuário envia arquivo que não é PDF, JPEG ou PNG, excede o limite ou não corresponde ao conteúdo declarado
- **THEN** o formulário exibe erro e nenhum arquivo fica persistido ou acessível

#### Scenario: Pagador substitui comprovante pendente

- **WHEN** o pagador envia um novo arquivo válido para um pagamento `PENDING` que já possui comprovante
- **THEN** o novo objeto é criado, os metadados passam a descrevê-lo, o objeto anterior é removido e o pagamento continua pendente sem alterar saldo

#### Scenario: Pagador remove comprovante pendente

- **WHEN** o pagador remove o comprovante de um pagamento `PENDING`
- **THEN** o objeto e seus metadados são removidos, o pagamento continua pendente e as pessoas autorizadas deixam de ver um link de comprovante

#### Scenario: Comprovante confirmado não é editado por terceiro

- **WHEN** o recebedor, o criador, um terceiro ou o pagador tenta substituir ou remover comprovante de pagamento `CONFIRMED` ou de dívida que não lhe pertence
- **THEN** o servidor recusa a operação e preserva arquivo, metadados, estado e saldo

#### Scenario: Pagamento revogado conserva comprovante no histórico

- **WHEN** uma cobrança é cancelada logicamente e um pagamento vinculado passa a `REVOKED`
- **THEN** o pagamento e seu comprovante permanecem no histórico e somente pagador, recebedor e criador daquela cobrança podem abrir o arquivo

## ADDED Requirements

### Requirement: Revogação de pagamentos pelo cancelamento da cobrança

Quando uma cobrança for cancelada logicamente, seus pagamentos MUST permanecer no histórico com estado `REVOKED`, independentemente do estado anterior, sem contar como pagamento pendente ou confirmado para operações ativas. A revogação MUST liberar reservas pendentes, impedir novas decisões ou pagamentos naquela cobrança e MUST NOT representar estorno de uma transferência externa nem recriar dívida. A cobrança cancelada MUST estar excluída dos totais financeiros ativos.

#### Scenario: Pagamento pendente é revogado

- **WHEN** uma cobrança com pagamento `PENDING` é cancelada logicamente pelo criador
- **THEN** o pagamento passa a `REVOKED`, deixa de reservar saldo e permanece no histórico junto do comprovante anexado

#### Scenario: Pagamento confirmado é revogado sem estorno

- **WHEN** uma cobrança com pagamento `CONFIRMED` é cancelada logicamente pelo criador
- **THEN** o histórico identifica o pagamento como revogado e a interface informa que o cancelamento não estorna a transferência externa

#### Scenario: Nova operação em cobrança cancelada

- **WHEN** qualquer pessoa tenta registrar, confirmar, rejeitar ou compensar pagamento de dívida de cobrança cancelada
- **THEN** o servidor recusa a operação e nenhum saldo, pagamento ou compensação é criado ou alterado
