# charges Specification

## Purpose

Preserva a integridade histórica das cobranças ao impedir alterações estruturais depois que uma operação financeira foi iniciada.

## Requirements

### Requirement: Bloqueio após pagamento

Desde o primeiro pagamento registrado, inclusive quando estiver `PENDING` e mesmo que seja rejeitado depois, a cobrança MUST bloquear definitivamente alterações do valor total, participantes, cotas e recebedor. A tentativa de edição MUST falhar no servidor e não alterar nenhuma participação ou dívida.

#### Scenario: Pagamento pendente bloqueia edição

- **WHEN** o criador tenta mudar cota, participante ou recebedor depois que um pagamento foi registrado e permanece pendente
- **THEN** o servidor recusa a edição com mensagem explicativa e preserva os valores anteriores

#### Scenario: Rejeição não desbloqueia

- **WHEN** o único pagamento registrado é rejeitado e o criador tenta editar a cobrança
- **THEN** a edição continua recusada, pois o bloqueio é definitivo nesta versão

#### Scenario: Cobrança sem operação permanece editável

- **WHEN** o criador edita uma cobrança ativa ou aguardando aceite sem pagamento registrado nem compensação aplicada
- **THEN** as regras anteriores de aceites e cotas continuam sendo aplicadas e a alteração válida é persistida

### Requirement: Bloqueio de edição após compensação

Ao aplicar uma compensação, o sistema MUST bloquear definitivamente a edição estrutural das duas cobranças envolvidas, incluindo total, participantes, cotas e recebedor, mantendo o histórico e os valores das dívidas coerentes.

#### Scenario: Compensação bloqueia as duas cobranças

- **WHEN** uma compensação é aplicada entre dívidas de cobranças distintas
- **THEN** ambas as cobranças ficam bloqueadas para edição e tentativas posteriores são recusadas pelo servidor sem alterar dados

#### Scenario: Repetição não altera o bloqueio

- **WHEN** o pedido de compensação já aplicado é reenviado
- **THEN** nenhuma cobrança é alterada novamente e o bloqueio permanece associado às duas operações financeiras registradas

### Requirement: Valores monetários em pt-BR

Os formulários de criação, prévia e edição de cobrança MUST aceitar a representação monetária pt-BR com vírgula decimal, como `150,00`, e MUST normalizar o valor no servidor para centavos inteiros. A interface MUST exibir valores em reais com duas casas e vírgula decimal; erros de entrada MUST ser apresentados em pt-BR. A validação MUST continuar server-side em POST convencional e HTMX.

#### Scenario: Prévia aceita vírgula decimal

- **WHEN** a pessoa informa `150,00` e solicita a prévia do rateio por HTMX
- **THEN** o servidor aceita o valor, calcula as cotas sobre 15000 centavos e a prévia mostra `150,00` sem erro em inglês

#### Scenario: Valor inválido permanece localizado

- **WHEN** a pessoa informa um valor que não pode ser convertido em dinheiro
- **THEN** o formulário preserva os demais campos e mostra uma mensagem de erro em pt-BR, sem criar ou alterar cobrança

### Requirement: Pluralização de contagens

As contagens visíveis de pessoas convidadas, participantes e contas disponíveis MUST usar a forma singular para uma pessoa e plural para mais de uma, de maneira traduzível pelo sistema de internacionalização do Django.

#### Scenario: Uma pessoa disponível

- **WHEN** existe exatamente uma conta disponível para convite ou uma participação na cobrança
- **THEN** a interface mostra `1 pessoa` ou `1 pessoa disponível`, sem o plural `pessoas`

#### Scenario: Várias pessoas

- **WHEN** existem duas ou mais contas disponíveis ou participações
- **THEN** a interface mostra a quantidade e a forma plural `pessoas`

### Requirement: Composição responsiva da cobrança

As telas de criação, prévia e detalhe de cobrança MUST adaptar sua composição aos breakpoints nativos do Tailwind: conteúdo em uma coluna e navegação inferior no mobile; navegação lateral e colunas de conteúdo em telas largas. A composição MUST evitar overflow horizontal, preservar uma área segura para a navegação fixa e manter ações e campos alcançáveis por rolagem e teclado.

#### Scenario: Criação em viewport móvel

- **WHEN** a pessoa abre a criação de cobrança em viewport estreita e percorre o formulário até o final
- **THEN** nenhum campo ou ação fica permanentemente coberto pela navegação inferior e não existe rolagem horizontal

#### Scenario: Detalhe em viewport desktop

- **WHEN** a pessoa abre o detalhe em viewport larga
- **THEN** a navegação lateral, o resumo, os participantes e os pagamentos permanecem alinhados em uma composição própria para desktop, sem moldura de telefone

### Requirement: Cancelamento lógico pelo criador

O criador MUST poder cancelar logicamente uma cobrança ativa ou aguardando aceite pela página de detalhe, informando um motivo opcional. Somente o criador pode executar essa ação. Se houver qualquer compensação aplicada a uma dívida da cobrança, o cancelamento MUST ser recusado sem alterar estados financeiros. Quando permitido, a cobrança MUST passar ao estado `CANCELLED`, sair dos totais e ações ativos e permanecer visível como histórico para o criador, recebedor e participantes; convites pendentes MUST ser invalidados. Todos os pagamentos vinculados MUST permanecer no histórico com estado `REVOKED`, sem estorno de transferências externas ou recriação das dívidas. O sistema MUST guardar quem cancelou, quando e o motivo informado; se preenchido, o motivo MUST aparecer no histórico visível às pessoas autorizadas da cobrança.

#### Scenario: Criador cancela cobrança sem compensações

- **WHEN** o criador confirma o cancelamento de uma cobrança ativa que não possui compensações
- **THEN** a cobrança aparece como cancelada no histórico dos envolvidos, deixa de integrar totais e ações ativos, e seus pagamentos permanecem como revogados com seus comprovantes

#### Scenario: Cancelamento de convite ainda pendente

- **WHEN** o criador cancela uma cobrança que ainda aguarda respostas
- **THEN** os convites pendentes deixam de poder ser aceitos ou recusados e a cobrança aparece como cancelada no histórico dos envolvidos

#### Scenario: Motivo de cancelamento opcional

- **WHEN** o criador cancela uma cobrança sem preencher o motivo
- **THEN** o cancelamento é concluído e o histórico registra autor e data sem exigir texto

#### Scenario: Motivo informado aparece no histórico

- **WHEN** o criador cancela uma cobrança e informa um motivo
- **THEN** as pessoas autorizadas a consultar o histórico veem o motivo junto do estado cancelado

#### Scenario: Participante tenta cancelar

- **WHEN** alguém que não é o criador tenta cancelar uma cobrança por requisição convencional ou HTMX
- **THEN** o servidor nega a operação e preserva cobrança, convites, pagamentos e saldos

#### Scenario: Cobrança com compensação não pode ser cancelada

- **WHEN** o criador tenta cancelar uma cobrança que possui ao menos uma compensação aplicada em qualquer dívida vinculada
- **THEN** o servidor recusa a ação, informa que a compensação impede o cancelamento e não altera o histórico financeiro

#### Scenario: Histórico permanece acessível após cancelamento

- **WHEN** o criador, recebedor ou participante abre uma cobrança cancelada
- **THEN** a tela identifica o estado cancelado e preserva os dados históricos, sem ações de aceite, pagamento, compensação ou edição estrutural

### Requirement: Exclusão absoluta auditada pelo superusuário

Somente um superusuário MUST poder excluir absolutamente uma cobrança pela área administrativa. A exclusão MUST ser bloqueada se qualquer dívida da cobrança participar de compensação. Quando permitida e confirmada, MUST remover a cobrança, suas participações, dívidas, pagamentos e comprovantes privados vinculados, sem deixar arquivos órfãos acessíveis pela aplicação. Antes de concluir, MUST persistir uma auditoria mínima contendo o identificador da cobrança excluída, o superusuário responsável, a data e hora e o motivo opcional; a auditoria MUST sobreviver à exclusão e MUST NOT copiar título, valores, comprovantes ou outros dados da cobrança.

#### Scenario: Superusuário exclui cobrança sem compensação

- **WHEN** um superusuário confirma a exclusão absoluta de uma cobrança sem compensações
- **THEN** a cobrança e os dados vinculados deixam de existir, os comprovantes são removidos do storage privado e uma auditoria mínima permanece

#### Scenario: Motivo da exclusão absoluta é opcional

- **WHEN** o superusuário confirma a exclusão sem informar motivo
- **THEN** a exclusão é concluída e a auditoria registra identificador, ator e data sem exigir texto

#### Scenario: Usuário sem privilégio tenta exclusão absoluta

- **WHEN** uma conta que não é superusuário tenta excluir absolutamente uma cobrança
- **THEN** a área administrativa nega o acesso e nenhum dado ou arquivo é removido

#### Scenario: Superusuário tenta excluir cobrança compensada

- **WHEN** o superusuário solicita exclusão absoluta de uma cobrança ligada a compensação
- **THEN** o sistema impede a exclusão, preserva os dois lados do histórico financeiro e informa o motivo do bloqueio

### Requirement: Convite visível quando a recebedora também participa

Ao criar uma cobrança, o sistema MUST criar uma participação `PENDING` e exibi-la na lista de convites da conta para cada pessoa ativa explicitamente selecionada como participante cuja preferência de inclusão direta esteja desativada, inclusive quando essa mesma pessoa for também a recebedora da cobrança. O convite MUST apresentar o título da cobrança, quem a criou, quem recebe e a cota da pessoa, e MUST permitir que somente essa pessoa aceite ou recuse. Para cada conta selecionada cuja titular ativou a preferência de inclusão direta, o sistema MUST criar a participação como `ACCEPTED`, sem convite nem aceite individual, usando a cota calculada pelas regras existentes e criando uma dívida somente quando a pessoa for diferente do recebedor. Selecionar alguém somente como recebedor MUST NOT criar uma participação nem um convite: a seleção de recebedor não substitui a seleção explícita de participantes. Ao aceitar uma participação, a pessoa recebedora MUST NOT receber uma dívida contra si mesma; a cobrança MUST permanecer aguardando aceite enquanto existir qualquer convite pendente e MUST ativar quando todas as participações atuais estiverem aceitas e as regras de total e cotas forem satisfeitas.

#### Scenario: Recebedora selecionada também como convidada

- **WHEN** o criador escolhe a mesma conta ativa, cuja preferência de inclusão direta está desativada, como recebedora e participante e confirma a criação da cobrança
- **THEN** essa conta vê um convite `PENDING` em “Convites” com a cobrança, o criador, a recebedora e sua cota, podendo aceitar ou recusar

#### Scenario: Participante com preferência ativada entra diretamente

- **WHEN** o criador seleciona uma conta ativa cuja titular ativou inclusão direta e confirma a cobrança
- **THEN** a participação é criada como `ACCEPTED`, não aparece como convite pendente e sua dívida é criada conforme as regras existentes se o recebedor for outra pessoa

#### Scenario: Recebedora aceita sua participação

- **WHEN** a recebedora aceita o convite criado para sua própria participação
- **THEN** sua participação passa a `ACCEPTED`, nenhuma dívida é criada contra ela mesma e a cobrança só fica ativa depois que as demais participações atuais forem aceitas

#### Scenario: Recebedora com inclusão direta não recebe dívida contra si

- **WHEN** o criador seleciona como participante uma conta que também é recebedora e cuja titular autorizou inclusão direta
- **THEN** sua participação é criada como aceita sem convite e nenhuma dívida é criada contra ela mesma

#### Scenario: Preferência desativada após participação direta

- **WHEN** uma pessoa desativa inclusão direta depois de ter sido incluída e aceita em uma cobrança existente
- **THEN** sua participação continua aceita e a dívida existente não é revertida

#### Scenario: Recebedora não foi selecionada como participante

- **WHEN** o criador seleciona uma conta somente como recebedora, sem selecioná-la entre os participantes
- **THEN** essa conta não recebe uma participação nem um convite; somente as pessoas explicitamente selecionadas no rateio recebem convites

#### Scenario: Participantes mudam antes da atualização da prévia do rateio

- **WHEN** o criador adiciona ou remove participantes e envia a cobrança antes de a prévia HTMX atualizar as cotas para a seleção atual
- **THEN** o sistema recalcula a divisão igualitária para as contas atualmente selecionadas, cria participações aceitas ou convites conforme a preferência própria de cada conta e não bloqueia a criação por campos de cota desatualizados

### Requirement: Rateio de itens individuais

Ao criar uma cobrança, o criador MUST poder registrar zero ou mais itens individuais com descrição, valor positivo em centavos e uma pessoa participante como responsável. O valor total dos itens MUST ser menor ou igual ao total da cobrança. O restante MUST formar a base comum, dividida igualmente entre todas as participações incluídas ou, no modo anônimo com total declarado, entre o total fixo de pessoas informado pelo criador; cada cota MUST somar sua parcela da base e os itens atribuídos àquela pessoa. O cálculo MUST usar centavos inteiros, distribuir resíduos de forma determinística e manter a soma das cotas persistidas e das vagas futuras exatamente igual ao total. O servidor MUST recalcular e validar os itens e as cotas em submissões convencionais e HTMX.

#### Scenario: Itens extras são somados à base comum

- **WHEN** Ryan cria uma cobrança de R$ 470,00 para quatro pessoas, atribuindo itens de R$ 50,00 a Meireles e R$ 20,00 a Roberto
- **THEN** o sistema divide a base de R$ 400,00 em quatro cotas e apresenta R$ 100,00 para Ryan e Ruan, R$ 150,00 para Meireles e R$ 120,00 para Roberto

#### Scenario: Resíduo da base comum é determinístico

- **WHEN** a base comum de R$ 100,00 é dividida entre três participações
- **THEN** as cotas da base são R$ 33,34, R$ 33,33 e R$ 33,33 em uma ordem estável, e somam exatamente R$ 100,00

#### Scenario: Itens excedem o total

- **WHEN** o criador envia itens cuja soma excede o total da cobrança
- **THEN** o servidor rejeita a cobrança com erro localizado, sem persistir cobrança, itens ou participações

#### Scenario: Item aponta para pessoa fora do rateio

- **WHEN** o criador atribui um item a uma pessoa não incluída entre as participações
- **THEN** o servidor rejeita a submissão e não cria a cobrança

### Requirement: Entrada convidada identificada por nome

O criador MUST poder habilitar entradas anônimas na criação, com limite configurável e default 10, inclusive quando ainda não houver participantes além dele (ou quando optar por não participar). Enquanto as entradas estiverem abertas, cada envio de nome MUST criar uma nova participação convidada na cobrança, sem tratar o nome como username global nem associá-lo automaticamente a uma conta Pixu existente. Nomes podem se repetir na mesma cobrança; cada entrada é diferenciada por uma credencial pessoal. Participações convidadas MUST integrar o cálculo e a soma das cotas como as demais participações, mas MUST NOT criar acesso a dashboard ou a outras cobranças.

#### Scenario: Convidado sem conta participa da cobrança

- **WHEN** uma pessoa acessa o link aberto e confirma o nome “Meireles”
- **THEN** o sistema cria uma participação convidada com nome e cota recalculada, sem exigir e-mail, senha ou username Pixu

#### Scenario: Nome de convidado coincide com username existente

- **WHEN** o criador adiciona um convidado cujo nome coincide com o username de uma conta Pixu
- **THEN** o sistema mantém a participação como convidada, sem conflito de username, associação automática ou acesso à conta existente

#### Scenario: Nomes iguais têm identidades diferentes

- **WHEN** duas pessoas entram com o mesmo nome na mesma cobrança
- **THEN** o sistema cria duas participações independentes com códigos pessoais diferentes

### Requirement: Total explícito no modo anônimo

Quando o criador habilitar entradas anônimas, ele MUST informar explicitamente o total de pessoas que participarão da conta. O total MUST incluir as contas já selecionadas, o criador quando incluído e as vagas que ainda serão ocupadas por pessoas anônimas; MUST ser positivo, limitado a 100 pessoas e não pode ser menor que as participações já selecionadas. O campo e sua validação MUST existir somente para o modo anônimo; cobranças sem entradas anônimas não podem exigir esse valor nem alterar seu fluxo.

O total declarado MUST fixar o denominador da base comum desde a criação. Uma entrada anônima confirmada MUST poder gerar dívida e registrar pagamento enquanto o link compartilhado ainda estiver aberto, sem aguardar o fechamento das entradas. Vagas anônimas ainda não ocupadas não geram dívida, mas preservam a cota reservada no rateio.

#### Scenario: Modo anônimo exige total explícito

- **WHEN** o criador marca entradas anônimas sem informar quantas pessoas participarão
- **THEN** o servidor rejeita a criação com erro no campo do total, sem criar a cobrança

#### Scenario: Total inclui contas selecionadas e vagas anônimas

- **WHEN** o criador participa e convida uma conta, informa total 4 e habilita entradas anônimas
- **THEN** as duas participações atuais recebem suas cotas sobre quatro pessoas e o link pode receber somente as vagas restantes dentro do limite configurado

#### Scenario: Convidado paga antes do fechamento

- **WHEN** uma pessoa entra em uma cobrança com total fixo, confirma a cota e o link ainda está aberto
- **THEN** o sistema libera a dívida para pagamento imediato, sem exigir que o criador feche as entradas

### Requirement: Fechamento e recálculo de entradas

Enquanto as entradas estiverem abertas, cada entrada ou saída MUST recalcular a base comum e as cotas em centavos, mantendo a soma igual ao total. O criador MUST poder fechar as entradas explicitamente; depois do fechamento novos nomes MUST ser recusados e somente identidades já criadas poderão confirmar sua cota. Antes de qualquer pagamento, o criador MUST poder reabrir as entradas para corrigir participantes ou itens e recalcular as cotas.

#### Scenario: Cobrança nasce sem participantes convidados

- **WHEN** o criador habilita entradas anônimas e salva uma cobrança sem nenhuma entrada
- **THEN** a cobrança permanece aguardando entradas, sem permitir pagamento ou fechamento com zero participantes

#### Scenario: Nova entrada recalcula a base

- **WHEN** o total fixo de R$ 470,00 recebe uma nova entrada
- **THEN** a nova participação recebe a parcela da base correspondente ao total declarado, sem alterar as cotas já confirmadas, e a soma das cotas atuais mais as vagas reservadas permanece R$ 470,00

#### Scenario: Fechamento bloqueia novas entradas

- **WHEN** o criador fecha as entradas
- **THEN** o link compartilhado deixa de aceitar novos nomes e os códigos pessoais existentes continuam válidos para confirmação e pagamento

#### Scenario: Reabertura antes do pagamento

- **WHEN** uma pessoa não confirma sua cota e ainda não existe pagamento
- **THEN** o criador pode reabrir e ajustar o conjunto de entradas antes de fechar novamente

### Requirement: Edição de cobrança itemizada antes do pagamento

Em uma cobrança itemizada, enquanto não houver operação financeira, o criador MUST poder revisar os participantes, responsáveis pelos itens, valores dos itens e total pelas regras existentes de edição. A prévia e a cobrança persistida MUST recalcular em conjunto base, itens e cotas. Depois do primeiro pagamento, o sistema MUST manter imutáveis os itens, responsáveis e cotas itemizadas; correções posteriores exigem uma nova cobrança.

#### Scenario: Criador revisa cobrança ainda sem aceite

- **WHEN** o criador altera um item ou participante antes de qualquer aceite ou operação financeira
- **THEN** o sistema recalcula base e cotas, preserva a soma igual ao total e salva a revisão atomicamente

#### Scenario: Aceite protege itens e cotas

- **WHEN** existe um pagamento registrado para qualquer participação
- **THEN** o servidor recusa alterações posteriores dos itens, responsáveis e cotas sem mudar o histórico da cobrança

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

Uma cota com saldo aberto e sem nenhum pagamento registrado MUST exibir **“Em aberto há &lt;duração&gt;”**, calculado desde a criação da dívida. Esse texto MUST descrever tempo em aberto e MUST NOT usar vocabulário de atraso, vencimento, multa ou cobrança vencida. Uma cota com pagamento confirmado ou rejeitado anteriormente, mas ainda com saldo, MUST informar o saldo aberto restante sem ser rotulada como pagamento não iniciado. Cotas liquidadas por Pix confirmado ou compensação MUST informar a quitação de modo compatível com sua forma de liquidação.

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

### Requirement: Navegação para perfis de contas Pixu no detalhe da cobrança

No detalhe autenticado de uma cobrança, toda identidade exibida de uma conta Pixu — criadora, recebedora ou participante cadastrada, inclusive a própria pessoa quando identificada como “Você” — MUST ser um link para o detalhe daquela conta. O link MUST preservar um nome acessível, foco visível e a mesma autorização do detalhe de perfil. Nomes de convidados externos MUST permanecer texto simples: o sistema MUST NOT inferir uma conta pelo nome autodeclarado nem oferecer perfil, `@username` ou rota de conta para eles.

#### Scenario: Participante cadastrado abre seu perfil a partir da cobrança

- **WHEN** uma pessoa autenticada consulta uma cobrança que mostra outra participante cadastrada
- **THEN** o nome daquela participante é um link para seu detalhe de conta autenticado

#### Scenario: Identidade da própria pessoa permanece navegável

- **WHEN** uma pessoa autenticada consulta uma cobrança em que aparece como criadora, recebedora ou participante
- **THEN** sua identificação, inclusive quando o texto visível é “Você”, permite abrir seu próprio perfil

#### Scenario: Convidado externo permanece sem perfil Pixu

- **WHEN** uma cobrança mostra uma participação de convidado externo, mesmo que o nome autodeclarado coincida com um `@username` existente
- **THEN** o nome permanece sem link de perfil e nenhum dado da conta coincidente é exposto
