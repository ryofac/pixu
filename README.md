# Pixu

<p align="center">
  <img src="pixu/static/images/pixu-logo.svg" alt="Símbolo da marca Pixu" width="112">
  <br><strong style="font-size: 2rem">PiXu</strong>
</p>

<p align="center"><strong>Divida despesas com clareza e acompanhe cada obrigação.</strong></p>

O Pixu ajuda amigos a combinar o rateio de uma despesa, acompanhar os pagamentos e compensar dívidas recíprocas. Cada pessoa vê sua cota e o estado da própria participação.

## Como funciona

1. Crie uma conta e, se quiser receber pagamentos, informe sua chave Pix no perfil.
2. Crie uma cobrança, escolha quem recebe, revise as cotas e convide outras contas do Pixu.
3. Cada pessoa convidada confere os termos e aceita ou recusa sua participação. A dívida só é ativada depois dos aceites necessários.
4. O pagamento é feito fora do Pixu. Quem pagou pode registrar o valor enviado e anexar um comprovante privado; quem recebe confere e confirma ou rejeita o registro.
5. Quando existem dívidas abertas nos dois sentidos entre as mesmas pessoas, o Pixu pode sugerir uma compensação. Ela reduz os saldos opostos pelo mesmo valor, sem representar uma transferência.

## O que você encontra no Pixu

- Um painel com cobranças, convites, valores em aberto a pagar e a receber, e compensações potenciais apresentadas separadamente.
- Divisão com cotas revisáveis e indicação clara de quem criou, participa e recebe cada cobrança.
- Registro de pagamentos parciais e comprovantes acessíveis somente a quem pagou e a quem recebe.
- Aparência **Sistema**, **Claro** ou **Escuro**, disponível em telas móveis e desktop.

## Importante

O Pixu não movimenta dinheiro, não verifica chaves Pix junto a bancos e não confirma pagamentos automaticamente. A transferência é feita no aplicativo bancário; a confirmação no Pixu é manual e cabe ao recebedor. Uma compensação apenas abate dívidas recíprocas — não cria carteira nem transfere valores.

## Desenvolvimento e deploy

### Tecnologias e estrutura

- Python 3.14 e Django 6.0.8; PostgreSQL 18, Redis e Celery 5.6.
- Django templates e HTMX 2.0.11; Tailwind CSS 4.3.3 compilado localmente, sem CDN.
- Docker Compose no desenvolvimento e produção; Gunicorn, Nginx, WhiteNoise e Traefik no deploy.
- `config/` contém settings e URLs; `pixu/accounts/`, `charges/`, `settlements/` e `dashboard/` concentram os domínios; templates ficam em `pixu/templates/` e a entrada Tailwind em `assets/css/`.
- `openspec/` guarda propostas, requisitos e tarefas; `docs/product-design.md` registra decisões de interface.

### Executar localmente

Requisitos: Docker com Compose, Node.js 20.19 ou superior e npm. Para executar comandos Python fora do container, instale Python 3.14 e `uv`.

```sh
npm ci
npm run build
docker compose -f docker-compose.local.yml up --build
```

A aplicação fica em `http://localhost:8000`. O Compose local inicia Django, PostgreSQL, Redis, o worker do Celery e o Garage. As migrações são aplicadas ao iniciar o Django. Para recompilar CSS enquanto edita templates, rode `npm run css:watch` em outro terminal. O modo local padrão usa e-mail de console: confirmações de conta e redefinições aparecem nos logs do Django, sem envio pela internet.

Para experimentar a aplicação, abra `/accounts/signup/`, crie uma conta e confirme o endereço pelo link que aparece em `just logs django`. Depois entre em `/accounts/login/`. Para criar uma conta administrativa local, rode `just manage createsuperuser`.

Os testes mais usados são:

```sh
just pytest
just e2e
```

`just pytest` roda a suíte Python sem navegador. `just e2e` compila os assets e roda Playwright/Chromium com um PostgreSQL de teste isolado. Para executar um cenário específico, passe seu caminho, por exemplo `just e2e tests/e2e/test_charges.py`. Para atualizar screenshots documentais, use `just e2e tests/e2e/test_capture_screenshots.py`. Falhas E2E podem guardar traces, screenshots e vídeos em `test-results/`.

Comandos Python fora do Docker:

```sh
uv sync --locked --group dev
```

Comandos de manutenção disponíveis no `justfile`:

```sh
just manage migrate
just manage check
just pytest
just e2e
just logs django
```

Para testar a fila de e-mail localmente, configure no `.env` `DJANGO_EMAIL_BACKEND=pixu.accounts.email_backends.CeleryEmailBackend` e `CELERY_EMAIL_DELIVERY_BACKEND=django.core.mail.backends.console.EmailBackend`, depois acompanhe `just logs celeryworker`. O backend padrão local é síncrono e apenas imprime mensagens nos logs do Django.

### Configuração e segredos

O Compose local lê `.envs/.local/.django`, `.envs/.local/.postgres` e `.env`; o Compose de produção lê `.envs/.production/.django` e `.envs/.production/.postgres`. Ao adicionar uma configuração por ambiente, declare a variável no código com leitura tipada por `django-environ`, faça a ponte no `.envs` correspondente usando `${NOME_DA_VARIÁVEL}` e mantenha o valor concreto somente no `.env` ignorado pelo Git. Em produção, use esse `.env` ou o cofre de segredos do deploy. Mantenha os exemplos versionados sem credenciais reais.

Exemplo do padrão:

```dotenv
# .envs/.production/.django
DJANGO_EMAIL_HOST_PASSWORD=${DJANGO_EMAIL_HOST_PASSWORD}
PIXU_S3_SECRET_ACCESS_KEY=${PIXU_S3_SECRET_ACCESS_KEY}

# .env (ignorado pelo Git)
DJANGO_EMAIL_HOST_PASSWORD=VALOR_CONFIGURADO_LOCALMENTE
PIXU_S3_SECRET_ACCESS_KEY=VALOR_CONFIGURADO_LOCALMENTE
```

### Storage S3-like e comprovantes

O ambiente local inclui o [Garage](https://garagehq.deuxfleurs.fr/documentation/quick-start/) em modo single-node para validar o fluxo S3-like; ele não oferece redundância e não deve ser tratado como serviço de produção. A API S3 local publica a porta `3900`: a partir do container Django, use `http://garage:3900`; a partir da máquina host, use `http://localhost:3900`. O endpoint administrativo usa a porta `3903`. Os dados ficam nos volumes `pixu_local_garage_data` e `pixu_local_garage_config`.

A configuração Django seleciona o backend por `PIXU_STORAGE_BACKEND`. Para Garage ou outro serviço S3-compatible, defina `PIXU_STORAGE_BACKEND=storages.backends.s3.S3Storage` e configure pelo `.env` as variáveis abaixo, redirecionadas nos arquivos `.envs` correspondentes.

| Variável | Função |
| --- | --- |
| `PIXU_S3_BUCKET_NAME` | Bucket privado para comprovantes. |
| `PIXU_S3_ENDPOINT_URL` | Endpoint S3; local: `http://garage:3900` dentro do Compose. |
| `PIXU_S3_REGION_NAME` | Região esperada pelo provedor S3-like. |
| `PIXU_S3_ACCESS_KEY_ID` | Identificador de acesso com escopo limitado ao bucket. |
| `PIXU_S3_SECRET_ACCESS_KEY` | Segredo correspondente; nunca versionar ou registrar em logs. |
| `PIXU_S3_ADDRESSING_STYLE` | Estilo suportado pelo provedor: `auto`, `path` ou `virtual`. |
| `PIXU_S3_USE_SSL` | `True` para endpoints remotos com TLS; `False` somente no Garage local. |

Para validar pelo Django em Compose, o endpoint local deve ser `http://garage:3900`; `localhost` dentro do container aponta para o próprio container Django. Para uma ferramenta executada diretamente na máquina host, use `http://localhost:3900`. A região usada pelo cliente e pelo Garage deve coincidir. Não publique o bucket e não habilite ACL pública.

O arquivo `.envs/.local/.django` deve redirecionar `PIXU_STORAGE_BACKEND` e `PIXU_S3_*` com `${NOME}`. O Garage lê `.envs/.local/.garage`; esse arquivo deve redirecionar `GARAGE_RPC_SECRET`, `GARAGE_ADMIN_TOKEN`, `GARAGE_METRICS_TOKEN`, `GARAGE_DEFAULT_ACCESS_KEY`, `GARAGE_DEFAULT_SECRET_KEY`, `GARAGE_DEFAULT_BUCKET` e `PIXU_S3_REGION_NAME`. Use o mesmo nome de bucket, região e credenciais S3 nos dois serviços: `GARAGE_DEFAULT_BUCKET` corresponde a `PIXU_S3_BUCKET_NAME`, e as credenciais default do Garage correspondem a `PIXU_S3_ACCESS_KEY_ID` e `PIXU_S3_SECRET_ACCESS_KEY`. Configure os valores concretos somente no `.env` local. Em produção, redirecione os valores S3 por `.envs/.production/.django` e forneça as credenciais do provedor pelo `.env` ou cofre de segredos.

Os volumes de dados do Garage e PostgreSQL persistem entre reinicializações. O comando `docker compose down -v` remove esses volumes; use-o somente quando quiser descartar os dados locais de desenvolvimento, nunca como limpeza de rotina nem em produção.

Modelo dos bridges de storage em `.envs/.production/.django`:

```dotenv
PIXU_STORAGE_BACKEND=${PIXU_STORAGE_BACKEND}
PIXU_S3_BUCKET_NAME=${PIXU_S3_BUCKET_NAME}
PIXU_S3_ENDPOINT_URL=${PIXU_S3_ENDPOINT_URL}
PIXU_S3_REGION_NAME=${PIXU_S3_REGION_NAME}
PIXU_S3_ACCESS_KEY_ID=${PIXU_S3_ACCESS_KEY_ID}
PIXU_S3_SECRET_ACCESS_KEY=${PIXU_S3_SECRET_ACCESS_KEY}
PIXU_S3_ADDRESSING_STYLE=${PIXU_S3_ADDRESSING_STYLE}
PIXU_S3_USE_SSL=${PIXU_S3_USE_SSL}
```

O Compose de produção não inicia o Garage. Para guardar comprovantes em um provedor S3-like, configure um endpoint externo; mantenha o bucket privado e use credenciais com o menor escopo possível. Os comprovantes usam o prefixo privado `private_uploads/`, não são publicados como mídia estática e são servidos pela aplicação somente a quem pagou ou recebe a dívida. O limite e os tipos permitidos são configurados por `PIXU_RECEIPT_MAX_BYTES` e `PIXU_RECEIPT_ALLOWED_TYPES` (por padrão, 10 MiB e PDF/JPEG/PNG). Após configurar o provedor, valide upload, leitura autorizada e recusa de acesso a outra conta.

### E-mail SMTP

Em produção, `DJANGO_EMAIL_BACKEND` deve ser `pixu.accounts.email_backends.CeleryEmailBackend`, que enfileira a mensagem após o commit da transação; o worker a entrega usando `CELERY_EMAIL_DELIVERY_BACKEND`. Configure este último como `django.core.mail.backends.smtp.EmailBackend` para envio SMTP.

Para usar Gmail SMTP, configure uma conta dedicada à aplicação: `DJANGO_EMAIL_HOST=smtp.gmail.com`, `DJANGO_EMAIL_PORT=587`, `DJANGO_EMAIL_USE_TLS=True`, `DJANGO_EMAIL_USE_SSL=False` e `DJANGO_EMAIL_HOST_USER` com o endereço completo. Defina `DJANGO_DEFAULT_FROM_EMAIL` e `DJANGO_SERVER_EMAIL` com o remetente autorizado. A porta 587 usa TLS/STARTTLS. A implementação atual usa credenciais SMTP, não OAuth; se optar por senha de app, ative a verificação em duas etapas, crie uma senha exclusiva para a aplicação e guarde-a em `DJANGO_EMAIL_HOST_PASSWORD`. O Google recomenda OAuth quando disponível e informa que senhas de app exigem verificação em duas etapas. Consulte a [documentação SMTP do Gmail](https://developers.google.com/workspace/gmail/imap/imap-smtp) e as [regras para senhas de app](https://support.google.com/accounts/answer/185833?hl=pt-BR).

O Google revoga senhas de app quando a senha principal da conta muda. Se a conta não permitir senhas de app por política da organização ou proteção avançada, não enfraqueça as proteções: use OAuth se a aplicação tiver suporte ou configure o relay autorizado pelo administrador Workspace.

Exemplo das pontes e dos valores esperados (substitua o e-mail e a senha de app localmente; não versione o `.env`):

```dotenv
# .envs/.production/.django
DJANGO_EMAIL_BACKEND=${DJANGO_EMAIL_BACKEND}
CELERY_EMAIL_DELIVERY_BACKEND=${CELERY_EMAIL_DELIVERY_BACKEND}
DJANGO_EMAIL_HOST=${DJANGO_EMAIL_HOST}
DJANGO_EMAIL_PORT=${DJANGO_EMAIL_PORT}
DJANGO_EMAIL_HOST_USER=${DJANGO_EMAIL_HOST_USER}
DJANGO_EMAIL_HOST_PASSWORD=${DJANGO_EMAIL_HOST_PASSWORD}
DJANGO_EMAIL_USE_TLS=${DJANGO_EMAIL_USE_TLS}
DJANGO_EMAIL_USE_SSL=${DJANGO_EMAIL_USE_SSL}
DJANGO_DEFAULT_FROM_EMAIL=${DJANGO_DEFAULT_FROM_EMAIL}
DJANGO_SERVER_EMAIL=${DJANGO_SERVER_EMAIL}

# .env (ignorado pelo Git)
DJANGO_EMAIL_BACKEND=pixu.accounts.email_backends.CeleryEmailBackend
CELERY_EMAIL_DELIVERY_BACKEND=django.core.mail.backends.smtp.EmailBackend
DJANGO_EMAIL_HOST=smtp.gmail.com
DJANGO_EMAIL_PORT=587
DJANGO_EMAIL_HOST_USER=pixu-app@example.com
DJANGO_EMAIL_HOST_PASSWORD=SENHA_DE_APP_SECRETA
DJANGO_EMAIL_USE_TLS=True
DJANGO_EMAIL_USE_SSL=False
DJANGO_DEFAULT_FROM_EMAIL="Pixu <pixu-app@example.com>"
DJANGO_SERVER_EMAIL="Pixu <pixu-app@example.com>"
```

Mantenha as pontes de SMTP e Celery em `.envs/.production/.django` e os valores no `.env` ignorado ou no cofre de segredos. O broker e o backend de resultados do Celery usam Redis, configurado por `CELERY_BROKER_URL` e `CELERY_RESULT_BACKEND`; o `celeryworker` precisa permanecer ativo. Depois do deploy, teste uma recuperação de senha real em uma caixa autorizada e confira os logs do worker. Para contas Workspace, confirme as políticas com o administrador ou avalie o relay SMTP descrito na [documentação de envio do Workspace](https://support.google.com/a/answer/176600).

### Deploy de produção

1. Crie os arquivos runtime a partir dos exemplos:

   ```sh
   cp .envs/.production/.django.example .envs/.production/.django
   cp .envs/.production/.postgres.example .envs/.production/.postgres
   ```

   Mantenha os exemplos versionados sem credenciais reais. Nos arquivos runtime, use bridges `${NOME_DA_VARIÁVEL}`; os valores concretos ficam no `.env` ignorado ou são injetados pelo cofre de segredos do deploy. Por exemplo:

   ```dotenv
   # .envs/.production/.django
   DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
   DJANGO_ALLOWED_HOSTS=${DJANGO_ALLOWED_HOSTS}

   # .envs/.production/.postgres
   POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

   # .env (ignorado pelo Git) ou secret manager
   DJANGO_SECRET_KEY=VALOR_ALEATORIO_LONGO
   DJANGO_ALLOWED_HOSTS=example.com,www.example.com
   POSTGRES_PASSWORD=SENHA_FORTE
   ```

2. Configure uma `DJANGO_SECRET_KEY` longa e aleatória, senha forte do PostgreSQL, domínio em `DJANGO_ALLOWED_HOSTS`, registro DNS, SMTP, Redis/Celery e storage privado. Configure também o hostname e o e-mail de certificado em `compose/production/traefik/traefik.yml`.
3. Compile os assets e suba o Compose de produção:

   ```sh
   npm ci
   npm run build
   docker compose -f docker-compose.production.yml up --build -d
   ```

   O conjunto inclui Django/Gunicorn, `celeryworker`, PostgreSQL, Redis, Nginx e Traefik com HTTPS. DNS e acesso às portas 80/443 precisam estar prontos para emissão do certificado.
4. Verifique os serviços e logs:

   ```sh
   docker compose -f docker-compose.production.yml ps
   docker compose -f docker-compose.production.yml logs -f django celeryworker
   ```

   Então teste login, recuperação de senha, envio e leitura autorizada de comprovantes e o acesso negado para uma conta que não seja pagador nem recebedor. Configure backups independentes para o PostgreSQL e para o bucket privado; os volumes locais e o Garage single-node não são estratégia de backup de produção.

### Fluxo de contribuição e regras do produto

Antes de implementar uma funcionalidade, leia [PIXU_IMPLEMENTATION_BRIEF.md](PIXU_IMPLEMENTATION_BRIEF.md) e confira a mudança OpenSpec ativa em `openspec/`; trabalhe em uma mudança por vez. Para telas novas ou alterações visuais, reconcilie primeiro as referências em `docs/design/`, conclua a Wave 0 e registre as decisões em [docs/product-design.md](docs/product-design.md). Esse documento é a referência de produto para a interface.

Preserve a arquitetura Django: templates renderizados no servidor e HTMX para interações incrementais. Tailwind deve ser compilado localmente com npm; mantenha `package-lock.json` e `uv.lock` coerentes com alterações de dependências. Não use CDN, SPA ou API pública sem escopo aprovado. A interface deve ser pt-BR, responsiva e acessível.

Valores monetários são inteiros em centavos e toda autorização e validação deve ocorrer no servidor, inclusive em requisições HTMX. Transferências registradas e abatimentos por compensação são conceitos distintos e devem preservar a auditoria. O pagamento acontece fora do Pixu; não adicione integração bancária nem confirmação automática. Comprovantes são privados e só podem ser acessados pelo pagador e pelo recebedor.
