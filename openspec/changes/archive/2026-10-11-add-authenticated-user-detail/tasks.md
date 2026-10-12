# Tasks

## 1. Wave 0 — revisão visual antes do código

- [x] 1.1 Criar o protótipo isolado `docs/design/pixu_authenticated_user_detail_prototype.html` com os estados de perfil próprio, perfil de outra conta com/sem chave e cobranças em comum, além da origem dos links no detalhe da cobrança; verificar em 375 px e 1024 px que não há overflow, que os estados têm texto e que os links preservam foco visível.
- [x] 1.2 Apresentar o protótipo para confirmação explícita da pessoa usuária e, somente após ela aprová-lo, registrar em `docs/product-design.md` as regras estáveis de hierarquia, responsividade, tema e identidade; verificar que a documentação não declara como aprovado um estado ainda não confirmado.

## 2. Perfil autenticado e isolamento de cobranças

- [x] 2.1 Ajustar a consulta do detalhe de conta para carregar a chave Pix declarada da conta-alvo e a interseção de cobranças visíveis para visitante e alvo, sem N+1 e sem migração; adicionar testes em `pixu/accounts/tests.py` e verificar com `just pytest pixu/accounts/tests.py` os casos de visitante, username inexistente, chave presente/ausente e próprio perfil.
- [x] 2.2 Renderizar os cartões de identidade e chave Pix e a seção de cobranças em comum conforme o protótipo aprovado, preservando os controles privados apenas para a titular; cobrir em `pixu/accounts/tests.py` o estado vazio, a navegação para cobrança compartilhada e a ausência de títulos/dados de cobrança não compartilhada, verificando com `just pytest pixu/accounts/tests.py`.
- [x] 2.3 Manter o perfil de outra conta sem aviso redundante de somente leitura e posicionar a ação de copiar junto à chave quando presente; validar foco, alvo de toque e retorno de sucesso em `tests/e2e/test_accounts.py`.

## 3. Navegação a partir da cobrança

- [x] 3.1 Atualizar os contextos e fragmentos do detalhe autenticado de cobrança para vincular criadora, recebedora e participantes com `Participation.user` ao detalhe canônico de conta, incluindo o rótulo “Você”; adicionar testes de renderização em `pixu/charges/` e verificar com `just pytest pixu/charges`.
- [x] 3.2 Manter entradas convidadas externas sem link mesmo quando seu nome coincide com um `@username`, inclusive nos detalhes sob demanda da cota; adicionar o cenário de isolamento aos testes de cobranças e verificar com `just pytest pixu/charges`.

## 4. Integração e verificação de entrega

- [x] 4.1 Executar a suíte de regressão afetada com `just pytest pixu/accounts pixu/charges pixu/settlements` e corrigir falhas relacionadas antes de concluir a mudança.
- [x] 4.2 Compilar os estilos com `npm run build` e percorrer no navegador os perfis próprio e de outra conta e o detalhe da cobrança em tema claro/escuro, nos viewports 375 px e 1024 px; verificar contraste, foco de teclado, área segura da navegação fixa e ausência de overflow horizontal.
- [x] 4.3 Validar os artefatos concluídos com `openspec validate add-authenticated-user-detail --strict` e confirmar que proposta, especificações, design, tarefas e documentação aprovada permanecem coerentes.
