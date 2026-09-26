# Proposal

## Why

Depois de criar e aceitar cobranças, o Pixu ainda não registra a etapa em que o devedor informa um Pix nem permite ao recebedor conferir o recebimento. Sem esse fluxo, o saldo permanece apenas uma obrigação teórica e o produto não consegue preservar pagamentos parciais, reservas, comprovantes privados e o histórico de confirmação.

A validação autenticada também encontrou inconsistências de idioma, formatação monetária e composição responsiva nas telas públicas, de conta, cobrança e pagamento. Elas precisam entrar no contrato desta mudança antes da próxima aplicação para que a interface pt-BR permaneça coerente em páginas próprias, fragmentos HTMX e telas fornecidas pelo django-allauth.

## What Changes

- Permitir que a pessoa autenticada cadastre e edite sua chave Pix principal, com aviso explícito de que o Pixu não a verifica junto ao banco.
- Criar pagamentos vinculados a uma única dívida, com valor parcial, referência opcional e comprovante privado opcional (imagem ou PDF).
- Exibir ao pagador a chave Pix atual do recebedor e separar saldo aberto de valor reservado por pagamentos pendentes.
- Permitir somente ao recebedor confirmar ou rejeitar um pagamento pendente, registrando autor e data da decisão de forma idempotente.
- Atualizar o saldo somente na confirmação; rejeições liberam a reserva sem quitar a dívida.
- Bloquear definitivamente alterações de valor, participantes, cotas e recebedor da cobrança desde o primeiro pagamento registrado, inclusive pendente.
- Proteger os comprovantes para que apenas pagador e recebedor autenticados tenham acesso.
- Permitir criar, substituir/editar e remover comprovantes respeitando o estado do pagamento e a autorização do pagador.
- Tornar o modelo de comprovante compatível com storage local e servidores S3-like; disponibilizar Garage no Compose local para validação.
- Disponibilizar as ações por POST convencional e melhorias HTMX, com autorização e validação no servidor.
- Garantir que textos de interface, rótulos, placeholders, mensagens de validação, estados e ações das telas de autenticação, conta, cobrança e pagamento sejam traduzíveis pelo sistema de internacionalização do Django e apresentados em pt-BR, incluindo as telas de gerenciamento de e-mail do django-allauth.
- Aceitar a representação monetária pt-BR com vírgula decimal nos formulários e na prévia HTMX, normalizando os valores para centavos inteiros e exibindo os valores novamente com vírgula.
- Corrigir pluralização de contagens, estado ativo da navegação, área segura da navegação inferior e consistência de layout entre mobile e desktop nas telas auditadas.

## Capabilities

### New Capabilities

- `settlements/payments`: chave Pix exibida ao pagador, registro de pagamentos, reservas, comprovantes privados e confirmação/rejeição manual.
- `charges`: regras de bloqueio definitivo da cobrança após o primeiro pagamento registrado.

### Modified Capabilities

- `charges`: entrada monetária pt-BR, pluralização e composição responsiva das telas de cobrança passam a ser requisitos observáveis.
- `settlements/payments`: internacionalização pt-BR, consistência das telas de conta/pagamento e mensagens de validação passam a ser requisitos observáveis.

## Impact

- `pixu/accounts`: perfil/chave Pix, formulários, autorização e telas de edição.
- `pixu/charges`: serviços e modelos para determinar o bloqueio financeiro da cobrança e impedir edições posteriores.
- `pixu/settlements`: novos modelos, migrações, serviços, views, URLs, templates e testes para pagamentos e comprovantes.
- Armazenamento privado de anexos, limites de tamanho/tipo e rota autenticada de download.
- Backend de storage configurável, credenciais e endpoint S3-like nos ambientes locais e de produção.
- Serviço Garage, volumes persistentes e bucket privado no Compose local.
- Templates, HTMX, Tailwind compilado e documentação de execução/testes.
- Catálogos de tradução pt-BR, mensagens localizadas, templates de conta/allauth e testes de parsing monetário.
- Revisão visual autenticada em viewport móvel e desktop, incluindo navegação, pluralização, prévia HTMX e detalhe de comprovante.
