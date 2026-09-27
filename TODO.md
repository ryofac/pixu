# TODO do Pixu

Este arquivo acompanha o roadmap geral. A mudança ativa do OpenSpec é `offset-reciprocal-debts`; suas tarefas e evidências ficam em `openspec/changes/offset-reciprocal-debts/tasks.md`.

## Concluído

- [x] Inicializar o projeto com Cookiecutter Django e manter Compose local e de produção.
- [x] Configurar os apps Django iniciais, build local de Tailwind e cópia local do HTMX.
- [x] Adicionar `AGENTS.md`, OpenSpec, skills de ai-memory, grill-me, Chrome DevTools e ferramentas do Pixu.
- [x] Criar exemplos de variáveis de produção sem incluir credenciais reais.

## Decisões de escopo resolvidas

- [x] Usar o documento atualizado em `docs/` como fonte e sincronizar `PIXU_IMPLEMENTATION_BRIEF.md`.
- [x] Incluir cadastro público, autenticação e recuperação por e-mail no primeiro lote.
- [x] Incluir aceite e recusa de convites, com substituição de destinatário e ativação da cobrança após todos os aceites.

## Wave 0 — design antes das telas

- [x] Mapear as jornadas de criador e participante pagador.
- [x] Criar wireframes das telas previstas na seção 6 do briefing atualizado.
- [x] Documentar estados de aceite, pagamento pendente/confirmado/rejeitado e compensação.
- [x] Criar protótipo navegável com dados fictícios.
- [x] Registrar decisões visuais, componentes e textos em `docs/product-design.md` e revisar as referências de `docs/design/`.
- [x] Revisar o protótipo e incorporar o retorno do usuário: desktop tem navegação lateral e composição própria; celular mantém navegação inferior.
- [x] Definir esta versão como online, sem cache pessoal nem fila offline para aceite/recusa.
- [ ] Validar com usuários se “Pix pendente”, “saldo aberto” e “compensado” são compreendidos sem explicação.

## OpenSpec — lotes concluídos

- [x] `bootstrap-pixu-and-charges` — contas, perfil, cobranças, convites e responsividade (arquivado em 25/09/2026).
- [x] `record-and-confirm-pix` — pagamentos manuais, comprovantes privados em storage S3-like/Garage e revisão visual/i18n (arquivado em 26/09/2026).
- [x] `add-frontend-integration-tests` — infraestrutura e auditoria E2E da interface em mobile e desktop (arquivado em 26/09/2026).

## OpenSpec — `offset-reciprocal-debts` (mudança ativa)

- [x] Criar proposta, design, specs delta e tarefas para compensações recíprocas; validar com `openspec validate offset-reciprocal-debts --strict`.
- [x] Implementar eventos auditáveis, cálculo de saldos, elegibilidade, aplicação transacional e fluxo acessível no detalhe da cobrança.
- [x] Validar concorrência no PostgreSQL, jornadas HTTP/E2E nos breakpoints mobile e desktop, suíte Django relevante e `git diff --check`.

## Próximo lote mapeado, conforme o briefing

- [ ] Planejar e implementar `complete-product-experience` (R01–R03, R15–R17), incluindo tema escuro conforme o backlog abaixo.

## Tema escuro — backlog de `complete-product-experience`

**Estado:** mapeado, não implementado. Contrato de experiência e critérios de aceite em [product-design, seção 2.4](docs/product-design.md#24-temas-claro-escuro-e-sistema--planejado). Ao planejar `complete-product-experience`, incorporar os itens abaixo aos seus artefatos OpenSpec, preservando os identificadores para rastreabilidade. Estes itens não integram a contagem de tarefas de `bootstrap-pixu-and-charges`.

- [ ] TEMA-01 — Definir e registrar tokens semânticos para os temas claro e escuro: fundo, superfícies, texto, bordas, ações, foco e estados. Revisar contraste e apresentação da marca provisória nos dois temas antes de implementar as telas.
- [ ] TEMA-02 — Implementar seletor acessível **Claro / Escuro / Sistema**, disponível antes e depois do login, com **Sistema** como padrão. Salvar somente a preferência visual no navegador; respeitar mudanças do sistema quando essa opção estiver ativa, aplicar a escolha antes da primeira pintura e manter fallback utilizável sem JavaScript ou armazenamento local.
- [ ] TEMA-03 — Adaptar entrada pública, login, cadastro, confirmação, recuperação, perfil e formulários compartilhados aos dois temas, incluindo ajuda, erros, estados desabilitados e foco visível.
- [ ] TEMA-04 — Adaptar navegação, cobranças, convites, detalhes e as telas de pagamentos/dashboard disponíveis naquele lote. Verificar que fragmentos HTMX novos herdam o tema vigente e que alternar tema preserva dados digitados e o estado da página.
- [ ] TEMA-05 — Validar claro/escuro/sistema em celular e desktop: contraste, teclado, recarga, navegação entre páginas, preferência salva, mudança de aparência do sistema, ausência de flash do tema incorreto e fallback com armazenamento indisponível. Registrar evidências no checklist OpenSpec do lote antes de marcá-lo concluído.
