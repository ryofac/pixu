# theme-preferences Specification

## Purpose

Permite que cada pessoa escolha uma aparência clara, escura ou acompanhando o sistema, mantendo leitura, navegação e formulários utilizáveis em todas as telas do produto.

## Requirements

### Requirement: Preferência Claro, Escuro ou Sistema

O produto MUST disponibilizar um seletor acessível de aparência com as opções Claro, Escuro e Sistema em páginas públicas e autenticadas. Sistema MUST ser a escolha inicial; escolhas explícitas MUST prevalecer sobre a configuração do dispositivo. A preferência visual MUST ser guardada somente no navegador e não pode armazenar dados pessoais ou financeiros.

#### Scenario: Primeira visita acompanha o sistema

- **WHEN** não existe preferência de aparência salva
- **THEN** a aplicação usa a aparência atual do sistema operacional

#### Scenario: Escolha explícita persiste no navegador

- **WHEN** a pessoa escolhe Claro ou Escuro e navega entre páginas ou recarrega a aplicação
- **THEN** a aparência escolhida permanece ativa sem ser sincronizada com a conta ou outro dispositivo

#### Scenario: Sistema retoma acompanhamento automático

- **WHEN** a pessoa escolhe Sistema e a aparência do dispositivo muda com a página aberta
- **THEN** a interface acompanha a nova aparência do dispositivo

#### Scenario: Armazenamento local indisponível

- **WHEN** o navegador impede leitura ou gravação da preferência local
- **THEN** a página continua utilizável, permite selecionar uma aparência durante a sessão e não falha por causa do armazenamento

### Requirement: Aplicação sem flash e fallback progressivo

A aparência escolhida MUST ser aplicada antes da primeira pintura quando a preferência puder ser lida. Sem JavaScript, ou sem preferência salva, a página MUST continuar legível e usar CSS para acompanhar o sistema, com tema claro como fallback quando a preferência do sistema não estiver disponível.

#### Scenario: Preferência salva evita flash

- **WHEN** existe uma preferência explícita salva no navegador e a página carrega
- **THEN** a primeira pintura visível já usa a aparência escolhida

#### Scenario: JavaScript desativado

- **WHEN** a pessoa navega com JavaScript desativado
- **THEN** conteúdo, ações e formulários permanecem utilizáveis e a aparência acompanha o sistema por CSS quando disponível

### Requirement: Cobertura consistente dos temas

As páginas públicas, autenticação, perfil, formulários, cobranças, convites, pagamentos, compensações, dashboard e fragmentos HTMX MUST oferecer aparência clara e escura legíveis. O seletor MUST comunicar a opção atual, funcionar por teclado e não depender somente de cor para estados, mensagens ou foco. Trocar tema MUST preservar campos preenchidos e estado da página.

#### Scenario: Tema cobre página e fragmento HTMX

- **WHEN** um fragmento HTMX substitui conteúdo enquanto a pessoa usa tema Escuro
- **THEN** o conteúdo atualizado mantém o mesmo tema, contraste e foco visível

#### Scenario: Troca de tema preserva formulário

- **WHEN** a pessoa muda a preferência enquanto um formulário contém valores digitados
- **THEN** a aparência muda sem limpar ou alterar os dados do formulário

#### Scenario: Seletor por teclado

- **WHEN** a pessoa navega até o seletor usando teclado
- **THEN** ela identifica a opção atual, altera entre as três opções e mantém foco visível
