# Design

## Context

Ver `proposal.md` para a motivação e os deltas de especificação para o contrato observável. A rota `accounts:detail` já resolve uma conta por `@username`, exige sessão e hoje reutiliza o template de perfil: para outra conta mostra apenas identidade; para a própria conta mostra chave Pix e ações privadas. O detalhe autenticado de cobrança já diferencia participações com `user` de entradas convidadas sem conta, mas renderiza as identidades como texto.

`Charge` relaciona contas Pixu por três vias: `creator`, `creditor` e `Participation.user`. A consulta de visibilidade de cobranças existente usa exatamente essas três relações e deve continuar sendo a definição de autorização para cada detalhe de cobrança. A aplicação usa Django templates, HTMX quando necessário e Tailwind compilado localmente; temas claro/escuro, navegação fixa e os tokens semânticos de `docs/product-design.md` já fazem parte do produto.

## Goals / Non-Goals

**Goals:**

- Transformar o detalhe de conta existente em um perfil autenticado útil, sem uma rota concorrente, API pública ou modelo adicional.
- Separar visualmente identidade, chave Pix e cobranças em comum para que a exposição aprovada seja fácil de entender e auditar.
- Centralizar a consulta de interseção de cobranças para que a página jamais use uma regra de visibilidade mais permissiva que a do detalhe da cobrança.
- Fazer as pessoas cadastradas no detalhe de uma cobrança navegáveis, preservando a distinção entre contas Pixu e convidados externos.

**Non-Goals:**

- Não criar busca pública de usuários, diretório de contas, seguidores, mensagens, contatos, QR Code, validação bancária ou integração Pix.
- Não expor e-mail, comprovantes, pagamentos, saldos, cotas, lista de terceiros, dados de convite ou credenciais de convidado no perfil.
- Não modificar as permissões de pagamento, comprovante, convite ou detalhe da cobrança; seguir um link nunca concede autorização adicional.
- Não produzir nem registrar como aprovado um protótipo visual antes da confirmação da pessoa usuária.

## Decisions

### Reutilizar `accounts:detail` como detalhe canônico

A rota por `@username` existente continuará sendo o único destino para o perfil. O contexto distinguirá a própria conta (`Meu perfil`) de outra conta (`Perfil de {nome}`), sem duplicar URLs ou templates. A titular preserva os controles privados atuais; o perfil de outra conta é inteiramente de leitura.

Alternativas consideradas:

- Criar `/p/<username>/` em paralelo: rejeitada porque duplicaria identidade, autorização e URLs canônicas sem benefício de navegação.
- Converter o próprio perfil em rota separada: rejeitada para evitar regressão de links, navegação e formulários existentes.

### Autenticação é o limite de acesso à chave Pix do perfil

Conforme decisão explícita do produto, qualquer sessão autenticada que alcance `accounts:detail` verá a chave Pix não vazia da conta-alvo e o aviso de que ela é declarada, não verificada. Não será exigida cobrança em comum para essa parte da página. Sem sessão, `LoginRequiredMixin` continuará protegendo a rota antes de renderizar qualquer dado; perfis inexistentes seguem como 404.

Esta decisão é intencionalmente mais ampla do que a exibição contextual da chave durante o registro de pagamento. Ela não altera as regras daquela tela nem dá direito de registrar, confirmar ou consultar uma dívida. Chave ausente terá estado neutro e nunca uma chave substituta.

Alternativa considerada:

- Restringir a chave a pessoas que compartilham cobrança: rejeitada pela decisão confirmada de que a autenticação basta para o endpoint de detalhe.

### Cobranças em comum são uma interseção de visibilidades já autorizadas

A página de outra conta receberá um único queryset de `Charge` que satisfaça, ao mesmo tempo, as três relações de visibilidade para a visitante e para a conta-alvo: criadora, recebedora ou `Participation.user`. A consulta usará `distinct()` por causa dos joins de participações e carregará relações necessárias de uma vez para impedir N+1. A ordenação continuará compatível com o histórico atual de cobranças.

O cartão de cada cobrança em comum mostra apenas título, estado textual e um link ao detalhe regular; nenhuma relação de participação adicional será serializada no contexto. Ao navegar, o `ChargeDetailView` executará sua autorização normal novamente. A própria conta não recebe a seção de cobranças em comum, pois ela não representa uma relação entre duas pessoas e o escopo não pede uma nova listagem de todas as cobranças pessoais.

Alternativas consideradas:

- Listar toda cobrança da conta-alvo: rejeitada por vazar títulos e contexto a pessoas autenticadas sem relação com a cobrança.
- Basear a lista só em participações aceitas: rejeitada porque criador, recebedor e participações ainda pendentes já possuem acesso legítimo à cobrança em outros fluxos.
- Calcular a interseção no template: rejeitada porque autorização e filtro precisam ocorrer no servidor antes da renderização.

### Hierarquia da página e comportamento responsivo

Antes de codificar a tela, a Wave 0 produzirá um protótipo HTML isolado para revisão, sem modificar `docs/product-design.md` como decisão aprovada. A composição proposta para esse protótipo e para a implementação posterior é:

1. cabeçalho com título contextual e retorno previsível à origem de navegação;
2. cartão de identidade com inicial, nome e `@username`;
3. cartão de chave Pix com valor quebrável, aviso de origem e ação discreta de copiar quando houver chave; ou estado vazio quando não houver;
4. somente para outra conta, seção de largura completa “Cobranças em comum”, com linhas compactas de título, estado textual e seta de navegação, ou estado vazio neutro.

O perfil de outra conta não inclui um aviso textual de “somente leitura”: a ausência de ações de edição já comunica esse estado sem repetir informação. Quando há uma chave Pix, a ação textual “Copiar chave Pix” fica junto ao valor no cartão, com alvo mínimo de 44 px, foco visível e confirmação após copiar; a ação não aparece no estado sem chave.

Em telas largas, os cartões de identidade e chave compartilham a primeira faixa em duas colunas de proporções estáveis, e a lista ocupa a largura abaixo. Em mobile, a ordem acima empilha sem scroll horizontal. A página respeita o recuo da navegação inferior e a área segura; links de pessoas e linhas de cobrança mantêm alvo de toque de pelo menos 44 px, contraste por tokens `pixu-*`, foco visível e não dependem de cor para informar estado. Nenhum hex ou variante `dark:` avulsa será introduzido: a tela usa os tokens já cobertos pelos dois temas.

Alternativas consideradas:

- Colocar cobranças e chave dentro do cartão de identidade: rejeitada porque reduz escaneabilidade e mistura dado de pagamento com histórico compartilhado.
- Exibir indicadores financeiros na lista comum: rejeitada por aumentar exposição e competir com a função de navegação contextual.

### Links somente para identidades registradas da cobrança

Os contextos/fragmentos que exibem criadora, recebedora e `Participation.user` no detalhe autenticado de cobrança usarão `accounts:detail` para a conta correspondente, inclusive quando o rótulo visível for “Você”. O link mantém o texto que já identifica a pessoa e é um elemento `<a>` sem aninhar botões ou quebrar os modais existentes.

Entradas cujo `Participation.user` é nulo são convidadas externas: o texto do nome permanece não interativo, ainda que coincida visualmente com um `@username`. A implementação não fará busca por nome para tentar convertê-las em conta e não usará URLs de convite nessa navegação.

Alternativa considerada:

- Linkar apenas participantes e não criador/recebedor: rejeitada pois criadora e recebedora também são contas Pixu visíveis no mesmo detalhe.

### Cobertura e documentação de design após a revisão do protótipo

Após a confirmação explícita do protótipo da Wave 0, `docs/product-design.md` receberá somente as regras estáveis: título/contexto do perfil, cartões de identidade e Pix, limite da seção “Cobranças em comum”, links de contas Pixu e tratamento de convidado externo. O protótipo será uma referência de composição, não um template servido. Esta mudança não declara o entregável visual como concluído antes dessa confirmação.

## Risks / Trade-offs

- [Uma chave Pix é dado sensível para parte das pessoas usuárias] → a decisão de acesso amplo entre sessões autenticadas fica explícita na especificação, sem cache público, e a página não expõe e-mail ou outros dados de contato.
- [Join de participação pode duplicar cobranças ou crescer com o histórico] → aplicar a interseção no banco, usar `distinct()`, relações pré-carregadas e testes com mais de uma participação relacionada.
- [Um atalho de perfil pode dar a impressão de acesso à cobrança] → o perfil lista apenas títulos/estados compartilhados e cada destino executa novamente a autorização de cobrança.
- [Nomes de convidados podem coincidir com contas reais] → o vínculo usa exclusivamente `Participation.user`; nunca o texto de `guest_name`.
- [Navegação fixa pode encobrir foco ou alvo no celular] → validar com teclado e viewports mobile, mantendo padding da área segura e foco visível, conforme a diretriz de foco não obscurecido.

## Migration Plan

Não há alteração de banco nem migração de dados. A entrega adicionará as consultas, templates e links em uma implantação normal; se houver regressão, o rollback do código restaura o perfil atual e remove os links sem tocar em contas, cobranças, chaves Pix ou histórico financeiro. Caso novas classes Tailwind sejam necessárias, o CSS compilado seguirá o build local já usado pelo projeto.

## Open Questions

Nenhuma. A regra de visibilidade da chave Pix foi definida: qualquer pessoa autenticada que alcance o detalhe de uma conta pode vê-la; cobranças permanecem restritas à interseção de acesso das duas contas.
