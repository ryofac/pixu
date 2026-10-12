# Spec Delta

## ADDED Requirements

### Requirement: Navegação para perfis de contas Pixu no detalhe da cobrança

No detalhe autenticado de uma cobrança, toda identidade exibida de uma conta Pixu — criadora, recebedora ou participante cadastrado, inclusive a própria pessoa quando identificada como “Você” — MUST ser um link para o detalhe daquela conta. O link MUST preservar um nome acessível, foco visível e a mesma autorização do detalhe de perfil. Nomes de convidados externos MUST permanecer texto simples: o sistema MUST NOT inferir uma conta pelo nome autodeclarado nem oferecer perfil, `@username` ou rota de conta para eles.

#### Scenario: Participante cadastrado abre seu perfil a partir da cobrança

- **WHEN** uma pessoa autenticada consulta uma cobrança que mostra outra participante cadastrada
- **THEN** o nome daquela participante é um link para seu detalhe de conta autenticado

#### Scenario: Identidade da própria pessoa permanece navegável

- **WHEN** uma pessoa autenticada consulta uma cobrança em que aparece como criadora, recebedora ou participante
- **THEN** sua identificação, inclusive quando o texto visível é “Você”, permite abrir seu próprio perfil

#### Scenario: Convidado externo permanece sem perfil Pixu

- **WHEN** uma cobrança mostra uma participação de convidado externo, mesmo que o nome autodeclarado coincida com um `@username` existente
- **THEN** o nome permanece sem link de perfil e nenhum dado da conta coincidente é exposto
