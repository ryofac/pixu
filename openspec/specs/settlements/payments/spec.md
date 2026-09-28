# payments Specification

## Purpose

Registra pagamentos Pix informados pelas pessoas, mantendo reservas, confirmação manual e comprovantes privados sem transformar o Pixu em carteira ou integração bancária.

## Requirements

### Requirement: Chave Pix do recebedor

O sistema MUST permitir que a pessoa autenticada cadastre e altere uma única chave Pix principal no próprio perfil. Ao registrar um pagamento, o sistema MUST mostrar ao pagador a chave atual do recebedor da dívida e uma ação para copiá-la. A interface MUST informar que a chave foi fornecida pelo usuário e não foi verificada pelo Pixu junto a uma instituição financeira.

#### Scenario: Pagador consulta chave do recebedor

- **WHEN** o devedor abre uma dívida ativa com recebedor que possui chave Pix cadastrada
- **THEN** a tela mostra a chave atual, permite copiá-la e informa que a validação bancária não é feita pelo Pixu

#### Scenario: Chave ausente

- **WHEN** o devedor abre uma dívida ativa cujo recebedor ainda não cadastrou chave
- **THEN** a tela informa que o recebedor precisa cadastrar a chave e não inventa ou valida uma chave

### Requirement: Registro de pagamento pendente

Somente o devedor de uma dívida de cobrança `ACTIVE` MUST poder registrar um pagamento positivo, em centavos inteiros, até o valor disponível para liquidar. O pagamento MUST pertencer a uma única dívida, aceitar referência textual opcional limitada e comprovante opcional em PDF, JPEG ou PNG dentro do limite configurado. Ao registrar, o estado MUST ser `PENDING`, o saldo aberto MUST permanecer inalterado e o valor MUST ficar reservado para impedir novo pagamento concorrente.

#### Scenario: Pagamento parcial é reservado

- **WHEN** o devedor registra R$ 20,00 para uma dívida ativa de R$ 50,00 sem outro pagamento pendente
- **THEN** o sistema cria um pagamento `PENDING`, mantém saldo aberto de R$ 50,00 e mostra R$ 20,00 aguardando confirmação, deixando R$ 30,00 disponíveis

#### Scenario: Valor acima do disponível

- **WHEN** o devedor tenta registrar valor maior que o saldo aberto menos reservas pendentes
- **THEN** o sistema rejeita o formulário com erro acionável e não cria pagamento nem altera o saldo

#### Scenario: Estado não permite pagamento

- **WHEN** qualquer pessoa tenta registrar pagamento para dívida de cobrança ainda não ativa ou que não lhe pertence
- **THEN** o servidor responde com acesso negado ou erro de estado, sem criar registro

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

### Requirement: Confirmação e rejeição manuais

Somente o recebedor da dívida MUST poder decidir sobre pagamento `PENDING`. Confirmar MUST alterar o estado para `CONFIRMED`, registrar quem confirmou e quando e reduzir o saldo uma única vez. Rejeitar MUST alterar para `REJECTED`, liberar a reserva e manter o saldo. O sistema MUST aceitar decisões idempotentes sem dupla liquidação e MUST exigir conferência manual; envio de comprovante nunca confirma automaticamente.

#### Scenario: Recebedor confirma

- **WHEN** o recebedor confirma um pagamento pendente de R$ 20,00
- **THEN** o pagamento fica `CONFIRMED`, a confirmação registra usuário e data, o saldo aberto passa de R$ 50,00 para R$ 30,00 e uma segunda confirmação não altera o saldo

#### Scenario: Recebedor rejeita

- **WHEN** o recebedor rejeita um pagamento pendente
- **THEN** o pagamento fica `REJECTED`, a reserva é liberada, o saldo aberto permanece igual e o pagador pode registrar novo pagamento disponível

#### Scenario: Pagador não confirma o próprio Pix

- **WHEN** o pagador ou terceiro tenta confirmar ou rejeitar o próprio pagamento
- **THEN** o servidor responde acesso negado e mantém o estado pendente

### Requirement: Saldos e concorrência

Para cada dívida, o sistema MUST manter `saldo_aberto = valor_original - pagamentos CONFIRMED - compensações aplicadas`; reservas de pagamentos `PENDING` não podem exceder o saldo aberto, e `disponível = saldo_aberto - reservas PENDING`. Persistência de pagamento, rejeição ou compensação e qualquer atualização de saldo materializado MUST ocorrer na mesma transação, com bloqueio suficiente para que operações simultâneas não produzam saldo negativo ou dupla liquidação.

#### Scenario: Duas tentativas concorrentes

- **WHEN** duas requisições tentam reservar ou confirmar a mesma parcela disponível ao mesmo tempo
- **THEN** no máximo o valor disponível é liquidado; uma requisição conclui e a outra recebe conflito ou erro de valor indisponível sem saldo negativo

#### Scenario: Histórico sobrevive à rejeição

- **WHEN** um pagamento pendente é rejeitado
- **THEN** o histórico conserva o registro como `REJECTED`, mas a fonte de saldo não o subtrai e a reserva deixa de contar

#### Scenario: Compensação reduz a disponibilidade das duas dívidas

- **WHEN** uma compensação de R$ 20,00 é aplicada entre duas dívidas com disponibilidade suficiente
- **THEN** o valor compensado é subtraído do saldo aberto de ambas e as reservas pendentes continuam discriminadas sem exceder o novo saldo

### Requirement: Formulários e autorização

Os fluxos de perfil, registro, confirmação, rejeição e download MUST funcionar por POST/GET convencional e poder receber melhoria HTMX. Toda requisição MUST aplicar CSRF quando alterar estado, autenticar o ator, validar os dados no servidor, escapar texto exibido e retornar mensagens acionáveis; uma resposta HTMX não pode ignorar as mesmas permissões.

#### Scenario: Ação HTMX sem permissão

- **WHEN** um usuário autenticado envia uma confirmação por HTMX para dívida de outra pessoa
- **THEN** o servidor rejeita a ação como na requisição convencional e nenhum estado financeiro muda

### Requirement: Internacionalização pt-BR

Textos visíveis nas telas de autenticação, cadastro, recuperação de senha, gerenciamento de e-mail, perfil, pagamentos e comprovantes MUST ser traduzíveis pelo sistema de internacionalização do Django e apresentados em pt-BR nesta entrega. Isso inclui títulos, rótulos, placeholders, ajuda, estados, botões, mensagens de sucesso, mensagens de erro e validações fornecidas pelo django-allauth. Fragmentos HTMX MUST manter a mesma localidade da página; nenhuma mensagem inglesa padrão pode aparecer quando houver tradução pt-BR configurada.

#### Scenario: Gerenciamento de e-mail em pt-BR

- **WHEN** uma pessoa autenticada abre o gerenciamento de endereços de e-mail
- **THEN** títulos, ações de tornar principal, reenviar verificação, remover e adicionar endereço são exibidos em pt-BR e a navegação identifica Perfil como a seção ativa

#### Scenario: Autenticação e validação em pt-BR

- **WHEN** a pessoa abre login, cadastro, recuperação de senha ou envia um formulário inválido
- **THEN** rótulos, placeholders, ajuda e erros aparecem em pt-BR, inclusive mensagens originadas pelo allauth ou pelos campos Django

#### Scenario: Fragmento HTMX localizado

- **WHEN** uma prévia de cobrança, atualização de comprovante ou ação de pagamento retorna um fragmento HTMX com erro ou sucesso
- **THEN** o fragmento mantém textos em pt-BR, associa a mensagem ao campo correto e não reintroduz o texto padrão em inglês

### Requirement: Navegação e identidade consistentes

As telas de perfil, gerenciamento de e-mail, registro de pagamento e comprovante MUST reutilizar a mesma linguagem visual, cabeçalho, marca e navegação responsiva das telas autenticadas. A seção correspondente MUST ficar identificada como ativa em desktop e mobile, inclusive nas rotas do django-allauth; ações e conteúdo não podem ser ocultados pela navegação fixa.

#### Scenario: Rota de conta identifica Perfil

- **WHEN** a pessoa abre edição de perfil ou gerenciamento de e-mail em viewport móvel
- **THEN** o item Perfil da navegação inferior fica ativo, o conteúdo respeita a área segura e existe caminho claro de retorno ao perfil

#### Scenario: Conta e pagamento em telas largas

- **WHEN** a pessoa abre uma tela de conta ou pagamento em viewport desktop
- **THEN** a marca e a navegação lateral permanecem consistentes com Cobranças e Convites, sem regressão para uma moldura de telefone ou overflow horizontal
