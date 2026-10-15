# Changelog

As mudanças relevantes do Pixu são registradas neste arquivo.

## [1.3.0] - 2026-10-15

### Adicionado

- Extratos próprios para contas a pagar, a receber e já pagas, com busca, filtros de data e exportação CSV/PDF dos eventos financeiros para auditoria.
- Priorização de dívidas abertas mais antigas no dashboard e na lista de cobranças.

### Melhorado

- Entrada de valores monetários no celular no estilo de apps bancários, aplicando os centavos conforme os dígitos são informados.

## [1.2.0] - 2026-10-15

### Corrigido

- Login OAuth com Google em produção, incluindo as dependências do `django-allauth` necessárias para validar o ID token retornado pelo provedor.

## [1.1.0] - 2026-10-11

Esta versão cobre as mudanças a partir do commit [`4d74f34`](https://github.com/ryofac/pixu/commit/4d74f340e7aa98a4804a88e4e3defc4fde60818), inclusive.

### Adicionado

- Login com Google e GitHub e onboarding inicial de conta.
- Cobranças com divisão por itens, convites para contas Pixu e entrada de convidados externos por link e código pessoal, com acesso limitado à própria cota.
- Pagamento da cota de convidado enquanto as entradas da cobrança permanecem abertas, usando o total de participantes declarado pelo cobrador.
- Manifesto PWA, ícones de alta definição e suporte à instalação em dispositivos compatíveis.
- Página de perfil autenticada com chave Pix declarada e cobranças compartilhadas; nomes de contas Pixu nas cobranças levam a esse perfil.
- Preferência opcional para inclusão direta em cobranças futuras, desativada por padrão, e confirmação automática no Pixu para pagamentos declarados por contas confiáveis. Essa confirmação não verifica transferências bancárias.
- Deploy de VM Oracle com Compose e Portainer, HTTPS com Traefik e publicação de imagens privadas multi-arquitetura no GHCR, mantendo o bundle local como alternativa.

### Melhorado

- Detalhes da cobrança organizam participantes pela origem e mostram primeiro, em cada grupo, pagamentos que precisam de atenção.
- Fluxos de pagamento, convites e perfis com hierarquia visual e adaptação para dispositivos móveis.

### Deploy

- Imagens Docker `pixu-django`, `pixu-postgres`, `pixu-nginx` e `pixu-traefik` publicadas no GHCR com tags `main` e `sha-<commit>` para `linux/amd64` e `linux/arm64`.
- Compose da VM aceita `PIXU_IMAGE_TAG` e preserva overrides para imagens locais carregadas pelo bundle.

[1.3.0]: https://github.com/ryofac/pixu/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/ryofac/pixu/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/ryofac/pixu/compare/4d74f340e7aa98a4804a88e4e3defc4fde60818%5E...v1.1.0
