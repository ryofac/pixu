## Context

Ver `proposal.md` para motivação e `specs/accounts/spec.md` e `specs/charges/spec.md` para os contratos. O repositório já contém configuração de Django/allauth, PostgreSQL, middleware CSRF, templates, HTMX e build local do Tailwind. A implementação parcial inclui perfil Pix, modelos e serviços de cobrança, além de páginas iniciais. Esta aplicação completa esses fluxos, conecta formulários de cotas e substituição e organiza as telas para mobile e desktop.

`docs/product-design.md` e `docs/design/pixu-first-vision-wireframes.md` registram a nova hierarquia responsiva: navegação inferior no celular e lateral em `lg`, usando os breakpoints nativos do Tailwind. A primeira versão é online; ações só aparecem como concluídas após resposta do servidor. Comprovantes privados pertencem ao lote de pagamentos posterior.

## Goals / Non-Goals

**Goals:**

- Integrar cadastro e recuperação de senha por e-mail ao allauth já instalado e permitir editar o perfil próprio.
- Criar cobranças e participações com cotas inteiras, convite/aceite/recusa e ativação após todas as respostas válidas.
- Criar uma dívida por participante aceito, sem duplicidade e sem incluí-la nos totais enquanto a cobrança não estiver ativa.
- Preservar autorização no servidor e a experiência progressiva com Django templates, HTMX e Tailwind compilado localmente.

**Non-Goals:**

- Implementar pagamentos, confirmação de Pix, comprovantes, compensações ou dashboard.
- Implementar tema escuro ou seleção Claro/Escuro/Sistema. Esse trabalho está mapeado para `complete-product-experience` em `TODO.md` (`TEMA-01` a `TEMA-05`) e `docs/product-design.md`, seção 2.4.
- Validar chaves Pix com bancos, processar transferências ou criar carteira.
- Exigir ou semear Ryan, Ana, Bruno e Carla em ambientes de produto; fixtures de exemplo são opcionais e restritas a desenvolvimento/testes.
- Implementar as telas sem revisão de `docs/product-design.md`.

## Decisions

### Contas e e-mail

Manter django-allauth como fluxo público de cadastro, sessão e recuperação. Configurar `DJANGO_ACCOUNT_ALLOW_REGISTRATION=True` nos ambientes local e de produção do produto; a variável continua disponível para pausar cadastros quando necessário. Manter a confirmação de e-mail obrigatória que já está configurada. O cadastro continua por e-mail, nome de usuário e senha, e o login usa nome de usuário conforme `ACCOUNT_LOGIN_METHODS`. Não adicionar provedores sociais.

Usar backend de console no ambiente local para que confirmações e links de recuperação sejam visíveis durante o desenvolvimento; produção usa o SMTP configurado em `.envs/.production/.django`. Para a primeira operação, o exemplo de produção adota uma conta Google dedicada com `smtp.gmail.com`, STARTTLS na porta 587 e senha de app; o endereço completo da conta é o usuário SMTP e também o remetente padrão. Em uma organização Google Workspace com maior volume ou política centralizada, o relay SMTP do Workspace pode substituir essa configuração. Alterar a senha principal da conta exige gerar uma nova senha de app. Não registrar token, senha de app ou senha de conta nos logs de aplicação.

Para a chave Pix, criar um perfil de pagamento de relação um-para-um com a conta e uma chave principal informada pelo titular. Isso mantém dados de identidade separados de dados de pagamento e permite que a mudança R03 aplique autorização própria ao exibir a chave a um participante. Alternativa considerada: acrescentar o campo diretamente ao modelo `User`; foi preferida a relação separada para isolar acesso e futuras regras de perfil. A chave não é validada junto a uma instituição financeira.

### Cobranças, participações e dívidas

Representar valores como inteiros em centavos. `Charge` guarda criador e recebedor em relações separadas, descrição, total, estado e marca de bloqueio futura. O recebedor é uma conta ativa selecionável, inicialmente o criador, e pode estar fora do rateio. `Participation` guarda usuário, cota e estado `PENDING`, `ACCEPTED` ou `DECLINED`. `Debt` identifica a obrigação criada quando uma participação é aceita e aponta ao recebedor da cobrança. Usar constraints de unicidade para impedir participação ativa duplicada e mais de uma dívida por participação; validar a soma das cotas no serviço transacional, pois ela depende de várias linhas.

Manter a participação recusada como histórico e substituí-la por outro usuário antes da primeira operação financeira. A nova participação continua `PENDING`; nenhuma dívida nasce da recusa. Cada aceite cria sua dívida uma só vez, mas consultas financeiras filtram por cobrança `ACTIVE`. A ativação ocorre na transação que processa o último aceite, depois de conferir todos os convites ativos e a soma das cotas.

Centralizar as regras em serviços de aplicação (`create_charge`, `calculate_shares`, `accept_participation`, `decline_participation`, `replace_declined_participant` e `activate_charge`). Views tradicionais e HTMX chamam os mesmos serviços. Ao aceitar, recusar ou substituir, bloquear a linha da cobrança no PostgreSQL dentro de `transaction.atomic()` e reforçar idempotência com constraints; isso evita que requisições concorrentes ativem duas vezes ou dupliquem dívidas.

Para centavos residuais, ordenar os participantes por identificador persistente antes de distribuir os centavos excedentes, mantendo resultado repetível para o mesmo conjunto de participantes. O criador escolhe se participa; se participar, sua cota é aceita na criação e gera dívida quando o recebedor for outra pessoa. Nenhuma participação do recebedor gera dívida contra si próprio. A autoria permanece com quem realizou a criação.

Na criação, aceitar cotas manuais completas, não negativas, inteiras em centavos e com soma exata. A revisão funciona por HTMX e POST convencional. Alterar total ou seleção de participantes recalcula o rateio padrão; ao submeter cotas inválidas, preservar entradas e apresentar erros sem persistir cobrança.

O criador pode editar sua cota e cotas pendentes antes de operação financeira; dívidas próprias devem ser sincronizadas na mesma transação. Trocar o recebedor exige que nenhuma participação de outra pessoa tenha sido aceita. A troca e os aceites usam o mesmo bloqueio de linha da cobrança, preservando o recebedor consentido por cada convidado. O recebedor tem acesso de leitura mesmo sem participação, mas edição continua exclusiva do criador. A seleção de participação do criador ocorre na criação.

O POST de aceite inclui a cota e o recebedor exibidos no convite. Dentro da transação, comparar esses valores com os atuais e rejeitar aceite desatualizado, devolvendo o convite atualizado para conferência. Isso evita aceitar inadvertidamente uma edição feita enquanto a tela estava aberta.

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
2. Criar migrações para o perfil Pix, cobranças, participações e dívidas; aplicar no PostgreSQL local e em produção antes de iniciar o código novo. Para separar o recebedor em cobranças existentes, adicionar a relação temporariamente anulável, preencher com o criador e torná-la obrigatória, preservando as dívidas e os aceites já registrados.
3. Configurar o backend de e-mail por ambiente e habilitar cadastro público no ambiente de execução do produto; não versionar segredos SMTP.
4. Publicar templates e assets compilados junto da aplicação. Não criar ou depender de contas demo em produção.
5. Para rollback, reverter a versão da aplicação e desabilitar o cadastro por configuração; manter dados de contas e cobranças. Não remover tabelas nem descartar dados do usuário como parte do rollback.

## Open Questions

Nenhuma decisão de comportamento necessária para este lote permanece aberta. Offline-first está fora desta versão; a compreensão dos rótulos de estado ainda precisa de validação com usuários.
