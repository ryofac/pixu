# Proposal

## Why

A página inicial atual serve como lista de cobranças e tem apenas uma apresentação pública mínima, enquanto a marca aprovada, o tema escuro e o dashboard da primeira versão ainda não estão integrados. A referência `docs/design/pixu_landing_page.html` oferece a direção visual que falta, mas precisa ser adaptada às regras de acessibilidade, pt-BR, Django templates e assets locais do Pixu.

## What Changes

- Criar uma landing page pública responsiva a partir da composição da referência: hero, chamadas para cadastro/login, ilustração decorativa e benefícios; manter a área de cobranças para pessoas autenticadas.
- Aplicar a System Core Logo aprovada e atualizar a documentação visual e o README com o arquivo de marca local.
- Implementar preferência de aparência Claro/Escuro/Sistema em telas públicas e autenticadas, com Sistema como padrão, persistência apenas no navegador, aplicação antes da primeira pintura e fallback sem JavaScript/armazenamento.
- Definir tokens semânticos para os dois temas e adaptar navegação, autenticação, formulários, cobranças, convites, pagamentos e compensações, incluindo fragmentos HTMX.
- Completar o dashboard autenticado com valores brutos a receber/a pagar, potencial de compensação separado, convites pendentes e listas curtas de cobranças criadas/participadas.
- Usar texto pt-BR, rotas reais de cadastro/login, fontes de sistema e ícones locais; remover da experiência os CDNs, valores em euro e interações de demonstração da referência.
- Validar a experiência nos breakpoints mobile/desktop, com teclado, preferência do sistema, recarga e ausência de flash do tema incorreto.

## Capabilities

### New Capabilities

- `dashboard`: resumo individual de saldos e atividades para a área autenticada, sem criar um extrato global.
- `product-experience/landing-page`: entrada pública do Pixu e encaminhamento contextual para cadastro, login ou área autenticada.
- `product-experience/theme-preferences`: escolha e aplicação consistente dos temas Claro, Escuro e Sistema nas páginas do produto.

### Modified Capabilities

Nenhuma. Os requisitos existentes de cobranças, pagamentos e compensações permanecem; esta mudança completa suas telas e apresenta os respectivos estados nos temas claro e escuro.

## Impact

- Templates Django de entrada, layout base, autenticação e fluxos autenticados; CSS de entrada Tailwind e JavaScript local para preferência visual.
- Consultas do dashboard reutilizando as regras existentes de pagamentos e compensações; nenhuma nova escrita monetária ou extrato global.
- `docs/product-design.md`, `TODO.md` e README, incluindo a marca SVG local.
- Testes Django e E2E para conteúdo público, dashboard, temas, navegação, acessibilidade básica e breakpoints mobile/desktop.
