## 1. Wave 0 — design e pré-requisito das telas

- [x] 1.1 Mapear jornadas de cadastro, edição de perfil, criação de cobrança, convite, aceite, recusa e substituição; entregar wireframes das telas previstas na seção 6 do brief e matriz de estados. Verificar que todos os estados e ações de R01–R06 estão representados.
- [x] 1.2 Criar protótipo navegável de revisão e `docs/product-design.md` com tokens, componentes, textos, estados vazios/erro/sucesso e padrões HTMX/Tailwind. Verificar que o documento cobre responsividade e acessibilidade e que não contradiz os specs desta mudança.
- [x] 1.3 Revisar os rótulos de estado no fluxo navegável; definir a primeira versão como online, sem cache ou fila offline; incorporar o retorno do usuário para dar ao desktop uma estrutura própria com breakpoints nativos do Tailwind e registrar as decisões em `docs/product-design.md`.

## 2. Contas e perfil

- [x] 2.1 Habilitar `DJANGO_ACCOUNT_ALLOW_REGISTRATION=True` nos ambientes local e produção, manter confirmação de e-mail e login por nome de usuário, e configurar recuperação de senha; verificar fluxos de e-mail local no console e SMTP em produção sem versionar segredos.
- [x] 2.2 Criar perfil Pix relacionado à conta, migração e formulário autenticado de edição da própria chave; verificar persistência para o titular, recusa de alteração por outra conta e texto informando que a chave não é validada pelo Pixu.
- [x] 2.3 Ajustar templates e URLs de cadastro, confirmação, login, logout, recuperação e perfil conforme `docs/product-design.md`; verificar navegação completa com contas criadas pela interface.

## 3. Domínio de cobranças

- [x] 3.1 Criar modelos de cobrança, participação e dívida com valores inteiros em centavos, estados e constraints de unicidade; verificar migrações geradas e restrições de valor/participação duplicada no PostgreSQL.
- [x] 3.2 Implementar cálculo de rateio igualitário com resíduos distribuídos por identificador persistente; verificar soma exata, valores inteiros e determinismo com testes para divisões exatas e com centavos residuais.
- [x] 3.3 Implementar criação de cobrança com participação opcional do criador, recebedor selecionável, seleção de usuários cadastrados, prévia editável e convites pendentes; verificar título, valor positivo, descrição opcional, participantes únicos, ao menos uma cota e ausência de dívida contra si mesmo.
- [x] 3.4 Implementar aceite, recusa e substituição de participante recusado antes de operação financeira; verificar que recusa não cria dívida, aceite repetido ou concorrente cria no máximo uma dívida e cotas aceitas não mudam.
- [x] 3.5 Implementar ativação transacional após todos os convites ativos serem aceitos e cotas fecharem o total; verificar que cobranças aguardando resposta ficam fora dos totais e passam a ativas após o último aceite.
- [x] 3.6 Implementar edição de cotas próprias e pendentes com validação da soma e de valores não negativos; verificar que cota aceita é imutável e que edição inválida não persiste.
- [x] 3.7 Separar criador e recebedor com migração que preserve cobranças existentes; permitir troca do recebedor antes de aceite de outra pessoa/operação financeira, sincronizar dívida própria e verificar acesso do recebedor sem participação e bloqueio concorrente com aceite.

## 4. Views, templates e segurança

- [x] 4.1 Criar telas de cadastro, autenticação, recuperação e perfil em Django templates estilizados segundo `docs/product-design.md`; verificar uso do CSS local compilado e mensagens acionáveis para erros.
- [x] 4.2 Criar lista de convites, criação/prévia de cobrança, detalhe e ações de aceitar/recusar/substituir com HTMX; verificar atualização dos fragmentos e equivalência com o fluxo convencional.
- [x] 4.3 Aplicar autorização por objeto, CSRF, limites de campos e escape de texto a todos os formulários e endpoints; verificar acesso negado para não participantes e payloads inválidos sem alteração persistida.

## 5. Validação integrada e documentação

- [x] 5.1 Adicionar testes de domínio e integração para cadastro/recuperação, rateio, convites, substituição, ativação, permissões e idempotência; verificar os cenários das specs usando PostgreSQL nos casos transacionais.
- [x] 5.2 Executar a suíte pelo fluxo local documentado (`just up` e `just pytest`) e corrigir falhas; verificar também `just manage check` no container Django.
- [x] 5.3 Atualizar README com configuração de e-mail, criação de conta, migrações e passos para executar o primeiro fluxo; confirmar que cada comando documentado existe no projeto.

## Evidências e pendências da validação — 25/09/2026

- `just pytest`: 46 testes passaram no PostgreSQL, incluindo jornada ponta a ponta de conta com CSRF, confirmação, recuperação, redirecionamento para cobranças e migração do recebedor, cotas manuais, exclusão do criador do rateio, autorização, corrida entre aceite e troca de recebedor e entrega assíncrona de e-mail.
- `just manage check`: sem problemas; `just manage makemigrations --check --dry-run`: nenhuma alteração de modelo sem migração.
- `npm run build`, Ruff e `git diff --check`: passaram. `just up` iniciou o ambiente local.
- 2.1: cadastro, confirmação e recuperação cobertos por testes; configuração de produção com conta Google dedicada, senha de app e `smtp.gmail.com:587`/STARTTLS documentada no README e no exemplo de ambiente; entrega real via SMTP validada em produção, com o e-mail recebido pelo destinatário.
- 2.3: templates e URLs implementados; a jornada HTTP completa com conta criada pela interface passou nos testes. A revisão visual com Chrome DevTools continua pendente porque o ambiente não tem servidor gráfico X.
- O CLI `openspec` não está disponível neste ambiente; checklist reconciliado diretamente com os arquivos da mudança e pronto para arquivamento manual.
- Tema escuro está mapeado para `complete-product-experience` em `TODO.md` (`TEMA-01` a `TEMA-05`), com critérios de aceite na seção 2.4 de `docs/product-design.md`. O backlog futuro não entra na contagem das 19 tarefas desta mudança.
