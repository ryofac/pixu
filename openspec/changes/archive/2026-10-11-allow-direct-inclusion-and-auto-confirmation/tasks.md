# Tasks

## 1. Preferência de inclusão direta

- [x] 1.1 Adicionar a preferência booleana desativada por padrão à conta e gerar a migração; verificar com `just pytest pixu/accounts/tests.py` e `just manage makemigrations --check`.
- [x] 1.2 Expor a preferência somente no formulário do próprio perfil, persistir sob autenticação e adicionar aviso recomendatório no onboarding sem ativação implícita; testar GET/POST, default falso e edição própria com `just pytest pixu/accounts/tests.py`.
- [x] 1.3 Criar participações diretas aceitas para contas que autorizaram inclusão, mantendo convite pendente para demais; criar dívida apenas quando aplicável, manter a ativação e rateio existentes, e cobrir os casos em `pixu/charges/tests.py` com `just pytest pixu/charges/tests.py`.

## 2. Confirmação automática por dívida

- [x] 2.1 Adicionar preferência por dívida e origem explícita da confirmação no pagamento, com migração compatível para dados existentes; testar defaults e preservar valores históricos com `just pytest pixu/settlements/tests.py`.
- [x] 2.2 Implementar serviço de configuração permitido apenas ao recebedor autenticado em cobrança ativa e controlar a opção na linha da dívida no detalhe; testar autorização, estado, POST convencional/HTMX e apresentação nos temas/tamanhos suportados com `just pytest pixu/charges pixu/settlements`.
- [x] 2.3 Confirmar no ato pagamentos futuros válidos de pagadores autenticados quando a preferência da dívida estiver ativa, incluindo parciais; manter convidados pendentes, validar disponibilidade com bloqueio transacional e auditar origem/data; cobrir tudo em `just pytest pixu/settlements/tests.py`.
- [x] 2.4 Atualizar mensagens e histórico para diferenciar confirmação automática de manual sem prometer verificação externa; testar cada retorno de pagamento em `just pytest pixu/settlements/tests.py`.

## 3. Integração e validação

- [x] 3.1 Compilar os estilos com `npm run build` e revisar onboarding, perfil, detalhe da cobrança e registro de pagamento em 375 px e desktop, claro/escuro, foco visível e sem overflow horizontal.
- [x] 3.2 Executar regressão das áreas afetadas com `just pytest pixu/accounts pixu/charges pixu/settlements` e corrigir falhas causadas por esta mudança.
- [x] 3.3 Validar artefatos OpenSpec com `openspec validate allow-direct-inclusion-and-auto-confirmation --strict` e confirmar coerência entre proposta, deltas, design, tarefas e documentação visual aprovada.
