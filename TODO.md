# TODO do Pixu

Este arquivo acompanha o roadmap geral. A mudança atual do OpenSpec é `bootstrap-pixu-and-charges`; suas tarefas detalhadas ficam em `openspec/changes/bootstrap-pixu-and-charges/tasks.md`.

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
- [ ] Revisar/aprovar o protótipo e confirmar compreensão dos estados antes das telas Django.
- [ ] Definir o escopo offline-first: leitura sem rede, rascunhos locais e se aceite/recusa de convites pode entrar em fila de sincronização.
- [ ] Validar se “Pix pendente”, “saldo aberto” e “compensado” são compreendidos sem explicação.

## OpenSpec — `bootstrap-pixu-and-charges`

- [x] Fechar o escopo conforme R01–R02, R04–R06 e R16–R17 do briefing atualizado.
- [x] Criar `proposal.md`, specs de `accounts` e `charges`, `design.md` e `tasks.md` com critérios verificáveis.
- [x] Validar os artefatos com `openspec validate bootstrap-pixu-and-charges --strict`.
- [ ] Revisar/aprovar os artefatos antes de iniciar implementação.
- [ ] Aplicar a mudança e validar seus cenários após aprovação explícita do plano.

## Próximos lotes, conforme o briefing

- [ ] Planejar e implementar `record-and-confirm-pix` (R03, R07–R10, R14, R16).
- [ ] Planejar e implementar `offset-reciprocal-debts` (R11–R14).
- [ ] Planejar e implementar `complete-product-experience` (R01–R03, R15–R17).
