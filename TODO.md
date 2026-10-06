# TODO do Pixu

Este arquivo acompanha o roadmap geral. Mudanças OpenSpec em andamento ficam em `openspec/changes/`; mudanças concluídas são arquivadas em `openspec/changes/archive/`.

## Concluído

- [x] Inicializar o projeto com Cookiecutter Django e manter Compose local e de produção.
- [x] Configurar os apps Django iniciais, build local de Tailwind e cópia local do HTMX.
- [x] Adicionar `AGENTS.md`, OpenSpec, skills de ai-memory, grill-me, Chrome DevTools e ferramentas do Pixu.
- [x] Criar exemplos de variáveis de produção sem incluir credenciais reais.
- [x] Preparar stack de VM para Portainer, imagens locais, ACME HTTP-01 via DuckDNS e template `.env.vm`.

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

## Testes beta

- [ ] Validar com três pessoas se “Pix pendente”, “saldo aberto” e “compensado” são compreendidos sem explicação prévia; registrar confusões e ajustar os textos se forem recorrentes. Esta validação foi planejada para a fase beta e não bloqueia o encerramento da implementação.

## OpenSpec — lotes concluídos

- [x] `bootstrap-pixu-and-charges` — contas, perfil, cobranças, convites e responsividade (arquivado em 25/09/2026).
- [x] `record-and-confirm-pix` — pagamentos manuais, comprovantes privados em storage S3-like/Garage e revisão visual/i18n (arquivado em 26/09/2026).
- [x] `add-frontend-integration-tests` — infraestrutura e auditoria E2E da interface em mobile e desktop (arquivado em 26/09/2026).
- [x] `offset-reciprocal-debts` — compensações auditáveis, concorrência e saldos recíprocos (arquivado e sincronizado em 26/09/2026).
- [x] `complete-product-experience` — landing page, dashboard, temas claro/escuro/sistema, refinamentos de interface e documentação (arquivado em 27/09/2026).

## Tema escuro — `complete-product-experience`

**Estado:** implementação e validação técnica concluídas (11/11 tarefas). A validação com pessoas usuárias está planejada para a fase beta e acompanhada separadamente acima.

- [x] Implementar a System Core Logo local, a landing page, o dashboard e os temas claro/escuro/sistema.
- [x] Adaptar telas públicas e autenticadas, formulários, pagamentos, compensações e fragmentos HTMX aos dois temas.
- [x] Validar fluxos integrados em 390×844 e 1440×900; `just e2e`: 24 testes passaram.
- [x] Validar a suíte Django; `just pytest`: 85 testes passaram. Corrigir o teardown do teste de migração que deixava apps dependentes sem tabelas.
- [x] Validar `openspec validate complete-product-experience --strict`, build local e `git diff --check`.
- [x] Transferir a validação de linguagem com três pessoas, sem explicação prévia dos termos, para os testes beta.

Itens técnicos `TEMA-01` a `TEMA-05` implementados e validados:

- [x] TEMA-01 — Definir tokens semânticos claro/escuro para fundo, superfícies, texto, bordas, ações, foco e estados; revisar contraste e marca.
- [x] TEMA-02 — Implementar seletor acessível **Claro / Escuro / Sistema**, preferência Sistema por padrão, armazenamento somente local, mudança automática do sistema e fallback sem storage/JavaScript.
- [x] TEMA-03 — Adaptar landing, login, cadastro, confirmação, recuperação, perfil e formulários compartilhados.
- [x] TEMA-04 — Adaptar navegação, cobranças, convites, detalhes, pagamentos, dashboard e fragmentos HTMX; preservar formulários e estado da página ao alternar.
- [x] TEMA-05 — Validar temas em celular e desktop: contraste, teclado, recarga, navegação, persistência, preferência de sistema e storage indisponível; evidências na checklist OpenSpec.
