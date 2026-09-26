# Design

## Context

O app `settlements` ainda é um esqueleto, enquanto `charges` já possui `Debt` e serviços de aceite/edição. O perfil `PixProfile` já existe em `accounts`, mas as telas de dívida e o armazenamento de comprovantes ainda não foram implementados. A mudança deve manter Django server-rendered, HTMX progressivo, valores em centavos e PostgreSQL como banco de produção.

## Goals / Non-Goals

**Goals:**

- Modelar pagamentos com estados pendente, confirmado e rejeitado, auditoria de confirmação e referência opcional.
- Calcular saldo aberto e reservas a partir de eventos confirmados e pendentes, com transações e bloqueios de linha.
- Validar, criar, substituir e remover comprovantes em armazenamento privado local ou S3-like, com rota autenticada de download.
- Exibir chave Pix somente no contexto de uma dívida acessível e conectar ações a templates responsivos existentes.
- Marcar `Charge.locked_at` na primeira operação financeira e reutilizar a guarda em todos os serviços de edição.
- Consolidar idioma pt-BR, parsing monetário localizado e navegação responsiva nas páginas próprias, fragmentos HTMX e telas de conta do django-allauth.

**Non-Goals:**

- Integração bancária, carteira, QR Code, confirmação automática ou pagamento para várias dívidas.
- Correção de valores já registrados; o fluxo é rejeitar e registrar outro pagamento.
- Retenção automática, antivírus externo ou armazenamento em nuvem específico; o contrato de armazenamento privado será abstraído.
- Dashboard completo e compensações recíprocas, que pertencem aos lotes posteriores.

## Decisions

1. **Eventos de pagamento como fonte de saldo.** Criar `Payment` ligado a `Debt`, com valor inteiro em centavos, estado e campos de auditoria. O saldo será uma consulta/serviço derivado de pagamentos `CONFIRMED`; reservas somam pagamentos `PENDING`. Não duplicar saldo materializado enquanto o volume não exigir, evitando divergência.

2. **Transações com bloqueio determinístico.** `record_payment` bloqueia a dívida e a cobrança, verifica estado e disponibilidade, cria o pagamento e define `Charge.locked_at` na mesma transação. `confirm_payment` e `reject_payment` bloqueiam a dívida, o pagamento e a cobrança em ordem estável, validam o recebedor e tratam estados finais como operações idempotentes.

3. **Storage privado por abstração Django.** O comprovante usa `FileField` com o storage configurado em `STORAGES["default"]`, sem assumir filesystem local. O caminho é não previsível sob `private_uploads/` e não é servido por `MEDIA_URL`; S3-like usa bucket privado e URLs assinadas não são expostas diretamente. Uma view de download busca o pagamento por identificador, autoriza pagador/recebedor e transmite o objeto; falhas de tipo, tamanho ou conteúdo são rejeitadas antes de persistir.

4. **Ciclo de vida explícito do arquivo.** Serviços separados criam, substituem e removem comprovantes. Substituição salva o novo objeto, atualiza os metadados e remove o objeto antigo somente após a nova referência estar persistida; deleção limpa o campo e o objeto de storage. Essas operações são permitidas apenas ao pagador enquanto `PENDING`, em transação e sem alterar valores financeiros.

5. **Validação de conteúdo configurável.** Definir limite e tipos permitidos nas configurações, declarados nos `.envs` conforme a regra do projeto e com valores locais concretos no `.env` ignorado. A validação combina extensão, MIME informado e assinatura básica (PDF/JPEG/PNG), sem confiar somente no nome do arquivo.

6. **Serviços separados das views.** Implementar `record_payment`, `confirm_payment`, `reject_payment`, `replace_receipt`, `delete_receipt`, `payment_balance` e autorização de download em serviços testáveis. Views apenas montam formulários, chamam serviços e renderizam páginas ou fragmentos HTMX.

7. **Experiência de estados.** O detalhe da dívida mostra valor original, confirmado, pendente/reservado e saldo aberto. A confirmação usa texto “Confirme somente depois de conferir o recebimento no seu banco”; comprovante é apoio de conferência, nunca gatilho automático.

8. **Configuração e migração segura.** Adicionar as variáveis de tamanho/tipos de anexo e do backend S3-like aos bridges `.envs/.local/.django` e `.envs/.production/.django.example`; criar migrações reversíveis e manter `PixProfile` sem dados reais em fixtures.

9. **Garage local.** O Compose local adicionará Garage em modo single-node, com volumes persistentes, bucket privado e credenciais somente no `.env` ignorado. Django e worker usarão o endpoint S3 interno configurável, permitindo validar criação, download, substituição e deleção sem depender de um provedor externo. A ausência de redundância é aceitável somente para o ambiente local de validação.

10. **Internacionalização pelo Django.** Textos de Python, forms, templates próprios e mensagens de domínio usarão as APIs de tradução do Django (`gettext`, `ngettext`, `{% translate %}` e `{% blocktranslate %}` conforme o contexto), com catálogo pt-BR compilado. Telas do django-allauth serão traduzidas pela localidade configurada e terão templates próprios somente quando a estrutura visual do produto exigir; não serão criados dicionários paralelos nem strings inglesas duplicadas no frontend.

11. **Formato monetário localizado na borda.** A entrada de dinheiro aceitará a vírgula decimal usada no pt-BR e normalizará o valor no servidor antes de convertê-lo em centavos. A saída usará um formatador único com duas casas e vírgula. Aceitar ponto como compatibilidade adicional não altera a representação exibida. A alternativa de corrigir a entrada apenas com JavaScript foi rejeitada porque não cobre POST convencional, HTMX nem clientes sem JavaScript.

12. **Auditoria responsiva como contrato de tela.** A base de templates continuará usando os breakpoints nativos do Tailwind, mas cada tela de conta, cobrança e pagamento será verificada em viewport móvel e desktop. A navegação inferior terá espaçamento de área segura no fim do conteúdo, a navegação lateral será usada em telas largas e as rotas do allauth deverão indicar a seção ativa. A alternativa de aceitar o overlay da navegação como comportamento esperado foi rejeitada porque pode esconder campos e ações.

13. **Higiene dos dados de demonstração.** Fixtures e dados locais visíveis durante a revisão deverão usar textos sem erros ortográficos ou conteúdo impróprio para uma interface de produto. Esses dados continuarão separados de fixtures de produção e não receberão dados pessoais reais.

## Risks / Trade-offs

- **[Configuração S3 incompatível entre provedores]** → limitar o contrato a APIs S3-like, manter endpoint/região/bucket configuráveis e validar no Garage local.
- **[Armazenamento local não escalável]** → encapsular o storage e documentar que produção precisa de bucket privado persistente; o fallback local continua útil para testes, sem expor o diretório por Nginx.
- **[MIME adulterado ou arquivo malformado]** → conferir assinatura e tamanho antes de salvar e limitar extensões aceitas.
- **[Corrida entre confirmação e novo pagamento]** → bloquear `Debt`/`Payment` dentro de `transaction.atomic()` e cobrir concorrência no PostgreSQL; SQLite será usado apenas para testes unitários simples.
- **[Migração de cobranças existentes]** → manter `locked_at` nulo para registros anteriores e derivar saldo sem alterar dívidas já criadas.
- **[HTMX pode esconder erros de autorização]** → usar os mesmos serviços e respostas de erro para requisições convencionais e HTMX, com testes de ambos os caminhos.
- **[Catálogos incompletos deixam mensagens inglesas]** → auditar telas allauth e próprias, compilar o catálogo pt-BR e exercitar erros de validação em smoke tests autenticados.
- **[Vírgula e ponto podem ser confundidos na entrada monetária]** → normalizar somente na borda, validar ambiguidade no servidor e cobrir `150,00`, `150.00` e entradas inválidas.
- **[Templates allauth podem divergir após atualização]** → manter overrides mínimos, verificar a versão instalada e incluir as rotas de conta no inventário visual.
- **[Navegação fixa cobre campos em telas longas]** → reservar área segura no layout, testar rolagem até o último campo em mobile e rejeitar overflow horizontal.

## Migration Plan

1. Adicionar configurações de anexo e storage, criar o bucket privado do Garage local e gerar migrações de `settlements`/eventuais constraints de `charges`.
2. Publicar aplicação e worker já existentes; executar `migrate` antes de habilitar os formulários de pagamento.
3. Verificar bucket privado, endpoint, credenciais e persistência antes de aceitar uploads; executar smoke test de criação, download, substituição e deleção no Garage.
4. Em rollback, desabilitar as rotas/formulários novos sem apagar pagamentos; objetos órfãos devem ser reconciliados antes de remover migrações.
5. Gerar/atualizar o catálogo pt-BR, compilar traduções, revisar templates allauth e aplicar a normalização monetária antes de liberar a próxima rodada visual.
6. Repetir a revisão autenticada em mobile e desktop, incluindo prévia HTMX, conta/e-mail, detalhe da cobrança e comprovante privado; registrar erros de console, overflow e mensagens não traduzidas.

## Open Questions

Nenhuma decisão em aberto que altere o contrato ou a abordagem deste lote.
