## Context

Ver `proposal.md` para motivação e `specs/accounts/spec.md` e `specs/charges/spec.md` para os contratos. O scaffold observado já tem um usuário Django customizado em `pixu/accounts/`, django-allauth com confirmação de e-mail obrigatória e login por nome de usuário, mas `ACCOUNT_ALLOW_REGISTRATION` está desabilitado. O app `pixu/charges/` é vazio. PostgreSQL, middleware CSRF, templates, HTMX e o build local de Tailwind já estão preparados; `docs/product-design.md` ainda não existe.

O brief atualizado determina cadastro público e recusa de convites, deixa os quatro usuários de exemplo como fixtures opcionais e exige concluir a Wave 0 de design antes de implementar telas finais. Comprovantes privados pertencem ao lote de pagamentos posterior.

## Goals / Non-Goals

**Goals:**

- Integrar cadastro e recuperação de senha por e-mail ao allauth já instalado e permitir editar o perfil próprio.
- Criar cobranças e participações com cotas inteiras, convite/aceite/recusa e ativação após todas as respostas válidas.
- Criar uma dívida por participante aceito, sem duplicidade e sem incluí-la nos totais enquanto a cobrança não estiver ativa.
- Preservar autorização no servidor e a experiência progressiva com Django templates, HTMX e Tailwind compilado localmente.

**Non-Goals:**

- Implementar pagamentos, confirmação de Pix, comprovantes, compensações ou dashboard.
- Validar chaves Pix com bancos, processar transferências ou criar carteira.
- Exigir ou semear Ryan, Ana, Bruno e Carla em ambientes de produto; fixtures de exemplo são opcionais e restritas a desenvolvimento/testes.
- Implementar as telas sem revisão de `docs/product-design.md`.

## Decisions

### Contas e e-mail

Manter django-allauth como fluxo público de cadastro, sessão e recuperação. Configurar `DJANGO_ACCOUNT_ALLOW_REGISTRATION=True` nos ambientes local e de produção do produto; a variável continua disponível para pausar cadastros quando necessário. Manter a confirmação de e-mail obrigatória que já está configurada. O cadastro continua por e-mail, nome de usuário e senha, e o login usa nome de usuário conforme `ACCOUNT_LOGIN_METHODS`. Não adicionar provedores sociais.

Usar backend de console no ambiente local para que confirmações e links de recuperação sejam visíveis durante o desenvolvimento; produção usa o SMTP configurado em `.envs/.production/.django`. Não registrar token ou senha nos logs de aplicação.

Para a chave Pix, criar um perfil de pagamento de relação um-para-um com a conta e uma chave principal informada pelo titular. Isso mantém dados de identidade separados de dados de pagamento e permite que a mudança R03 aplique autorização própria ao exibir a chave a um participante. Alternativa considerada: acrescentar o campo diretamente ao modelo `User`; foi preferida a relação separada para isolar acesso e futuras regras de perfil. A chave não é validada junto a uma instituição financeira.

### Cobranças, participações e dívidas

Representar valores como inteiros em centavos. `Charge` guarda criador/recebedor, descrição, total, estado e marca de bloqueio futura. `Participation` guarda usuário, cota e estado `PENDING`, `ACCEPTED` ou `DECLINED`. `Debt` identifica a obrigação criada quando uma participação é aceita. Usar constraints de unicidade para impedir participação ativa duplicada e mais de uma dívida por participação; validar a soma das cotas no serviço transacional, pois ela depende de várias linhas.

Manter a participação recusada como histórico e substituí-la por outro usuário antes da primeira operação financeira. A nova participação continua `PENDING`; nenhuma dívida nasce da recusa. Cada aceite cria sua dívida uma só vez, mas consultas financeiras filtram por cobrança `ACTIVE`. A ativação ocorre na transação que processa o último aceite, depois de conferir todos os convites ativos e a soma das cotas.

Centralizar as regras em serviços de aplicação (`create_charge`, `calculate_shares`, `accept_participation`, `decline_participation`, `replace_declined_participant` e `activate_charge`). Views tradicionais e HTMX chamam os mesmos serviços. Ao aceitar, recusar ou substituir, bloquear a linha da cobrança no PostgreSQL dentro de `transaction.atomic()` e reforçar idempotência com constraints; isso evita que requisições concorrentes ativem duas vezes ou dupliquem dívidas.

Para centavos residuais, ordenar os participantes por identificador persistente antes de distribuir os centavos excedentes, mantendo resultado repetível para o mesmo conjunto de participantes. A participação do criador entra no total, mas nunca gera dívida contra si próprio.

### Interface e validação

Após a revisão da Wave 0, implementar as telas de conta, convite e cobrança como templates Django e fragmentos HTMX. Reutilizar o build existente em `assets/css/input.css` e `pixu/static/css/tailwind.css`; incluir templates e fragmentos no escaneamento do Tailwind. Não trazer Bootstrap por CDN nem introduzir SPA.

Toda permissão, validação de formulário, soma do rateio, transição de estado e atualização HTMX é decidida no servidor. Retornar erros no formulário sem salvar estado inválido; preservar CSRF e escape automático. Limites de campos seguem o design e são aplicados no formulário e na persistência.

### Testabilidade

Cobrir cadastro, confirmação/recuperação de e-mail, permissões, divisão com centavos, convites aceitos/recusados, substituição e ativação. Exercitar idempotência e concorrência com PostgreSQL, que é o banco usado pelo fluxo; os testes unitários de cálculo puro podem usar entradas em memória. Fixtures de usuários são opcionais, locais a desenvolvimento/testes e não substituem cadastro pela interface na jornada de aceitação.

## Risks / Trade-offs

- [E-mail local não chega a uma caixa externa] → usar backend de console no desenvolvimento e documentar configuração SMTP obrigatória para produção.
- [Cadastro público aumenta exposição a contas automatizadas] → manter confirmação por e-mail obrigatória e aplicar as proteções padrão do Django/allauth; controles antifraude ou rate limiting não são inventados neste lote.
- [Aceites concorrentes podem ativar a cobrança duas vezes] → transação com bloqueio de linha e constraints de unicidade no PostgreSQL.
- [Rateio pode divergir por arredondamento] → usar exclusivamente centavos inteiros, ordem estável para resíduos e teste que verifica a soma exata.
- [Telas implementadas antes das decisões visuais] → bloquear implementação das telas até revisar `docs/product-design.md` produzido na Wave 0.
- [R16 também menciona anexos privados] → limitar este lote à validação dos formulários de conta/cobrança; storage, acesso a arquivo e retenção ficam no lote R08/R16 de pagamentos.

## Migration Plan

1. Aprovar a Wave 0 de design e os artefatos OpenSpec antes da implementação.
2. Criar migrações para o perfil Pix, cobranças, participações e dívidas; aplicar no PostgreSQL local e em produção antes de iniciar o código novo.
3. Configurar o backend de e-mail por ambiente e habilitar cadastro público no ambiente de execução do produto; não versionar segredos SMTP.
4. Publicar templates e assets compilados junto da aplicação. Não criar ou depender de contas demo em produção.
5. Para rollback, reverter a versão da aplicação e desabilitar o cadastro por configuração; manter dados de contas e cobranças. Não remover tabelas nem descartar dados do usuário como parte do rollback.

## Open Questions

Nenhuma decisão de comportamento necessária para este lote permanece aberta. A definição visual está deliberadamente delegada à Wave 0 antes da implementação das telas.
