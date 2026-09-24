## Why

O scaffold Django já existe, mas ainda não permite que uma pessoa crie uma conta e estabeleça obrigações compartilhadas. A primeira mudança torna utilizáveis os fluxos de conta e de cobrança, com convites consentidos e rateio exato antes de avançar para pagamentos.

## What Changes

- Habilitar cadastro público, login/logout, recuperação de senha por e-mail e edição de perfil e chave Pix fornecida pelo usuário.
- Criar cobranças com título, descrição opcional, valor em centavos, participantes existentes, prévia de divisão igualitária e edição manual de cotas.
- Modelar convites pendentes, aceitos e recusados; permitir substituição de participante recusado antes da primeira operação financeira.
- Criar cada dívida uma única vez no aceite e ativar a cobrança somente depois que todos os convites ativos forem aceitos.
- Implementar páginas e fragmentos HTMX responsivos conforme `docs/product-design.md`, usando o build local de Tailwind já preparado no scaffold.
- Aplicar CSRF, validação no backend, autorização por objeto, escape e limites de texto nos formulários desta mudança.
- Deixar comprovantes privados, pagamentos, compensações e dashboard para as mudanças posteriores definidas no brief.

## Capabilities

### New Capabilities

- `accounts`: cadastro público, autenticação, recuperação de acesso e edição do perfil do usuário.
- `charges`: criação, divisão, convites/participações, ativação da cobrança e geração idempotente de dívidas.

### Modified Capabilities

- Nenhuma. Ainda não existem especificações de capacidade em `openspec/specs/`.

## Impact

- Apps Django `pixu/accounts/` e `pixu/charges/`, hoje com autenticação básica e esqueleto de cobranças; configurações do Django e do allauth em `config/settings/`; URLs, templates e fragmentos HTMX.
- PostgreSQL, migrações e constraints para participações únicas, cotas em centavos e dívidas criadas uma única vez.
- Configuração de cadastro e e-mail por ambiente. A chave Pix é informada pelo titular; sua leitura pelo participante de uma dívida pertence ao lote R03.
- `docs/product-design.md` é pré-requisito para implementar as telas. Upload de arquivos e requisitos de armazenamento privado de comprovantes ficam no lote de pagamentos, embora os controles de formulários desta mudança atendam à parte aplicável de R16.
