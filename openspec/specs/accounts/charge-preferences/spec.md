# charge-preferences Specification

## Purpose

Permite que cada pessoa controle uma preferência própria para aceitar inclusão direta em cobranças futuras, preservando a escolha individual e sem alterar participações já existentes.

## Requirements

### Requirement: Preferência própria para inclusão direta em cobranças

Cada conta MUST poder ativar ou desativar, somente para si, a permissão de ser incluída diretamente em novas cobranças por outras contas Pixu. A preferência MUST iniciar desativada, ser explicada no onboarding com recomendação para considerar sua ativação e poder ser alterada no perfil. A interface MUST deixar claro que a preferência permite inclusão sem convite ou aceite individual e que cotas seguem as regras da cobrança. A preferência MUST afetar somente novas cobranças; alterá-la MUST NOT reverter, recusar ou remover participações já aceitas.

#### Scenario: Conta nova recebe recomendação sem ativação implícita

- **WHEN** uma pessoa conclui seu onboarding com a preferência ainda desativada
- **THEN** ela recebe uma recomendação para considerar permitir inclusão direta e a preferência permanece desativada até ação explícita no perfil

#### Scenario: Titular ativa a preferência no perfil

- **WHEN** uma pessoa autenticada ativa a permissão em seu próprio perfil
- **THEN** novas cobranças podem incluí-la diretamente, sem convite individual, e sua preferência fica identificável como ativada

#### Scenario: Preferência não pode ser alterada por outra conta

- **WHEN** o criador de uma cobrança tenta definir ou alterar a preferência de uma pessoa selecionada
- **THEN** a requisição é recusada e somente a titular pode modificar sua própria configuração

#### Scenario: Desativação não altera cobranças existentes

- **WHEN** uma pessoa desativa a preferência depois de já ter sido incluída e aceita em uma cobrança
- **THEN** a participação existente permanece aceita e qualquer efeito financeiro segue as regras atuais daquela cobrança
