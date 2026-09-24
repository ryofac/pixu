## 1. Wave 0 — design e pré-requisito das telas

- [x] 1.1 Mapear jornadas de cadastro, edição de perfil, criação de cobrança, convite, aceite, recusa e substituição; entregar wireframes das telas previstas na seção 6 do brief e matriz de estados. Verificar que todos os estados e ações de R01–R06 estão representados.
- [x] 1.2 Criar protótipo navegável de revisão e `docs/product-design.md` com tokens, componentes, textos, estados vazios/erro/sucesso e padrões HTMX/Tailwind. Verificar que o documento cobre responsividade e acessibilidade e que não contradiz os specs desta mudança.
- [ ] 1.3 Revisar a compreensão de “convite pendente”, “cobrança ativa” e “dívida criada” com o fluxo navegável; decidir o escopo offline-first e registrar a revisão e aprovação do design antes de iniciar as telas Django.

## 2. Contas e perfil

- [ ] 2.1 Habilitar `DJANGO_ACCOUNT_ALLOW_REGISTRATION=True` nos ambientes local e produção, manter confirmação de e-mail e login por nome de usuário, e configurar recuperação de senha; verificar fluxos de e-mail local no console e SMTP em produção sem versionar segredos.
- [ ] 2.2 Criar perfil Pix relacionado à conta, migração e formulário autenticado de edição da própria chave; verificar persistência para o titular, recusa de alteração por outra conta e texto informando que a chave não é validada pelo Pixu.
- [ ] 2.3 Ajustar templates e URLs de cadastro, confirmação, login, logout, recuperação e perfil conforme `docs/product-design.md`; verificar navegação completa com contas criadas pela interface.

## 3. Domínio de cobranças

- [ ] 3.1 Criar modelos de cobrança, participação e dívida com valores inteiros em centavos, estados e constraints de unicidade; verificar migrações geradas e restrições de valor/participação duplicada no PostgreSQL.
- [ ] 3.2 Implementar cálculo de rateio igualitário com resíduos distribuídos por identificador persistente; verificar soma exata, valores inteiros e determinismo com testes para divisões exatas e com centavos residuais.
- [ ] 3.3 Implementar criação de cobrança com criador incluído, seleção de usuários cadastrados, prévia e convites pendentes; verificar título, valor positivo, descrição opcional, ausência de participantes repetidos e ausência de dívida contra o criador.
- [ ] 3.4 Implementar aceite, recusa e substituição de participante recusado antes de operação financeira; verificar que recusa não cria dívida, aceite repetido ou concorrente cria no máximo uma dívida e cotas aceitas não mudam.
- [ ] 3.5 Implementar ativação transacional após todos os convites ativos serem aceitos e cotas fecharem o total; verificar que cobranças aguardando resposta ficam fora dos totais e passam a ativas após o último aceite.
- [ ] 3.6 Implementar edição de cotas próprias e pendentes com validação da soma e de valores não negativos; verificar que cota aceita é imutável e que edição inválida não persiste.

## 4. Views, templates e segurança

- [ ] 4.1 Criar telas de cadastro, autenticação, recuperação e perfil em Django templates estilizados segundo `docs/product-design.md`; verificar uso do CSS local compilado e mensagens acionáveis para erros.
- [ ] 4.2 Criar lista de convites, criação/prévia de cobrança, detalhe e ações de aceitar/recusar/substituir com HTMX; verificar atualização dos fragmentos e equivalência com o fluxo convencional.
- [ ] 4.3 Aplicar autorização por objeto, CSRF, limites de campos e escape de texto a todos os formulários e endpoints; verificar acesso negado para não participantes e payloads inválidos sem alteração persistida.

## 5. Validação integrada e documentação

- [ ] 5.1 Adicionar testes de domínio e integração para cadastro/recuperação, rateio, convites, substituição, ativação, permissões e idempotência; verificar os cenários das specs usando PostgreSQL nos casos transacionais.
- [ ] 5.2 Executar a suíte pelo fluxo local documentado (`just up` e `just pytest`) e corrigir falhas; verificar também `just manage check` no container Django.
- [ ] 5.3 Atualizar README com configuração de e-mail, criação de conta, migrações e passos para executar e validar o primeiro fluxo; confirmar que cada comando documentado existe no projeto.
