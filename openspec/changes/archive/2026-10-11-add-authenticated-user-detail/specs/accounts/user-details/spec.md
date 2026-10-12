# Spec Delta

## Purpose

Permite consultar, com sessão autenticada, a identidade declarada de uma conta Pixu e o contexto de cobranças que ela compartilha com quem faz a consulta.

## ADDED Requirements

### Requirement: Detalhe autenticado de conta Pixu

O sistema MUST disponibilizar o detalhe de uma conta Pixu pelo seu `@username` somente para pessoas autenticadas. O detalhe MUST identificar a conta-alvo pelo nome de exibição e `@username`; pessoas autenticadas sem qualquer cobrança em comum também podem consultar essa identidade. Uma conta inexistente MUST continuar indisponível, e uma pessoa sem sessão MUST ser direcionada ao login sem receber os dados do perfil.

#### Scenario: Pessoa autenticada consulta uma conta sem cobrança em comum

- **WHEN** uma pessoa autenticada abre o detalhe de uma conta Pixu existente com a qual não compartilha cobrança
- **THEN** ela vê o nome e o `@username` da conta, sem receber títulos ou dados de cobranças alheias

#### Scenario: Visitante tenta consultar uma conta Pixu

- **WHEN** uma pessoa sem sessão abre a URL de detalhe de uma conta existente
- **THEN** o sistema a direciona ao login antes de renderizar nome, `@username`, chave Pix ou cobranças

#### Scenario: Username desconhecido é consultado

- **WHEN** uma pessoa autenticada abre o detalhe de um `@username` inexistente
- **THEN** o sistema responde como recurso não encontrado sem renderizar um perfil substituto

### Requirement: Chave Pix declarada no detalhe autenticado

A chave Pix principal de uma conta MUST aparecer para qualquer pessoa autenticada que acesse o detalhe daquela conta, quando houver chave não vazia cadastrada. A tela MUST informar que a chave foi declarada pela titular e não é verificada pelo Pixu, e MUST oferecer uma ação para copiar a chave junto ao valor exibido. A ação de cópia MUST existir somente quando houver uma chave não vazia. A ausência de chave MUST ser comunicada sem inventar ou validar um valor; a chave nunca pode ser revelada a visitante sem sessão.

#### Scenario: Pessoa autenticada vê a chave Pix de outra conta

- **WHEN** uma pessoa autenticada abre o detalhe de uma conta com chave Pix principal cadastrada
- **THEN** a chave atual e o aviso de que ela não é verificada pelo Pixu ficam visíveis, mesmo sem cobrança em comum

#### Scenario: Pessoa autenticada copia a chave Pix exibida

- **WHEN** uma pessoa autenticada abre o detalhe de uma conta com chave Pix principal cadastrada
- **THEN** uma ação identificada como “Copiar chave Pix” aparece junto ao valor e copia exatamente a chave exibida

#### Scenario: Conta sem chave Pix é consultada

- **WHEN** uma pessoa autenticada abre o detalhe de uma conta que ainda não cadastrou chave Pix
- **THEN** a tela informa a ausência da chave e não exibe valor de outra conta nem ação de cópia ou pagamento

### Requirement: Cobranças em comum sem vazamento de contexto

O detalhe de outra conta MUST listar somente as cobranças às quais tanto a pessoa visitante quanto a conta-alvo já têm acesso como criadora, recebedora ou participante cadastrada. Cada item listado MUST se limitar à identificação e ao estado da cobrança, com caminho para o detalhe já autorizado da própria cobrança; títulos, participantes, cotas, saldos, pagamentos, comprovantes ou links de cobranças fora dessa interseção MUST NOT ser expostos. O detalhe da própria conta MUST preservar suas ações privadas de perfil e não precisa transformar essa área em uma listagem de cobranças.

#### Scenario: Duas contas compartilham uma cobrança

- **WHEN** a pessoa autenticada abre o detalhe de uma conta que participa da mesma cobrança que ela
- **THEN** a cobrança compartilhada aparece com seu título e estado, e seu link leva ao detalhe normal da cobrança

#### Scenario: Cobranças sem relação não aparecem

- **WHEN** a conta-alvo possui uma cobrança à qual a pessoa visitante não tem acesso
- **THEN** essa cobrança não aparece no perfil, mesmo que a visitante conheça o `@username` da conta-alvo

#### Scenario: Não há cobranças em comum

- **WHEN** a pessoa autenticada abre um perfil sem cobranças compartilhadas
- **THEN** a tela mostra um estado vazio neutro e continua mostrando somente a identidade e, se houver, a chave Pix permitida

### Requirement: Ações privadas permanecem da própria conta

Somente a titular do perfil MUST ver as ações de editar perfil, gerenciar e-mail e sair da conta. Quem consulta outra conta MUST receber uma página de leitura e não pode alterar dados, e-mail, sessão ou chave Pix da conta-alvo.

#### Scenario: Titular abre o próprio perfil

- **WHEN** uma pessoa autenticada abre o detalhe do seu próprio `@username`
- **THEN** ela continua vendo as ações privadas existentes para editar seu perfil, gerenciar e-mail e encerrar a sessão

#### Scenario: Outra pessoa abre o perfil

- **WHEN** uma pessoa autenticada abre o detalhe de outra conta
- **THEN** ela não vê controles de edição, e-mail ou sessão da conta-alvo
