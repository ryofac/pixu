# Pixu — decisões de produto e interface

**Status:** primeira proposta pronta para revisão da Wave 0  
**Escopo desta entrega:** contas, perfil Pix, cobranças, participações e convites.  
**Fontes normativas:** `PIXU_IMPLEMENTATION_BRIEF.md` e a mudança `bootstrap-pixu-and-charges`.

**Conectividade:** offline-first ainda não está especificado nem implementado. A revisão abaixo descreve a hierarquia visual mobile-first, não promete uso sem rede.

## 1. Princípios

- Mobile-first, com navegação e ações que também funcionam em telas largas.
- Django templates são a fonte do HTML; HTMX atualiza somente regiões identificadas e continua sujeito à mesma validação e autorização do servidor.
- Tailwind é compilado pelo build local do repositório. A interface não depende de CDN.
- Valores monetários são sempre apresentados em reais com duas casas, e persistidos como centavos inteiros.
- Estados financeiros e de convite são nomeados com clareza. “Convite pendente”, “cobrança aguardando aceite” e “dívida ativa” representam situações diferentes.
- Sem confirmação implícita: criar cobrança não significa que os convidados aceitaram; convite aceito cria uma dívida; a cobrança só ativa quando todos os convites atuais foram aceitos.

## 2. Referências visuais reconciliadas

Os materiais existentes em `docs/design/` são explorações visuais, não contratos de comportamento. A referência mobile sugere uma identidade Sakura, cards arredondados e navegação simples. Esta proposta preserva a paleta e a abordagem mobile-first, mas corrige a hierarquia de estados e remove dos fluxos atuais pagamento, compensação, dashboard financeiro e confirmação automática. O protótipo desta Wave 0 é autocontido e não carrega Tailwind, fontes ou ícones por CDN.

### Tokens iniciais

| Token | Valor | Uso |
| --- | --- | --- |
| `brand` | `#EC275F` | Marca e detalhes decorativos |
| `brand-action` | `#B91649` | Botão principal com contraste de texto branco |
| `brand-hover` | `#97133D` | Hover/foco reforçado de ação primária |
| `accent` | `#FFA7A6` | Destaques secundários e ícones decorativos |
| `blue-soft` | `#D4E0EE` | Superfícies informativas |
| `canvas` | `#FFF4F3` | Fundo principal |
| `surface` | `#FFFFFF` | Cartões e formulários |
| `text` | `#2D3748` | Texto principal |
| `text-muted` | `#5B6573` | Texto secundário com contraste legível |
| `border` | `#E8D5D8` | Contorno de campos e cartões |
| `success` | `#176B45` | Aceite e sucesso |
| `warning` | `#805400` | Estado pendente e atenção |
| `danger` | `#A12632` | Recusa e erros |

Usar fonte do sistema nesta fase. Ícones devem ter rótulo acessível ou ser decorativos com `aria-hidden="true"`. Não depender de carregar uma fonte externa para entender navegação ou status.

## 3. Navegação e telas

### Conta

- Cadastro por e-mail, nome de usuário e senha; exibir erros no campo correspondente.
- Confirmação de e-mail informa que uma mensagem foi enviada e explica o próximo passo.
- Login, logout e recuperação seguem o fluxo django-allauth existente.
- Após login, encaminhar para a página de cobranças/convites definida no produto, sem mostrar totais que ainda não existem nesta mudança.

### Perfil

- Editar nome de exibição e uma chave Pix principal.
- Texto fixo: “A chave Pix é informada por você. O Pixu não verifica a chave junto ao banco.”
- A edição afeta apenas o perfil da própria pessoa autenticada.

### Convites

- Listar convites pendentes com título, criador, total, cota individual e participantes.
- Ações “Aceitar participação” e “Recusar convite” pedem confirmação por botão explícito e retornam o estado atualizado.
- Cobranças aguardando respostas exibem quantos convites ainda precisam de decisão.
- Uma participação recusada não aparece como dívida.

### Criar cobrança

- Formulário com título, descrição opcional, valor total e busca de usuários cadastrados.
- Criador aparece sempre como participante e único recebedor.
- Mostrar prévia das cotas antes de salvar. A prévia explica centavos residuais e preserva o total exato.
- Permitir editar a cota do criador e cotas pendentes até que a regra de bloqueio se aplique; cotas aceitas ficam visíveis como imutáveis.
- Depois de confirmar, mostrar a cobrança em estado “Aguardando aceite”.

### Detalhe da cobrança

- Cabeçalho: título, criador/recebedor, total e estado.
- Lista de participantes com cota e estado de convite.
- Para o criador, expor substituição após recusa e edição permitida de cotas.
- Para o destinatário, expor somente ações do convite destinado a ele.
- Não mostrar ações de pagamento ou compensação nesta mudança.

## 4. Componentes e linguagem

- **Botão primário:** uma ação principal por formulário; altura mínima de 44px.
- **Botão secundário:** voltar, cancelar ou ação menos frequente.
- **Campo de formulário:** rótulo persistente, exemplo curto, ajuda e erro associados via `aria-describedby`.
- **Badge de estado:** rótulo textual além da cor: “Pendente”, “Aceito”, “Recusado”, “Aguardando aceite” e “Ativa”.
- **Cartão de participante:** nome, cota, estado e ação que a pessoa tem permissão para executar.
- **Resumo de cotas:** mostra os participantes, cada valor e a soma final; inclui o criador.
- **Aviso informativo:** explica confirmação de e-mail, origem da chave Pix ou efeito do aceite sem tom alarmista.

Tom direto e acolhedor. Preferir “Sua participação foi aceita” a mensagens genéricas como “Sucesso”. Não usar texto que sugira transferência, verificação bancária ou quitação nesta mudança.

## 5. Estados, validação e HTMX

- Cada formulário funciona por POST convencional com CSRF e validação no servidor.
- HTMX é melhoria progressiva: respostas podem substituir somente o resumo, a linha de convite ou o formulário que originou a ação.
- Em erro, devolver o fragmento do formulário com valores preenchidos, mensagem junto ao campo e foco apropriado quando possível.
- Em atualização assíncrona, usar região `aria-live="polite"` e manter o foco; não substituir a página inteira para atualizar uma participação.
- Desabilitar botão apenas durante a requisição e restaurá-lo após resposta inválida.
- O servidor verifica titularidade, estado atual, soma de cotas, CSRF e permissão em cada POST, inclusive HTMX.
- Escapar texto fornecido pelo usuário e impor limites de tamanho no backend.

## 6. Responsividade e acessibilidade

- Projetar primeiro para celular: conteúdo em uma coluna, campos de largura total, ações empilhadas e navegação principal fixa na parte inferior, respeitando as áreas seguras do aparelho.
- Em telas maiores, manter a mesma hierarquia e navegação inferior, centralizar o conteúdo e limitar sua largura. Não transformar a experiência em um painel com sidebar.
- Reservar espaço no fim da página para que a navegação fixa não cubra conteúdo ou ações.
- Não depender de hover para expor estado ou ação.
- Manter foco visível, ordem de tabulação previsível e rótulos associados a todos os campos.
- Combinar cor com texto/ícone para estados e erros.
- Testar zoom de 200%, leitura em largura estreita, teclado e leitores de tela nos formulários principais.

## 7. Conectividade e funcionamento offline

O briefing e os specs desta mudança não definem suporte offline. O protótipo é uma demonstração visual e não implementa PWA, cache local, sincronização ou fila de ações. Portanto, “mobile-first” aqui descreve layout e navegação, não funcionamento offline.

Antes de implementar telas e persistência local, definir quais dados podem ser consultados sem rede e quais ações podem ser registradas offline. A decisão importa especialmente para aceitar ou recusar convites: enquanto a operação não for confirmada pelo servidor, a interface não pode apresentá-la como concluída; uma recusa também pode ficar obsoleta se a participação tiver sido substituída.

Como ponto de partida para decidir, uma entrega segura pode manter rascunhos locais e exigir conexão para aceitar/recusar convites e alterar estado financeiro. Se aceite/recusa offline for requisito, será preciso especificar fila persistente, identificador idempotente, resolução de conflitos e indicação explícita de sincronização pendente. A proposta final depende da decisão de produto.

## 8. Telas de pagamentos e compensações futuras

Estes padrões orientam futuras mudanças do OpenSpec e não ampliam o escopo desta tela inicial:

- Pagamento Pix fica pendente até confirmação manual do recebedor; comprovante não é tratado como verificação.
- Um pagamento pertence a uma dívida. Pagamentos parciais são mostrados em linhas próprias.
- Saldo aberto e valor reservado por Pix pendente aparecem separadamente.
- A compensação é uma ação explícita sobre duas dívidas recíprocas; sugestão de compensação não é dinheiro disponível em conta.
- Não há confirmação automática por confiança nem transferência única alocada a várias cobranças nesta versão do brief.

## 9. Entregáveis da revisão

- Wireframes e matriz de estados: `docs/design/pixu-first-vision-wireframes.md`.
- Protótipo navegável local: `docs/design/pixu-first-vision-prototype.html`.
- Este documento define os tokens, componentes, textos, responsividade, acessibilidade e padrões HTMX/Tailwind.

Antes de começar as telas Django, revisar o protótipo, confirmar se “convite pendente”, “cobrança ativa” e “dívida criada” estão claros e decidir o escopo offline.
