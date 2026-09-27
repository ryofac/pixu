# Tasks

## 1. Wave 0, marca e documentação

- [x] 1.1 Registrar em `docs/product-design.md` a System Core Logo aprovada, os tokens do tema escuro e a adaptação da landing page, verificando as referências HTML e os critérios mobile/desktop.
- [x] 1.2 Criar SVG local reutilizável da System Core Logo e aplicá-lo nos pontos de marca; incluir a imagem e sua origem de design no README e verificar renderização em fundos claros/escuros.

## 2. Preferência de tema e superfícies

- [x] 2.1 Implementar tokens semânticos claros/escuros e fallback CSS por preferência do sistema; verificar que Tailwind compila as classes usadas sem CDN.
- [x] 2.2 Aplicar preferência Sistema/Claro/Escuro antes da primeira pintura e adicionar seletor acessível persistente na navegação pública e autenticada; verificar storage bloqueado, navegação, recarga e mudança de aparência do sistema.
- [x] 2.3 Adaptar layouts base, django-allauth, perfil, cobranças, convites, pagamentos e compensações aos tokens; adicionar testes E2E de legibilidade, foco, estados, HTMX e formulário preenchido nos dois temas.

## 3. Entrada pública e dashboard

- [x] 3.1 Implementar a landing page Django com a composição aprovada, conteúdo pt-BR, rotas reais de cadastro/login, ilustração sem dados reais, mobile/desktop e movimento reduzido; cobrir conteúdo e CTAs com testes HTTP.
- [x] 3.2 Implementar dashboard com saldos abertos a receber/pagar, potencial de compensação separado, convites pendentes e listas recentes; testar cobranças ativas, saldos liquidados, dívidas recíprocas e estados vazios.
- [x] 3.3 Manter a lista de cobranças em `/charges/` e encaminhar a rota inicial conforme autenticação; testar permissões e ausência de cobranças privadas na resposta pública.

## 4. Validação integrada e produto

- [x] 4.1 Validar fluxo integrado com conta criada pela interface, área pública/autenticada, dashboard, cobranças, pagamentos e alternância de tema em 390×844 e 1440×900; executar `just e2e` e registrar evidências.
- [x] 4.2 Destinar a validação curta com três pessoas sobre “Pix pendente”, “saldo aberto” e “compensado” à fase de testes beta; registrar confusões e ajustar os textos conforme os resultados dessa validação.
- [x] 4.3 Executar `openspec validate complete-product-experience --strict`, `just pytest` relevante, `just e2e` e `git diff --check`; atualizar `TODO.md` com o estado real das tarefas.
