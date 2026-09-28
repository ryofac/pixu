# landing-page Specification

## Purpose

Apresenta o Pixu a visitantes sem autenticação e oferece caminhos claros para cadastro e login, preservando o acesso à área autenticada na mesma rota inicial.

## Requirements

### Requirement: Apresentação pública do Pixu

Visitantes não autenticados que acessarem a rota inicial MUST ver uma landing page em pt-BR com a marca aprovada, uma chamada principal sobre rateio, descrição breve do fluxo, ações reais de cadastro e login e benefícios do produto. A página MUST explicar rateio e aceite sem expor dados privados nem sugerir transferência, confirmação automática ou quitação pelo Pixu.

#### Scenario: Visitante abre a página inicial

- **WHEN** uma pessoa não autenticada acessa a rota inicial
- **THEN** a página mostra a apresentação pública, o botão de criar conta e o caminho para entrar na conta

#### Scenario: Ações encaminham para autenticação

- **WHEN** a pessoa seleciona criar conta ou entrar
- **THEN** o sistema navega para os fluxos reais de cadastro ou login, sem links de demonstração

#### Scenario: Conteúdo não expõe dados financeiros privados

- **WHEN** um visitante consulta a landing page
- **THEN** os exemplos são claramente ilustrativos e não revelam cobranças, pagamentos ou comprovantes de usuários reais

### Requirement: Apresentação responsiva e movimento decorativo

A landing page MUST manter chamada e ações legíveis em mobile e desktop: em telas estreitas o conteúdo e os botões ficam em uma coluna; em telas largas, chamada e ilustração podem ocupar colunas próprias. Decorações e animações MUST ser não interativas, não bloquear o conteúdo e respeitar `prefers-reduced-motion`.

#### Scenario: Página em viewport móvel

- **WHEN** o visitante acessa a página em viewport estreito
- **THEN** chamada, cadastro e login permanecem visíveis e alcançáveis sem overflow horizontal, enquanto a ilustração decorativa pode ser omitida

#### Scenario: Página em viewport desktop

- **WHEN** o visitante acessa a página em viewport largo
- **THEN** chamada e ilustração aparecem em composição equilibrada sem enquadramento de telefone

#### Scenario: Movimento reduzido

- **WHEN** o sistema operacional indica preferência por movimento reduzido
- **THEN** pétalas, flutuação e transições decorativas são removidas ou reduzidas sem esconder conteúdo

### Requirement: Área autenticada preservada na rota inicial

Uma pessoa autenticada que acessa a rota inicial MUST receber seu dashboard e não a apresentação pública. Cobranças e demais dados privados MUST permanecer protegidos pelas autorizações existentes.

#### Scenario: Pessoa autenticada abre a página inicial

- **WHEN** uma pessoa autenticada acessa a rota inicial
- **THEN** o sistema mostra o dashboard personalizado, sem os CTAs públicos de cadastro e login

### Requirement: Narrativa funcional em rolagem

A landing page MUST apresentar em pt-BR uma narrativa curta distribuída em três seções verticais sequenciais, alcançáveis por rolagem comum em mobile e desktop, sem travar, capturar ou forçar a rolagem. As seções MUST explicar: criar rateios, convidar e aceitar cotas; acompanhar pagamentos realizados fora do Pixu, comprovantes e confirmação manual; e consultar saldos, compensações e histórico, incluindo o cancelamento lógico pelo criador. O conteúdo MUST usar exemplos abstratos que correspondam a ações reais, MUST NOT usar as palavras “demo” ou “demonstração” e MUST NOT anunciar funções ainda indisponíveis. O conteúdo MUST permanecer legível nos temas claro e escuro, preservar a marca, e manter visíveis os caminhos reais de cadastro e login.

#### Scenario: Visitante percorre a narrativa em mobile

- **WHEN** um visitante sem autenticação percorre a landing page em viewport móvel
- **THEN** encontra as três seções em ordem, com todo conteúdo e ações alcançáveis por rolagem normal, sem overflow horizontal nem seção escondida

#### Scenario: Visitante percorre a narrativa em desktop

- **WHEN** um visitante sem autenticação percorre a landing page em viewport desktop
- **THEN** as três seções formam uma sequência visual coerente e mantêm cadastro e login acessíveis, sem captura da rolagem

#### Scenario: Fluxos financeiros são descritos corretamente

- **WHEN** a seção sobre pagamento é apresentada
- **THEN** ela deixa claro que a transferência ocorre fora do Pixu, que o comprovante pode ser consultado por pessoas autorizadas e que somente o recebedor confirma ou rejeita o pagamento

#### Scenario: Exemplos abstratos sem promessas indisponíveis

- **WHEN** a landing page apresenta elementos visuais de cobranças ou pagamentos
- **THEN** eles não expõem dados reais, não se descrevem como “demo” ou “demonstração” e representam somente funcionalidades existentes na aplicação

#### Scenario: Seções permanecem legíveis nos dois temas

- **WHEN** o visitante alterna entre os temas claro e escuro
- **THEN** as seções, os exemplos abstratos e as ações preservam contraste, hierarquia e legibilidade
