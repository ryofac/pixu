# Spec Delta

## ADDED Requirements

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
