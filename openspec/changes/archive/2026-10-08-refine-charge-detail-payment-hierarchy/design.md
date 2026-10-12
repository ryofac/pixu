# Design

## Context

O detalhe atual monta duas leituras paralelas: `Pagamentos e saldos`, com um cartão completo por dívida do ator, e `Participantes`, com linhas simples e sem o estado financeiro correspondente. A consulta carrega as participações separadamente das dívidas do ator; o cálculo de saldo por dívida é feito pelo serviço financeiro. A decisão de Pix pendente já é autorizada e transacional, mas o fragmento HTMX atual atualiza somente o cartão da dívida.

O protótipo aprovado em `docs/design/pixu_charge_detail_hierarchy_prototype.html` passa a ser a referência visual do recorte do recebedor. Os requisitos comportamentais estão nas deltas de `charges` e `settlements/payments`; a motivação está em `proposal.md`.

## Goals / Non-Goals

**Goals:**

- Montar uma única lista operacional para o recebedor, agrupada por identidade e sem repetir a mesma pessoa em um bloco financeiro paralelo.
- Derivar, em lote, saldo, reserva Pix e estado de apresentação para cada participação, preservando os cálculos financeiros atuais.
- Reaproveitar os endpoints, autorização e semântica transacional existentes de confirmação e rejeição, atualizando a ordem visual por HTMX.
- Manter pagamento, compensação, comprovantes e itens consultáveis sem ampliar o acesso de criadores, participantes ou convidados.

**Non-Goals:**

- Não criar estados de pagamento, vencimentos, juros, cobranças automáticas ou integração bancária.
- Não alterar o cálculo de cotas, saldos, reservas, compensações, acesso convidado ou a regra de quem pode decidir pagamentos.
- Não substituir a experiência de quem apenas paga uma dívida; o recorte reorganiza a visão do recebedor. As ações existentes de pagador e compensação permanecem nos fluxos próprios.
- Não fazer migração de banco, alterar URLs públicas ou expor código pessoal de convidado.

## Decisions

### 1. Um apresentador para a lista do recebedor

Extrair do `views.py` o contexto reutilizável do detalhe para um módulo de apresentação da cobrança. Esse módulo produzirá uma estrutura de linhas para o recebedor e será usado tanto pelo detalhe inicial quanto pela resposta HTMX de decisão de pagamento.

Cada linha reúne participação, dívida opcional, resumo de saldo, pagamentos pendentes, itens, comprovantes autorizados e metadados de ordenação. A consulta deve buscar todas as participações da cobrança com usuários, itens, dívidas, pagamentos e compensações necessárias e agregar valores de Pix e compensação por dívida em lote. O cálculo resultante mantém a mesma fórmula de `payment_balance`; a apresentação não passa a ser fonte de verdade de dinheiro.

Alternativa considerada: chamar `payment_balance` uma vez por linha. Foi descartada porque aumenta consultas conforme cresce o número de participantes e torna a renderização de uma cobrança com convidados desnecessariamente cara.

### 2. Identidade é o agrupamento; pagamento é o critério de ordenação

O template do recebedor terá um cartão **Participantes e cotas** com dois grupos mutuamente exclusivos: `Contas Pixu` para participações com usuário e `Convites Anônimos` para participações convidadas. A própria cota do recebedor, se presente, fica identificada no primeiro grupo sem parecer cobrança contra si.

Dentro de cada grupo, as linhas de devedores serão ordenadas por uma chave derivada, e não por novos blocos de interface:

1. uma ou mais reservas Pix `PENDING` que o recebedor precisa decidir;
2. saldo aberto sem Pix pendente, priorizando dívida sem nenhum pagamento registrado e, dentro dela, a mais antiga;
3. saldo residual após histórico de Pix ou compensação, sem reserva pendente;
4. dívida quitada;
5. participação ainda pendente de aceite, quando a regra de cobrança permitir que ela coexista com outras cotas ativas.

Uma linha sem qualquer pagamento histórico mostra `Em aberto há <duração>` a partir de `Debt.created_at`; linhas com eventos anteriores mostram saldo e histórico pertinente, sem reutilizar essa frase. A apresentação nunca usa linguagem de atraso ou vencimento.

Alternativa considerada: três seções globais — aguardando aprovação, em aberto e quitado. Foi descartada porque quebra o modelo mental principal da cobrança, duplica identidades e obriga a procurar a mesma pessoa em lugares diferentes.

### 3. Ações pendentes ficam na linha da pessoa e preservam granularidade do Pix

Uma linha com um único Pix pendente mostra valor, aviso de conferência no banco e o atalho `Confirmar recebimento`, além da rejeição já prevista. Havendo mais de um Pix pendente para a mesma dívida, a linha mostra cada reserva como evento distinto com sua respectiva decisão: pagamentos não serão somados em uma ação única, pois confirmação e rejeição são operações por pagamento.

Comprovantes que o criador já pode ler continuam acessíveis na linha ou nos detalhes da cota, mas somente o recebedor recebe ações de decisão. O conteúdo detalhado que não cabe à leitura rápida — histórico de Pix, compensações, itens e comprovantes — permanece acessível sob demanda em diálogo no desktop e bottom sheet no mobile, reutilizando o padrão de modal já presente no detalhe. Isso evita remover auditoria financeira para obter a lista enxuta.

Alternativa considerada: manter todos os cartões de dívida completos abaixo da lista resumida. Foi descartada porque reintroduz a repetição que a mudança elimina.

### 4. Atualização HTMX reordena o fragmento de detalhe

Os formulários de confirmação e rejeição da lista terão como alvo `#charge-content`. Depois de a camada de serviço concluir a decisão, a view de pagamento reconstruirá o contexto compartilhado do detalhe e retornará o fragmento completo com uma mensagem de status. Dessa forma, a linha muda de estado e de posição na mesma resposta, sem recarregar a página nem manter uma ordem obsoleta.

A resposta continua usando o endpoint existente, CSRF, `hx-disabled-elt` e a verificação de credor no servidor. A mensagem é uma região de status e o foco do gatilho é preservado/restaurado conforme o comportamento atual dos modais e swaps.

Alternativa considerada: atualizar somente o cartão da dívida antigo ou forçar `HX-Refresh`. O primeiro não consegue reordenar grupos; o segundo perde o ganho incremental e interrompe a pessoa que estava analisando a cobrança.

### 5. Escopo por papel e responsividade

A nova leitura é habilitada quando o ator autenticado é o recebedor da cobrança. Quando o criador não for o recebedor, ele mantém apenas a leitura e os comprovantes já permitidos; participantes e convidados continuam nos seus fluxos próprios. Isso impede que uma melhoria visual alargue autorização financeira.

Em desktop, o cartão operacional permanece na coluna principal e resumo/link de convidados ficam na lateral. Em mobile, o cartão de participantes e cotas aparece logo após o cabeçalho, seguido do resumo e do link, como no protótipo aprovado. As ações têm pelo menos 44 px de altura, refluem sem rolagem horizontal, e badges sempre combinam texto e cor.

### 6. A cota itemizada explica sua soma na leitura rápida

Quando a participação tiver itens extras, o valor à direita deixa de ser apenas um número isolado e passa a apresentar a operação que forma a cota: `base + item extra + item extra = total`. A base vem de `base_share_cents`; cada parcela adicional vem dos itens vinculados à participação; o resultado exibido continua sendo `share_cents`. Isso mantém a conta auditável na lista sem obrigar a abrir o modal.

A expressão usa `flex-wrap`, valores tabulares e termos inteiros para que, em uma tela estreita, ela quebre entre parcelas sem cortar sinal, valor ou total. Participações sem extras mantêm o total compacto existente. O gatilho “Ver detalhes da cota” fica em um contêiner com alinhamento inicial, imediatamente abaixo da linha e após seu divisor, preservando alvo de toque e foco.

Alternativa considerada: repetir somente o total e deixar os itens exclusivamente no modal. Foi descartada porque a diferença entre base e acréscimos individuais é relevante para entender a cobrança e já está disponível no contexto da linha.

## Risks / Trade-offs

- [Várias reservas para a mesma dívida podem tornar uma linha alta] → manter cada Pix pendente como decisão individual e colocar histórico secundário em diálogo/bottom sheet.
- [Reorganizar o fragmento pode introduzir importação circular entre `charges` e `settlements`] → extrair o construtor de contexto para um módulo sem dependência de views e testá-lo pelos dois chamadores.
- [Cálculos agregados podem divergir da regra financeira] → derivar o resumo com a mesma fórmula de saldo, cobrir cenários de Pix pendente, parcial, confirmado, rejeitado e compensação, e manter os serviços como fonte de verdade.
- [Dados de convidado podem vazar na visão autenticada] → nunca incluir digest, código ou URL pessoal na estrutura de linha; testar a ausência desses dados no HTML.
- [A hierarquia enxuta pode ocultar auditoria útil] → disponibilizar detalhes sob demanda e preservar links privados já autorizados.
- [Uma expressão com muitos itens pode ficar longa no celular] → permitir quebra entre termos, manter cada valor inteiro e preservar o total como último termo visível.

## Migration Plan

1. Introduzir o apresentador e o novo fragmento sem alterar modelos ou rotas.
2. Trocar somente a visão do recebedor para a hierarquia aprovada; manter os fluxos do pagador e do criador não recebedor durante a transição.
3. Atualizar as respostas HTMX de decisão para reconstruírem o fragmento completo e executar testes de autorização, ordenação e reordenação.
4. Construir os assets Tailwind e validar o detalhe em viewport móvel e desktop.

Rollback: restaurar o fragmento anterior e o alvo HTMX de cartão por dívida. Como não há migração nem mudança de dados, o rollback não exige transformação de estado.
