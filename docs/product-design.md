# Pixu — decisões de produto e interface

**Status:** direção responsiva revisada com o usuário; logo System Core e temas claro/escuro/sistema implementados; teste de compreensão dos termos com usuários ainda pendente

**Escopo visual:** entrada pública, dashboard, perfil, cobranças, convites, pagamentos e compensações.
**Fontes normativas:** `PIXU_IMPLEMENTATION_BRIEF.md` e a mudança ativa `openspec/changes/manage-charge-cancellation-and-landing`.

## 1. Princípios

- Mobile-first com uma estrutura própria para desktop; telas largas não ficam presas ao formato de um aparelho.
- Usar os breakpoints nativos do Tailwind (`md:`, `lg:` e `xl:`) para transformar colunas, navegação e densidade dos cartões. Não criar breakpoints paralelos em CSS para as telas do produto.
- Django templates são a fonte do HTML; HTMX atualiza somente regiões identificadas e continua sujeito à mesma validação e autorização do servidor.
- Tailwind é compilado pelo build local do repositório. A interface não depende de CDN.
- Valores monetários são sempre apresentados em reais com duas casas, e persistidos como centavos inteiros.
- Estados financeiros e de convite são nomeados com clareza. “Convite pendente”, “cobrança aguardando aceite” e “dívida ativa” representam situações diferentes.
- Criar cobrança não significa que os convidados aceitaram. Cada aceite confirma a cota e o recebedor; gera dívida somente quando participante e recebedor são pessoas diferentes. A cobrança só ativa quando todos os convites atuais foram aceitos, exceto no modo anônimo com total explícito, em que uma cota fixa pode ser paga enquanto ainda há vagas abertas ou outro convite pendente.

## 2. Identidade visual

### 2.1 Referências visuais

Os materiais existentes em `docs/design/` são referências visuais, não contratos de comportamento. A direção Sakura e os cartões arredondados foram preservados, com hierarquia de estados e layouts próprios para desktop. A aplicação inclui os fluxos financeiros aprovados em mudanças OpenSpec posteriores; confirmação automática só acontece para uma dívida em que o recebedor habilitou essa opção, sem verificação ou integração bancária. O protótipo da Wave 0 é autocontido e não carrega Tailwind, fontes ou ícones por CDN.

### 2.2 Logo — System Core aprovada

A versão canônica é a **System Core Logo** apresentada em [`pixu_logo_system.html`](design/pixu_logo_system.html): flor Sakura de cinco pétalas com núcleo Pix em X, moldura de losango arredondada e wordmark **PiXu**. O gradiente Sakura permanece no símbolo e o recorte do núcleo acompanha a superfície para manter contraste nos temas claro e escuro. Ao integrar, reproduzir o desenho como SVG local, sem carregar as dependências CDN da página HTML de referência; não substituir a marca por outra variação dos protótipos antigos.

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

### 2.4 Temas claro, escuro e sistema — implementados

**Lote responsável:** `complete-product-experience`. **Rastreabilidade:** itens `TEMA-01` a `TEMA-05` no [TODO](../TODO.md#tema-escuro--complete-product-experience). A validação técnica passou; a rodada separada de compreensão dos termos financeiros com três pessoas segue pendente na tarefa 4.2 da mudança.

#### Comportamento previsto

- Oferecer **Claro**, **Escuro** e **Sistema** em um seletor com rótulo persistente e opção atual identificável, acessível por teclado e disponível também nas telas públicas de autenticação.
- Usar **Sistema** na primeira visita. Nessa opção, acompanhar a aparência escolhida no dispositivo, inclusive quando ela mudar com a página aberta. Uma escolha explícita por Claro ou Escuro prevalece sobre o sistema.
- Salvar a preferência somente no navegador, mantendo-a entre páginas e recargas. Sincronização entre dispositivos ou contas não faz parte deste mapeamento. Preferência ausente ou inválida equivale a Sistema; falha de armazenamento não impede usar a aplicação.
- Aplicar a preferência antes da primeira pintura para evitar flash do tema incorreto. Sem JavaScript, a interface continua utilizável e acompanha a preferência do sistema por CSS, com tema claro como fallback quando ela não estiver disponível.
- Alternar aparência preserva os dados dos formulários e o estado da página. Fragmentos retornados por HTMX herdam o tema ativo, inclusive erros e mensagens de sucesso.

#### Cobertura visual

- Definir tokens próprios para os dois temas: fundo, superfícies, texto principal e secundário, bordas, ações, foco e estados de sucesso, aviso e erro. Os valores da seção 2.3 e a tabela escura abaixo estão aplicados ao CSS.
- Implementar com tokens e variantes de tema do Tailwind compilado localmente. Preservar a identidade Sakura, sem tratar o tema escuro como simples inversão de cores.
- Cobrir navegação, páginas públicas, autenticação, perfil, formulários, cobranças, convites, pagamentos, compensações, dashboard, estados vazios e fragmentos HTMX.
- A System Core Logo está implementada como SVG local; seu recorte e losango acompanham os dois temas sem perder o gradiente Sakura.

#### Tokens do tema escuro

| Token            | Valor     | Uso                                        |
| ---------------- | --------- | ------------------------------------------ |
| `canvas`         | `#0F172A` | Fundo principal                            |
| `surface`        | `#1E293B` | Cartões, formulários e navegação           |
| `surface-raised` | `#273449` | Superfícies elevadas e hover               |
| `text`           | `#F8FAFC` | Texto principal                            |
| `text-muted`     | `#CBD5E1` | Texto secundário                           |
| `border`         | `#475569` | Bordas e separadores                       |
| `brand`          | `#FFA7A6` | Detalhes Sakura e links sobre fundo escuro |
| `brand-action`   | `#B91649` | Ação primária com texto branco             |
| `focus`          | `#93C5FD` | Indicador de foco visível                  |
| `success`        | `#86EFAC` | Confirmações e estados positivos           |
| `warning`        | `#FCD34D` | Pendências e atenção                       |
| `danger`         | `#FDA4AF` | Recusas e erros                            |

Os tons escuros são uma superfície azul-ardósia, não uma inversão literal do tema claro. Os pares de texto/ação e superfícies de estado foram exercitados nos testes de navegador; badges e estados mantêm rótulos, não dependem somente de cor.

### 2.5 Aplicativo web instalável (PWA)

- O Pixu oferece um manifesto PWA em `/manifest.webmanifest`, com `display: standalone`, escopo na raiz e tema Sakura coerente com os temas claro/escuro. A instalação não transforma o produto em uma carteira nem em uma aplicação offline.
- A logo System Core em SVG continua sendo a fonte vetorial da marca. Os ícones instaláveis `192x192`, `512x512` e Apple Touch Icon são derivados dela em alta definição, com fundo `canvas` para preservar a área segura em máscaras de launcher.
- O shell registra um service worker de escopo raiz apenas para cumprir o requisito de instalação e encaminha as requisições à rede. Não armazenar contas, cobranças, chaves Pix, comprovantes, formulários ou respostas HTMX em cache local.
- Em celulares Android compatíveis, capturar `beforeinstallprompt` e mostrar um convite discreto, dispensável e posicionado acima da navegação inferior. O botão deve ter pelo menos 44px de altura e só abrir o prompt nativo após ação explícita da pessoa.
- No iOS, onde o prompt nativo não é exposto ao navegador, mostrar instrução equivalente: **Compartilhar → Adicionar à Tela de Início**. Não mostrar o convite quando a página já estiver em modo standalone; uma dispensa vale por sete dias.
- O convite usa texto e ícone, mantém foco visível e não cobre o conteúdo principal. Sem JavaScript, a aplicação continua utilizável e o manifesto permanece disponível para o navegador.

### 2.6 Landing page pública

**Referências revisadas:** [`pixu_landing_page.html`](design/pixu_landing_page.html) para composição e conteúdo; [`pixu_logo_system.html`](design/pixu_logo_system.html) para a marca aprovada. São referências visuais, não arquivos para servir diretamente: substituir URLs `#` pelas rotas reais, localizar para pt-BR e manter o build local.

- Preservar cabeçalho com marca, seletor de tema e entrada; hero com chamada e cadastro; e os caminhos reais de criar conta e entrar. Usuário autenticado vê o dashboard ao abrir a rota inicial.
- Organizar o conteúdo público em três seções verticais sequenciais: criar rateio, convidar e aceitar cotas; acompanhar pagamentos feitos fora do Pixu e anexos, com confirmação manual como padrão; consultar saldos, compensações, histórico e cancelamento de cobrança pelo criador.
- Em mobile e desktop, todas as seções aparecem na mesma ordem por rolagem normal, sem scroll snap obrigatório, captura de rolagem, conteúdo escondido ou animação necessária para entendê-las. Usar uma coluna em telas estreitas e composições próprias para telas largas.
- Manter paleta Sakura, gradientes suaves e superfícies com contraste suficiente nos dois temas. Usar os tokens definidos nesta seção, fonte de sistema e ícones SVG locais/inline; não carregar Tailwind, fontes ou icon fonts por CDN.
- Todo conteúdo visível é pt-BR. Usar exemplos abstratos que representem ações possíveis, sem nomes, contas ou transações reais e sem afirmar que um pagamento, verificação ou cancelamento ocorreu para uma pessoa real. Descrever somente funcionalidades disponíveis na aplicação; não apresentar exclusão administrativa ou extrato global.
- A ilustração é estática e puramente decorativa, sem movimento contínuo. Se houver animação futura, respeitar `prefers-reduced-motion: reduce` e não criar/remover nós continuamente para simular chuva de pétalas.
- O seletor segue a regra **Claro / Escuro / Sistema** da seção 2.4, inicia em Sistema e persiste apenas a preferência visual no navegador. A preferência deve ser aplicada antes da primeira pintura; sem JavaScript, a página continua legível e acompanha o sistema por CSS.

#### Critérios de aceite

1. Sem preferência salva, o tema acompanha o sistema; escolher Claro ou Escuro mantém a escolha após recarga e navegação, inclusive entre páginas públicas e autenticadas.
2. Voltar para Sistema retoma o acompanhamento automático; mudar a aparência do dispositivo só altera a página quando Sistema estiver selecionado.
3. Trocar tema não apaga campos preenchidos nem altera estado de cobranças ou convites. Uma atualização HTMX mantém a aparência correta.
4. As telas previstas são revisadas nos dois temas em celular e desktop, com texto, bordas, foco e estados legíveis; erros e estados permanecem identificáveis sem depender somente de cor.
5. O seletor funciona por teclado e comunica sua opção atual. Carregamento, armazenamento indisponível e ausência de JavaScript têm os fallbacks definidos acima; não há flash do tema incorreto quando a preferência salva pode ser lida. Esses critérios foram cobertos na E2E mobile/desktop e na suíte Django.

## 3. Navegação e telas

### Conta e autenticação

- **Entrada com SSO e tradicional:** Suporte a SSO via Google e GitHub, além do login tradicional por usuário/e-mail e senha.
  - Botões sociais proeminentes no topo do cartão de autenticação: **Continuar com Google** e **Continuar com GitHub**, com altura mínima de 48px (`min-h-12`), cantos arredondados (`rounded-xl`), SVGs inline oficiais locais e contraste acessível nos temas claro e escuro.
  - Divisor semântico sutil com texto: `ou entre com e-mail e senha`.
  - Formulário convencional com campos de identificador e senha, rótulos persistentes e botão primário **Entrar** (`bg-pixu-action-solid`).
- **Onboarding e solicitação inicial de chave Pix:**
  - No primeiro acesso após o cadastro (seja por SSO ou cadastro tradicional), a pessoa é recebida em uma tela dedicada de boas-vindas / onboarding.
  - Confirmação do identificador `@username`: campo obrigatório no cadastro com sugestão automática gerada a partir do nome da pessoa, permitindo ajuste direto no input.
  - Solicitação da chave Pix principal: campo único e simplificado de texto livre (_"Cole sua chave Pix"_), sem menus ou seletores burocráticos de tipos de chave (a chave é colada pelo usuário).
  - Texto fixo obrigatório: _“A chave Pix é informada por você. O Pixu não verifica a chave junto ao banco.”_
  - Botões de ação diretos e objetivos: ação primária **Salvar e continuar** e ação secundária subordinada **Fazer depois** (salvando o nome e `@username`, deixando apenas a chave Pix vazia).
- **Aviso de chave pendente no Dashboard:**
  - Caso a pessoa opte por "Fazer depois", um banner em destaque no topo do Dashboard alerta sobre a ausência da chave (_"Sua chave Pix ainda não foi configurada. Você pode participar de cobranças normalmente, mas precisará cadastrar uma chave para poder receber dinheiro quando criar um rateio."_), com botão de ação direta **Configurar chave Pix**.
  - Alerta contextual ao tentar criar cobrança onde o criador seja o recebedor sem ter cadastrado chave Pix.
- **Fluxos convencionais Allauth:** Confirmação de e-mail informa envio e próximos passos; recuperação de senha e logout seguem o padrão visual do layout de entrada.
- Após login/onboarding, encaminhar para o dashboard autenticado; a lista completa permanece disponível em **Cobranças** (`/charges/`).

### Perfil

- O detalhe canônico por `@username` exige autenticação. Para a própria conta, o título é **Meu perfil** e permanecem as ações de editar perfil, gerenciar e-mail e sair; para outra conta, o título é **Perfil de {nome}** e a página é somente leitura.
- Em telas móveis, identidade e chave Pix aparecem em cartões empilhados; em telas largas, ficam lado a lado, com cobranças em comum ocupando a largura abaixo. A identidade mostra nome e `@username`.
- A chave Pix principal não vazia pode ser consultada por qualquer pessoa autenticada que acesse o detalhe, mesmo sem cobrança em comum. O cartão informa que a chave foi declarada pela titular e não é verificada pelo Pixu; quando ausente, mostra um estado vazio sem inventar valor ou ação de pagamento. A titular também pode copiar a chave.
- Somente o perfil de outra conta mostra **Cobranças em comum**. Essa seção lista a interseção das cobranças que visitante e conta-alvo podem acessar, com somente título, estado textual e link para o detalhe que valida acesso novamente. Não mostra valor, cotas, participantes, saldos, pagamentos, comprovantes, e-mail nem dados de terceiros. Sem cobranças compartilhadas, usa um estado vazio neutro.
- No detalhe autenticado de cobrança, criadora, recebedora e participantes com conta Pixu são links para o detalhe canônico, inclusive quando aparecem como **Você**. Os links usam token semântico com contraste legível nos dois temas. Convidados externos continuam texto simples, mesmo que o nome coincida com um `@username`; nenhuma conta é inferida pelo nome autodeclarado.
- Editar nome de exibição e chave Pix afeta somente o perfil da própria pessoa autenticada. A chave continua sendo fornecida pela pessoa e não é validada pelo Pixu.
- A preferência **Permitir inclusão direta em cobranças** pertence à própria conta, inicia desativada e pode ser alterada no perfil. No onboarding, um aviso recomenda considerar a ativação, mas não marca a opção por padrão. A preferência vale somente para cobranças criadas depois da alteração; desativá-la não desfaz participações já aceitas.

### Convites

- Listar convites pendentes com título, criador, recebedor, total, cota individual e participantes.
- Ações “Aceitar participação” e “Recusar convite” pedem confirmação por botão explícito e retornam o estado atualizado.
- Cobranças aguardando respostas exibem quantos convites ainda precisam de decisão.
- Uma participação recusada não aparece como dívida.
- Cobranças com entradas anônimas exibem um link compartilhado enquanto as entradas estão abertas; esse link não revela cotas antes de a pessoa informar seu nome.
- Cada entrada anônima gera uma identidade temporária e um código pessoal. Nomes iguais são permitidos e nunca são tratados como username ou prova de identidade.

### Criar cobrança

- Formulário com título, descrição opcional, valor total, seleção de um recebedor e busca de usuários cadastrados.
- A seleção múltipla de convidados usa checkbox de cantos arredondados (não toggle), com estado marcado em Sakura e tique contrastante. O cartão inteiro permanece clicável, com alvo confortável; foco de teclado é visível nos dois temas e a seleção não depende apenas da cor.
- O campo “Quem recebe” começa no usuário autenticado e permite escolher outra conta ativa. Receber não inclui automaticamente a pessoa no rateio.
- “Também participo do rateio” começa marcada; desmarcar exclui a cota do criador, mantendo sua autoria e acesso à cobrança. É necessário ao menos um participante.
- Oferecer “Permitir convidados anônimos por link”, com total explícito obrigatório de pessoas, limite editável e default de 10 entradas, além de validade de código pessoal default de 7 dias ou até quitar. O total inclui contas selecionadas e vagas anônimas; a cobrança pode nascer sem participantes convidados, mas o total declarado fixa a cota das vagas futuras.
- Mostrar prévia com campos de cota editáveis antes de salvar. A divisão inicial é igualitária e explica centavos residuais; a soma deve corresponder exatamente ao total. Alterar total ou participantes recalcula a divisão; erros de submissão preservam as cotas digitadas.
- “Conferir cotas” oferece a mesma revisão por POST convencional, inclusive sem JavaScript.
- Permitir editar a cota do criador e cotas pendentes até que a regra de bloqueio se aplique; cotas aceitas ficam visíveis como imutáveis.
- Depois de confirmar, mostrar “Aguardando aceite” quando houver convidados, ou “Ativa” se somente a participação do próprio criador já estiver aceita.
- Participantes com a preferência de inclusão direta ativada entram como aceitos em novas cobranças, sem convite individual; os demais seguem o convite e aceite existentes. A informação de que contas Pixu podem autorizar inclusão direta é apresentada no onboarding e explicada na preferência do perfil.
- Ao criar entradas anônimas, mostrar no resumo o link compartilhado e o código do link, com ação de gerar novo link. O link compartilhado deixa de aceitar nomes ao atingir o limite, ser revogado ou quando o criador fechar as entradas.

### Detalhe da cobrança

- **Cabeçalho:** título, criador, estado da cobrança e menu contextual de ações (`···`) no canto superior direito para o criador.
- **Divisão da Grid e Hierarquia Responsiva:**
  - **No Desktop (`lg:` e `xl:`):** Grid proporcional de duas colunas (`lg:grid-cols-[minmax(0,1.4fr)_minmax(19rem,1fr)]`):
    - **Coluna Principal (Esquerda ~60-65%):** Foco operacional vivo da conta:
      1. _Ação Imediata do Usuário_ (aceitar cota ou pagar se houver pendência);
      2. _Participantes e Cotas_ — na visão do recebedor, é a única lista operacional e incorpora saldo, Pix pendente e confirmação manual na linha da pessoa, sem uma lista financeira paralela.
    - **Sidebar de Apoio (Direita ~35-40%):** Painel de contexto limpo e respirado:
      1. _Resumo da Conta_ (Total, Quem recebe, Sua cota, Descrição);
      2. _Link da Mesa (Convidados Anônimos)_ (link compartilhado, ações de compartilhar e copiar, contador de entradas e opções rápidas).
  - **No Mobile (`< lg`):** Empilhamento vertical sequencial em blocos card bem ordenados:
    1. Participantes e Cotas, com a ação de confirmação que exige atenção no início da lista;
    2. Resumo da Conta;
    3. Link da Mesa, quando houver convidados anônimos.
- **Hierarquia aprovada de participantes e pagamentos (visão do recebedor):**
  - A primeira divisão da lista é sempre de identidade: **Contas Pixu** e **Convites Anônimos**. Cada pessoa aparece em um único grupo; não há uma segunda categoria global de “pagamentos aguardando”, “em aberto” ou “quitados”.
  - Dentro de cada grupo, a própria participação do recebedor fica identificada como cota própria. Os demais pagantes são ordenados por atenção: Pix pendente de confirmação pelo recebedor, saldo aberto sem Pix pendente e, por último, cota quitada. Uma participação que ainda aguarda aceite não parece uma dívida ativa.
  - A linha mostra nome, cota e estado textual. Quando houver itens extras, a cota discrimina a parcela base, cada item extra e o total em uma expressão aritmética exata; sem extras, mantém somente o total conciso. O atalho **Ver detalhes da cota** começa alinhado ao conteúdo da linha. A origem é comunicada pelo título do grupo, sem repetir badges de **Conta Pixu** ou **Usuário externo** em cada pessoa. O recebedor pode configurar, em cada dívida de conta Pixu, se futuros pagamentos declarados serão confirmados automaticamente. O controle explicita que não há verificação bancária, inclui pagamentos parciais e torna a confirmação final; convidados sem conta continuam na confirmação manual.
  - **“Em aberto há …”** é reservado a cotas sem nenhum pagamento iniciado e mede o tempo desde a criação da dívida. Não usar “atrasado”, vencimento, juros ou multa, pois a cobrança não tem data de vencimento neste fluxo. Saldos parciais ou com Pix rejeitado mostram o saldo restante, sem se passarem por pagamento não iniciado.
  - Pagamentos confirmados e compensações preservam seu histórico e seus comprovantes autorizados em detalhe sob demanda (modal no desktop e bottom sheet no celular); a compactação da lista não elimina auditoria ou acesso já permitido.
- **Menu Contextual de Ações do Criador (`···`):**
  - Eliminação de formulários secundários embutidos em sanfonas aninhadas (`<details><summary>`) na sidebar ("AI slope").
  - As ações do criador (_Adicionar item extra_, _Ajustar cotas / recebedor_, _Cancelar cobrança_) são acessadas pelo menu `···` no cabeçalho ou por gatilhos limpos na interface.
- **Padrão de Interação (Bottom Sheet no Mobile / Modal no Desktop):**
  - Para formulários rápidos de inclusão de consumos (_Adicionar item extra_), a interface dispara um **Bottom Sheet** deslizante a partir do rodapé no celular (`rounded-t-[28px]`, puxador superior, botões na área do polegar e sem colisão com o teclado virtual).
  - Em telas médias/largas (`sm:` e `lg:`), o mesmo componente transmuta responsivamente para um diálogo centralizado com backdrop suave (`sm:rounded-[24px] sm:max-w-md`).
  - Formulários extensos de redistribuição de cotas utilizam rotas/telas dedicadas com validação total no servidor.
- **Regras Operacionais e Financeiras:**
  - Lista de participantes com cota e estado de convite.
  - Para o criador, cada pagante mostra links dos comprovantes que anexou. A visualização é somente leitura e não dá ao criador, por si só, permissão para confirmar ou rejeitar pagamentos.
  - O recebedor decide entre confirmação manual (padrão) e confirmação automática em cada dívida elegível. A configuração não verifica comprovantes nem transfere dinheiro. Comprovantes autorizados abrem em prévia do navegador quando suportado pelo formato.
  - Para o criador, expor substituição após recusa e edição permitida de cotas.
  - O criador pode cancelar logicamente cobranças ativas ou aguardando aceite com motivo opcional. Antes de confirmar, informar que não haverá estorno; após cancelar, mostrar a cobrança e pagamentos revogados no histórico, com motivo, autor e data quando disponíveis. Convites pendentes ficam inválidos, sem ações de pagamento, aceite, compensação ou edição estrutural.
  - Se uma cobrança possuir compensação, explicar que ela não pode ser cancelada. Exclusão absoluta é uma ação administrativa exclusiva de superusuários, exige motivo opcional e auditoria mínima, e também é bloqueada quando há compensações; não a expor como ação comum do produto.
  - Permitir ao criador trocar o recebedor antes de qualquer aceite de outra pessoa e de operação financeira. Após esse limite, mostrar o recebedor sem edição e explicar o bloqueio. O recebedor tem acesso à cobrança mesmo sem participar do rateio, mas não recebe permissão de edição por esse papel.
  - Se o criador participa e escolhe outro recebedor, sua própria dívida é criada junto da cobrança e acompanha os ajustes permitidos de sua cota.
  - Para o destinatário, expor somente ações do convite destinado a ele.
  - Para uma pessoa convidada, a página pública mostra apenas título, total, seu nome autodeclarado, sua cota discriminada, chave Pix do recebedor e o formulário de pagamento. O código pessoal é mostrado uma vez e pode ser usado até quitar ou expirar.
  - O criador pode fechar as entradas explicitamente. Em cobranças legadas sem total fixo, cada convidado confirma sua cota depois do fechamento; no modo anônimo com total declarado, a pessoa pode confirmar e pagar imediatamente enquanto o link segue aberto. Se alguém não confirmar e nenhum pagamento existir, o criador pode reabrir e recalcular.
  - Exibir ações de pagamento e compensação conforme o papel financeiro e o estado da dívida, seguindo os fluxos descritos na seção 8.

### Estrutura para desktop

- A partir de `lg`, usar uma navegação vertical fixa à esquerda, com marca, Início (dashboard), cobranças, convites e perfil. O contador de convites pendentes continua visível.
- A partir de `lg`, remover o enquadramento de telefone, o fundo escuro externo e a navegação inferior. A área principal ocupa o espaço restante e alinha o conteúdo em uma largura máxima confortável.
- No celular, manter cabeçalho compacto e navegação inferior fixa com Início, Cobranças, Convites e Perfil. A navegação inferior respeita a área segura e nunca cobre ações ou conteúdo.
- Listas de cobranças e convites podem usar duas colunas em `md` e três em `xl`.
- O detalhe da cobrança organiza a tela em duas colunas proporcionais a partir de `lg` (`~60%` atividade operacional à esquerda e `~35-40%` sidebar de resumo/link à direita), eliminando o desnível de altura e o espaço morto. Formulários secundários usam o menu contextual `···` e bottom sheets/diálogos modais responsivos.
- A página pública de entrada não mostra a navegação autenticada; em telas largas, apresenta a chamada principal e os benefícios em duas colunas.

## 4. Componentes e linguagem

- **Botão primário:** uma ação principal por formulário; altura mínima de 44px.
- **Botão secundário:** voltar, cancelar ou ação menos frequente.
- **Campo de formulário:** rótulo persistente, exemplo curto, ajuda e erro associados via `aria-describedby`.
- **Badge de estado:** rótulo textual além da cor: “Pendente”, “Aceito”, “Recusado”, “Aguardando aceite”, “Ativa”, “Cancelada” e “Revogado”.
- **Cartão de participante:** nome, cota, estado e ação que a pessoa tem permissão para executar.
- **Resumo de cotas:** mostra somente as pessoas incluídas, cada valor editável na criação e a soma final; distingue criador, recebedor e participantes.
- **Aviso informativo:** explica confirmação de e-mail, origem da chave Pix ou efeito do aceite sem tom alarmista.
- **Menu contextual de ações (`···`):** botão discreto de 36px/40px com três pontos e foco visível; no clique, abre menu dropdown flutuante com as ações secundárias da cobrança, evitando a proliferação de sanfonas aninhadas na interface principal.
- **Bottom Sheet / Diálogo responsivo:** painel para formulários rápidos auxiliares (como inclusão de itens extras). Em telas móveis (`< sm`), surge como gaveta deslizante pelo rodapé (`bottom-0`, cantos superiores `rounded-t-[28px]`, puxador tátil de 48px e ações na zona ergonômica do polegar, prevenindo colisão com o teclado virtual); a partir de `sm`, comporta-se como modal centralizado elegante com backdrop translúcido.

Tom direto e acolhedor. Preferir “Sua participação foi aceita” a mensagens genéricas como “Sucesso”. A interface não deve sugerir transferência, verificação bancária ou confirmação automática pelo Pixu.

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

A primeira versão continua online. Páginas, convites e dados de cobrança vêm do servidor; criar, editar, aceitar ou recusar exige conexão. A interface só confirma uma mudança depois da resposta do servidor. O shell pode ser instalado como PWA, mas não há cache de dados pessoais, rascunhos locais ou fila de ações offline. Suporte offline exigiria mudança OpenSpec própria para sincronização, idempotência e conflitos.

A persistência da preferência visual de tema, descrita na seção 2.4, armazena somente a escolha de aparência. Ela não habilita uso offline nem armazenamento de contas, cobranças ou formulários no navegador.

## 8. Pagamentos e compensações

Estes padrões orientam as telas financeiras implementadas em mudanças OpenSpec próprias:

- Pagamento Pix fica pendente até a decisão manual do recebedor por padrão; quando a confirmação automática estiver ativada para aquela dívida, declarações futuras de uma conta autenticada são confirmadas após validação. Comprovante não é tratado como verificação.
- O criador da cobrança pode consultar em modo de leitura os comprovantes anexados pelos pagantes enquanto os registros de pagamento permanecerem no histórico. Somente o recebedor confirma ou rejeita.
- Cancelamento lógico revoga pagamentos e invalida convites, preservando cobrança, pagamentos e comprovantes no histórico; não desfaz transferências externas nem recria dívidas. Cobranças com compensações não podem ser canceladas ou excluídas.
- Um pagamento pertence a uma dívida. Pagamentos parciais são mostrados em linhas próprias.
- Saldo aberto e valor reservado por Pix pendente aparecem separadamente.
- A compensação é uma ação explícita sobre duas dívidas recíprocas; sugestão de compensação não é dinheiro disponível em conta.
- Não há confirmação automática por confiança nem transferência única alocada a várias cobranças nesta versão do brief.

## 9. Entregáveis da revisão

- Wireframes e matriz de estados: `docs/design/pixu-first-vision-wireframes.md`.
- Protótipo navegável local dos fluxos financeiros: `docs/design/pixu-first-vision-prototype.html`.
- Protótipo navegável de autenticação SSO (Google e GitHub) e onboarding de chave Pix: `docs/design/pixu_sso_onboarding_prototype.html`.
- Protótipo navegável da refatoração da grid de cobrança, menu contextual e bottom sheet: `docs/design/pixu_charge_detail_grid_refactor_prototype.html`.
- Este documento define os tokens, componentes, textos, responsividade, acessibilidade e padrões HTMX/Tailwind.

Decisões desta revisão: “convite pendente”, “cobrança ativa” e “dívida criada” são estados distintos; a navegação e a composição do desktop são próprias, sem moldura de celular; o detalhe da cobrança passa a ter proporções equilibradas (sidebar operacional limpa e sem acordeons aninhados, menu contextual `···` e bottom sheet responsivo para formulários rápidos auxiliares); esta versão exige conexão para qualquer ação que altere estado. O protótipo e os wireframes foram atualizados para refletir a navegação lateral em telas largas. A hierarquia semântica está documentada e implementada; ainda falta verificar com três pessoas a compreensão espontânea de “Pix pendente”, “saldo aberto” e “compensado”.
