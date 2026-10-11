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

Somente o recebedor da dívida MUST poder decidir manualmente sobre pagamento `PENDING`. Por padrão, a confirmação MUST ser manual: confirmar MUST alterar o estado para `CONFIRMED`, registrar quem confirmou e quando e reduzir o saldo uma única vez; rejeitar MUST alterar para `REJECTED`, liberar a reserva e manter o saldo. O recebedor MAY ativar, para uma dívida específica e por ação autenticada própria, a confirmação automática no Pixu de pagamentos futuros declarados pelo devedor autenticado. Ao registrar um pagamento válido para uma dívida assim configurada, o sistema MUST aplicar as mesmas validações, reservas, limites, autorização e atomicidade existentes, persistir diretamente o pagamento como `CONFIRMED` e registrar data e origem automática da confirmação sem atribuí-la a uma ação manual do recebedor. Pagamentos parciais MUST seguir a mesma regra. Pagamentos de convidados sem conta Pixu MUST permanecer `PENDING` para decisão manual, mesmo se a dívida estiver configurada. Desativar a opção MUST afetar somente declarações futuras e MUST NOT reverter pagamentos já confirmados. Comprovantes nunca constituem verificação bancária; o Pixu MUST NOT executar ou verificar a transferência externa. O sistema MUST manter decisões e registros idempotentes, sem dupla liquidação.

#### Scenario: Recebedor confirma

- **WHEN** o recebedor confirma um pagamento pendente de R$ 20,00
- **THEN** o pagamento fica `CONFIRMED`, a confirmação registra usuário e data, o saldo aberto passa de R$ 50,00 para R$ 30,00 e uma segunda confirmação não altera o saldo

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

### Requirement: Confirmação manual contextual no detalhe da cobrança

Quando o recebedor autenticado visualiza uma participação com pagamento `PENDING`, a linha dessa participação MUST identificar que o Pix aguarda confirmação manual, discriminar o valor pendente sem reduzir prematuramente o saldo aberto e oferecer a ação rápida **“Confirmar recebimento”**. A interface MUST orientar a conferência no extrato antes da decisão e MUST NOT sugerir verificação bancária automática pelo Pixu.

A ação de confirmar ou rejeitar MUST continuar disponível somente ao recebedor da dívida. Criadores que não são recebedores, outros participantes e convidados MUST NOT receber ação de decisão na linha; uma tentativa direta no servidor continua negada. Após uma decisão válida por HTMX, a atualização MUST substituir o conteúdo financeiro afetado, anunciar o resultado e reordenar a participação conforme o novo estado sem exigir recarregamento completo.

#### Scenario: Recebedor confirma Pix pendente pela linha da pessoa

- **WHEN** o recebedor confere o extrato e aciona “Confirmar recebimento” para um Pix `PENDING` no detalhe da cobrança
- **THEN** o pagamento é confirmado pelas regras existentes, a linha atualiza saldo e estado, e a pessoa é reordenada dentro de seu grupo de identidade

#### Scenario: Criador sem papel de recebedor não vê decisão

- **WHEN** o criador abre a cobrança mas não é o recebedor de uma dívida com Pix `PENDING`
- **THEN** pode manter os acessos de leitura já autorizados, mas não vê ações de confirmar ou rejeitar e o servidor recusa uma tentativa forjada de decisão

#### Scenario: Pix pendente preserva saldo aberto

- **WHEN** o recebedor vê uma cota com saldo aberto de R$ 117,50 e Pix `PENDING` de R$ 117,50
- **THEN** a linha identifica o Pix aguardando confirmação e continua apresentando R$ 117,50 como saldo aberto até a confirmação manual

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
