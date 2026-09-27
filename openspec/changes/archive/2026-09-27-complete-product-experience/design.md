# Design

## Context

Veja `proposal.md` para motivação e as três specs delta para o contrato observável. Hoje `config/urls.py` aponta a rota inicial para `ChargeListView`; o template `pages/home.html` alterna entre a lista de cobranças autenticada e uma apresentação pública curta. A app `pixu/dashboard` ainda é um esqueleto. `base.html` concentra a navegação pública/autenticada, e Tailwind 4 já é compilado de `assets/css/input.css` para `pixu/static/css/tailwind.css`. `project.js` contém interações locais, mas não existe preferência de tema.

A referência [`docs/design/pixu_landing_page.html`](../../../docs/design/pixu_landing_page.html) usa Tailwind, fonte e ícones por CDN, idioma pt-PT, euro, links `#`, alternância apenas claro/escuro e geração contínua de pétalas no DOM. Ela orienta composição e conteúdo, mas esses detalhes não são contrato. A marca canônica é a System Core Logo descrita em `docs/product-design.md` e demonstrada em `docs/design/pixu_logo_system.html`.

## Goals / Non-Goals

**Goals:**

- Entregar uma página pública real na rota inicial, um dashboard autenticado útil e a mesma preferência visual entre telas públicas e autenticadas.
- Manter Django templates, HTMX, autorização server-side e Tailwind compilado localmente.
- Reutilizar eventos existentes de pagamentos e compensações como fonte de verdade dos saldos.
- Preservar a composição Sakura da referência, a marca aprovada, acessibilidade e redução de movimento.

**Non-Goals:**

- Não implementar extrato global, dados em cache/offline, sincronização de tema por conta, integração Pix/bancária ou confirmação automática.
- Não incluir o fluxo de cancelamento de cobranças nesta mudança; ele terá uma mudança OpenSpec própria.
- Não servir o HTML de exploração diretamente, introduzir SPA, baixar fonte/icon font de terceiros nem manter a geração contínua de elementos decorativos.

## Decisions

### Rota inicial separa visitante de pessoa autenticada

Manter o nome de rota `home`, mas encaminhar visitantes para um template público dedicado e pessoas autenticadas para o dashboard. A lista completa de cobranças continua acessível pela rota já existente `charges:list` (`/charges/`). A view de lista fica restrita a usuários autenticados, para que a entrada pública não reapareça como uma lista vazia em outra URL.

Alternativa considerada: manter um único template condicionado pelo usuário. Foi rejeitada porque mistura landing, dashboard e listagem, e dificulta validar privacidade e estados vazios isoladamente.

### Landing page reaproveita a composição, não o runtime da demonstração

Implementar com templates Django e utilitários Tailwind locais: header com marca/tema/entrar, hero com cadastro, login secundário, ilustração apenas em telas largas e dois cartões de benefícios. O texto passa para pt-BR; valores ilustrativos usam `R$`, são estáticos e identificados como exemplo. O status decorativo comunica convite/cota, não transferência ou confirmação real. Gradientes e elementos Sakura ficam atrás do conteúdo e não recebem eventos.

Usar poucas pétalas em CSS com `prefers-reduced-motion` em vez do `setInterval` que insere e remove elementos. Isso preserva o caráter visual sem churn de DOM, ruído para leitores de tela ou animação obrigatória.

Alternativa considerada: copiar o HTML como está. Foi rejeitada pelos CDNs, links de demonstração, locale/moeda divergentes, controle de tema incompleto e marca antiga.

### Preferência de tema é global e progressiva

Representar a escolha `light`, `dark` ou `system` na preferência do navegador. Um pequeno script local síncrono no `<head>` lê armazenamento e define o tema resolvido no elemento raiz antes do CSS pintar; erros de storage são capturados. `project.js` atualiza a seleção sem recarregar, persiste a escolha se possível e observa mudanças de `prefers-color-scheme` somente quando Sistema está ativo.

Sem JavaScript, CSS usa `prefers-color-scheme` para tokens semânticos; sem preferência detectável, o padrão é claro. Os tokens de canvas, superfície, texto, borda, ação, foco e estados são variáveis CSS usadas pelo Tailwind. As páginas reutilizam essas classes semânticas, inclusive layouts do django-allauth e fragmentos HTMX. O seletor é um campo `<select>` com rótulo visível e opções localizadas, para manter teclado e estado atual claros sem lotar o header mobile.

Alternativas consideradas: salvar escolha na conta (exigiria API/modelo e sincronização entre dispositivos) e alternar somente com ícone binário (não expõe claramente Sistema). Ambas foram rejeitadas.

### A System Core Logo é um componente reutilizável

Reproduzir localmente o desenho aprovado como SVG, usando gradiente Sakura e variáveis para o losango/recorte conforme o tema; manter wordmark `PiXu`. Um partial reutilizável evita cópias divergentes no header mobile, sidebar desktop e landing. Incluir uma versão SVG estática no README para documentar a identidade sem serviço externo.

Alternativa considerada: manter o ícone Sakura simplificado do `base.html` ou carregar a logo por CDN. A primeira perpetua a inconsistência rejeitada pelo usuário; a segunda falha offline e contraria o build local.

### Dashboard calcula saldos de eventos, sem materializar dinheiro

Adicionar consulta de dashboard que filtre dívidas aceitas de cobranças `ACTIVE` e some saldos abertos por direção em centavos inteiros. Calcular potencial agrupando as dívidas recíprocas por outra pessoa, somando disponibilidades em cada direção e tomando o menor total uma única vez por par. Reutilizar a mesma fórmula de pagamentos/compensações, preferindo agregações em lote para não executar consultas por cartão. Convites pendentes e listas recentes são consultas separadas, limitadas e com autorização herdada pelo detalhe.

Alternativa considerada: saldo gravado em novos campos de usuário/dívida. Foi rejeitada para não criar segunda fonte de verdade nem nova escrita financeira.

## Risks / Trade-offs

- [Classes de cor existentes podem fixar superfícies claras em uma página escura] → Trocar fundos, texto e bordas de layout por tokens semânticos; usar variantes específicas somente para estados que realmente variam.
- [Uma preferência local pode estar bloqueada pelo navegador] → Capturar falhas de leitura/gravação e manter o tema selecionável durante a sessão com fallback CSS.
- [A referência contém cartões que poderiam parecer dados reais] → Manter ilustração estática e claramente demonstrativa, sem nomes/estados de pagamento real.
- [Dashboard pode somar mal dívidas recíprocas ou reservas] → Somar saldos abertos para A receber/A pagar; calcular potencial a partir de disponibilidade, por par e sem adicioná-lo aos totais.
- [Logo SVG em múltiplos pontos pode colidir em IDs de gradiente] → O partial recebe um prefixo de ID único por instância e os testes verificam todas as renderizações.

## Migration Plan

Não há migração de banco. Primeiro publicar o initializer, tokens e seletor; depois substituir templates/rotas e incluir consultas do dashboard. A preferência local ausente ou inválida cai para Sistema, portanto usuários existentes recebem comportamento padrão sem ajuste de conta. Reversão consiste em retirar o novo seletor/initializer e restaurar a view/template anterior; nenhuma preferência afeta dados financeiros.
