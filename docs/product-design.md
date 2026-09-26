# Pixu — decisões de produto e interface

**Status:** direção responsiva revisada com o usuário; identidade da logo ainda pendente; tema escuro mapeado para `complete-product-experience`, não implementado

**Escopo desta entrega:** contas, perfil Pix, cobranças, participações e convites.  
**Fontes normativas:** `PIXU_IMPLEMENTATION_BRIEF.md` e a mudança `bootstrap-pixu-and-charges`.

## 1. Princípios

- Mobile-first com uma estrutura própria para desktop; telas largas não ficam presas ao formato de um aparelho.
- Usar os breakpoints nativos do Tailwind (`md:`, `lg:` e `xl:`) para transformar colunas, navegação e densidade dos cartões. Não criar breakpoints paralelos em CSS para as telas do produto.
- Django templates são a fonte do HTML; HTMX atualiza somente regiões identificadas e continua sujeito à mesma validação e autorização do servidor.
- Tailwind é compilado pelo build local do repositório. A interface não depende de CDN.
- Valores monetários são sempre apresentados em reais com duas casas, e persistidos como centavos inteiros.
- Estados financeiros e de convite são nomeados com clareza. “Convite pendente”, “cobrança aguardando aceite” e “dívida ativa” representam situações diferentes.
- Criar cobrança não significa que os convidados aceitaram. Cada aceite confirma a cota e o recebedor; gera dívida somente quando participante e recebedor são pessoas diferentes. A cobrança só ativa quando todos os convites atuais foram aceitos.

## 2. Identidade visual

### 2.1 Referências visuais

Os materiais existentes em `docs/design/` são explorações visuais, não contratos de comportamento. A referência mobile sugere uma identidade Sakura, cards arredondados e navegação simples. Esta proposta preserva a paleta e a abordagem mobile-first, mas corrige a hierarquia de estados e remove dos fluxos atuais pagamento, compensação, dashboard financeiro e confirmação automática. O protótipo desta Wave 0 é autocontido e não carrega Tailwind, fontes ou ícones por CDN.

### 2.2 Logo — definição pendente

A logo atual está inconsistente entre a aplicação e os materiais de exploração: a aplicação usa um símbolo Sakura simplificado em SVG inline com o nome “Pixu”, enquanto referências antigas variam o desenho, incluem uma moldura em losango e usam a grafia “PiXu”. Nenhuma dessas versões está aprovada como identidade final. Antes de consolidar o acabamento visual, definir uma versão canônica da marca — símbolo, wordmark/grafia e variações de uso. Até essa revisão, tratar a marca existente como provisória; esta nota não escolhe nem redesenha uma alternativa.

### 2.3 Paleta, tipografia e ícones

#### Tokens iniciais — tema claro

| Token          | Valor     | Uso                                           |
| -------------- | --------- | --------------------------------------------- |
| `brand`        | `#EC275F` | Marca e detalhes decorativos                  |
| `brand-action` | `#B91649` | Botão principal com contraste de texto branco |
| `brand-hover`  | `#97133D` | Hover/foco reforçado de ação primária         |
| `accent`       | `#FFA7A6` | Destaques secundários e ícones decorativos    |
| `blue-soft`    | `#D4E0EE` | Superfícies informativas                      |
| `canvas`       | `#FFF4F3` | Fundo principal                               |
| `surface`      | `#FFFFFF` | Cartões e formulários                         |
| `text`         | `#2D3748` | Texto principal                               |
| `text-muted`   | `#5B6573` | Texto secundário com contraste legível        |
| `border`       | `#E8D5D8` | Contorno de campos e cartões                  |
| `success`      | `#176B45` | Aceite e sucesso                              |
| `warning`      | `#805400` | Estado pendente e atenção                     |
| `danger`       | `#A12632` | Recusa e erros                                |

Usar fonte do sistema nesta fase. Ícones devem ter rótulo acessível ou ser decorativos com `aria-hidden="true"`. Não depender de carregar uma fonte externa para entender navegação ou status.

### 2.4 Temas claro, escuro e sistema — planejado

**Lote responsável:** `complete-product-experience`. **Rastreabilidade:** tarefas `TEMA-01` a `TEMA-05` no [TODO](../TODO.md#tema-escuro--backlog-de-complete-product-experience). Esta seção registra o trabalho futuro; a entrega atual `bootstrap-pixu-and-charges` ainda oferece somente tema claro.

#### Comportamento previsto

- Oferecer **Claro**, **Escuro** e **Sistema** em um seletor com rótulo persistente e opção atual identificável, acessível por teclado e disponível também nas telas públicas de autenticação.
- Usar **Sistema** na primeira visita. Nessa opção, acompanhar a aparência escolhida no dispositivo, inclusive quando ela mudar com a página aberta. Uma escolha explícita por Claro ou Escuro prevalece sobre o sistema.
- Salvar a preferência somente no navegador, mantendo-a entre páginas e recargas. Sincronização entre dispositivos ou contas não faz parte deste mapeamento. Preferência ausente ou inválida equivale a Sistema; falha de armazenamento não impede usar a aplicação.
- Aplicar a preferência antes da primeira pintura para evitar flash do tema incorreto. Sem JavaScript, a interface continua utilizável e acompanha a preferência do sistema por CSS, com tema claro como fallback quando ela não estiver disponível.
- Alternar aparência preserva os dados dos formulários e o estado da página. Fragmentos retornados por HTMX herdam o tema ativo, inclusive erros e mensagens de sucesso.

#### Cobertura visual

- Definir tokens próprios para os dois temas antes de implementar: fundo, superfícies, texto principal e secundário, bordas, ações, foco e estados de sucesso, aviso e erro. Os valores da seção 2.3 são a referência clara; a paleta escura ainda precisa ser definida e revisada em `TEMA-01`.
- Implementar com tokens e variantes de tema do Tailwind compilado localmente. Preservar a identidade Sakura, sem tratar o tema escuro como simples inversão de cores.
- Cobrir navegação, páginas públicas, autenticação, perfil, formulários, cobranças, convites, estados vazios e fragmentos HTMX. Incluir também as telas de pagamentos, compensações e dashboard disponíveis quando o lote for executado.
- Verificar legibilidade da marca provisória em ambos os fundos; essa adaptação não aprova nem substitui a decisão pendente sobre a logo.

#### Critérios de aceite

1. Sem preferência salva, o tema acompanha o sistema; escolher Claro ou Escuro mantém a escolha após recarga e navegação, inclusive entre páginas públicas e autenticadas.
2. Voltar para Sistema retoma o acompanhamento automático; mudar a aparência do dispositivo só altera a página quando Sistema estiver selecionado.
3. Trocar tema não apaga campos preenchidos nem altera estado de cobranças ou convites. Uma atualização HTMX mantém a aparência correta.
4. As telas previstas são revisadas nos dois temas em celular e desktop, com texto, bordas, foco e estados legíveis; erros e estados permanecem identificáveis sem depender somente de cor.
5. O seletor funciona por teclado e comunica sua opção atual. Carregamento, armazenamento indisponível e ausência de JavaScript têm os fallbacks definidos acima; não há flash do tema incorreto quando a preferência salva pode ser lida.

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

- Listar convites pendentes com título, criador, recebedor, total, cota individual e participantes.
- Ações “Aceitar participação” e “Recusar convite” pedem confirmação por botão explícito e retornam o estado atualizado.
- Cobranças aguardando respostas exibem quantos convites ainda precisam de decisão.
- Uma participação recusada não aparece como dívida.

### Criar cobrança

- Formulário com título, descrição opcional, valor total, seleção de um recebedor e busca de usuários cadastrados.
- O campo “Quem recebe” começa no usuário autenticado e permite escolher outra conta ativa. Receber não inclui automaticamente a pessoa no rateio.
- “Também participo do rateio” começa marcada; desmarcar exclui a cota do criador, mantendo sua autoria e acesso à cobrança. É necessário ao menos um participante.
- Mostrar prévia com campos de cota editáveis antes de salvar. A divisão inicial é igualitária e explica centavos residuais; a soma deve corresponder exatamente ao total. Alterar total ou participantes recalcula a divisão; erros de submissão preservam as cotas digitadas.
- “Conferir cotas” oferece a mesma revisão por POST convencional, inclusive sem JavaScript.
- Permitir editar a cota do criador e cotas pendentes até que a regra de bloqueio se aplique; cotas aceitas ficam visíveis como imutáveis.
- Depois de confirmar, mostrar “Aguardando aceite” quando houver convidados, ou “Ativa” se somente a participação do próprio criador já estiver aceita.

### Detalhe da cobrança

- Cabeçalho: título, criador e recebedor em campos separados, total e estado.
- Lista de participantes com cota e estado de convite.
- Para o criador, expor substituição após recusa e edição permitida de cotas.
- Permitir ao criador trocar o recebedor antes de qualquer aceite de outra pessoa e de operação financeira. Após esse limite, mostrar o recebedor sem edição e explicar o bloqueio. O recebedor tem acesso à cobrança mesmo sem participar do rateio, mas não recebe permissão de edição por esse papel.
- Se o criador participa e escolhe outro recebedor, sua própria dívida é criada junto da cobrança e acompanha os ajustes permitidos de sua cota.
- Para o destinatário, expor somente ações do convite destinado a ele.
- Não mostrar ações de pagamento ou compensação nesta mudança.

### Estrutura para desktop

- A partir de `lg`, usar uma navegação vertical fixa à esquerda, com marca, cobranças, convites e perfil. O contador de convites pendentes continua visível.
- A partir de `lg`, remover o enquadramento de telefone, o fundo escuro externo e a navegação inferior. A área principal ocupa o espaço restante e alinha o conteúdo em uma largura máxima confortável.
- No celular, manter cabeçalho compacto e navegação inferior fixa. A navegação inferior respeita a área segura e nunca cobre ações ou conteúdo.
- Listas de cobranças e convites podem usar duas colunas em `md` e três em `xl`. O detalhe da cobrança organiza o resumo e os participantes em colunas em `lg`; formulários permanecem em uma coluna estreita ou se dividem quando há campos independentes.
- A página pública de entrada não mostra a navegação autenticada; em telas largas, apresenta a chamada principal e os benefícios em duas colunas.

## 4. Componentes e linguagem

- **Botão primário:** uma ação principal por formulário; altura mínima de 44px.
- **Botão secundário:** voltar, cancelar ou ação menos frequente.
- **Campo de formulário:** rótulo persistente, exemplo curto, ajuda e erro associados via `aria-describedby`.
- **Badge de estado:** rótulo textual além da cor: “Pendente”, “Aceito”, “Recusado”, “Aguardando aceite” e “Ativa”.
- **Cartão de participante:** nome, cota, estado e ação que a pessoa tem permissão para executar.
- **Resumo de cotas:** mostra somente as pessoas incluídas, cada valor editável na criação e a soma final; distingue criador, recebedor e participantes.
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
- Em telas largas, usar a navegação lateral e composições em colunas descritas acima; não limitar toda a aplicação a uma moldura de celular.
- Reservar espaço no fim da página para a navegação inferior no celular; em desktop, usar o espaço liberado para conteúdo sem rolagem horizontal.
- Não depender de hover para expor estado ou ação.
- Manter foco visível, ordem de tabulação previsível e rótulos associados a todos os campos.
- Combinar cor com texto/ícone para estados e erros.
- Testar zoom de 200%, leitura em largura estreita, teclado e leitores de tela nos formulários principais.

## 7. Conectividade

A primeira versão é online. Páginas, convites e dados de cobrança vêm do servidor; criar, editar, aceitar ou recusar exige conexão. A interface só confirma uma mudança depois da resposta do servidor. Não implementar PWA, cache de dados pessoais, rascunhos locais nem fila de ações offline neste lote. Suporte offline exigiria mudança OpenSpec própria para sincronização, idempotência e conflitos.

A persistência futura da preferência visual de tema, descrita na seção 2.4, armazena somente a escolha de aparência. Ela não habilita uso offline nem armazenamento de contas, cobranças ou formulários no navegador.

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

Decisões desta revisão: “convite pendente”, “cobrança ativa” e “dívida criada” são estados distintos; a navegação e a composição do desktop são próprias, sem moldura de celular; esta versão exige conexão para qualquer ação que altere estado. O protótipo e os wireframes foram atualizados para refletir a navegação lateral em telas largas. A hierarquia semântica está documentada, mas ainda não passou por teste com usuários.
