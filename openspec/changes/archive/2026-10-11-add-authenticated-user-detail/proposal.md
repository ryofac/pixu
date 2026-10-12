# Proposal

## Why

Hoje o detalhe de uma cobrança apresenta nomes de contas Pixu como texto sem caminho para conhecê-las, e o perfil só mostra a própria chave Pix. Isso impede que pessoas autenticadas consultem uma identidade Pixu, sua chave informada e o histórico de cobranças que realmente compartilham.

## What Changes

- Criar uma página de detalhe de conta autenticada, reutilizando a rota canônica por `@username`, com identidade da pessoa, chave Pix principal e a lista de cobranças que ela compartilha com quem consulta.
- Tornar a chave Pix da conta-alvo visível para **qualquer pessoa autenticada** que acesse esse endpoint; a chave continua sendo texto declarado pela titular e não verificado pelo Pixu.
- Restringir a lista de cobranças ao cruzamento das cobranças que a pessoa visitante e a conta-alvo podem consultar, sem vazar participações, saldos, comprovantes ou dados de terceiros.
- Transformar as identidades de contas Pixu no detalhe autenticado de uma cobrança em links para esse perfil. Nomes de convidados externos continuam texto simples, sem rota de perfil.
- Preservar as ações privadas do próprio perfil (editar perfil, e-mail e sair) somente para sua titular e não mudar as regras dos pagamentos, convites por link ou comprovantes.

## Capabilities

### New Capabilities

- `accounts/user-details`: perfil de conta acessível após autenticação, com chave Pix declarada e cobranças em comum sem extrapolar a autorização da cobrança.

### Modified Capabilities

- `charges`: o detalhe autenticado da cobrança passa a navegar das identidades de contas Pixu para seu perfil, mantendo convidados externos sem link.

## Impact

- Afeta a consulta e o template de `accounts:detail`, as consultas de cobranças compartilhadas e os testes de autenticação, isolamento e ausência de chave.
- Afeta os fragmentos e contextos do detalhe de cobrança que exibem criador, recebedor e participantes cadastrados, além de seus testes de interface e acessibilidade.
- Não cria migração, não introduz dependências, não altera valores monetários, estados financeiros, autorização de comprovantes nem acessos de convidados.
