# Design

## Context

Consulte `proposal.md` e as specs `accounts/social-authentication` e `accounts/first-access-onboarding`. O projeto já fixa django-allauth 65.19.4, instala `allauth.socialaccount`, monta `allauth.urls` e usa adapters próprios. Ainda não instala os módulos dos provedores Google/GitHub nem configura credenciais sociais. A entrada local está limitada a nome de usuário e senha e encaminha ao dashboard. O guia visual e `docs/design/pixu_sso_onboarding_prototype.html` definem os botões sociais, os estados de primeiro acesso e o aviso de chave ausente.

## Goals / Non-Goals

**Goals:**

- Usar a infraestrutura allauth já instalada para os dois provedores solicitados.
- Preservar fluxos locais e a experiência visual existente, incluindo temas claro/escuro.
- Fazer com que a primeira visita de contas novas passe pelo onboarding, sem redirecionar contas existentes.
- Manter segredos fora do repositório e fora do banco.

**Non-Goals:**

- Usar os provedores para movimentar dinheiro, validar chave Pix ou obter permissões além de identidade e e-mail.
- Persistir access tokens ou refresh tokens, adicionar autenticação por outro provedor ou mudar para uma SPA.
- Obrigar contas existentes a preencher o onboarding.

## Decisions

- **Manter django-allauth e habilitar os módulos nativos.** Adicionar os módulos Google e GitHub a `INSTALLED_APPS`; os caminhos OAuth e callbacks permanecem sob `/accounts/`, já montado pelo projeto. Isso evita dependência ou protocolo de autenticação próprio.
- **Guardar credenciais em configuração do ambiente.** Ler `DJANGO_GOOGLE_OAUTH_CLIENT_ID`, `DJANGO_GOOGLE_OAUTH_CLIENT_SECRET`, `DJANGO_GITHUB_OAUTH_CLIENT_ID` e `DJANGO_GITHUB_OAUTH_CLIENT_SECRET` com `django-environ`. Fazer a ponte em `.envs/.local/.django` e `.envs/.production/.django.example`; os valores reais de desenvolvimento ficam no `.env` ignorado e os de produção são fornecidos pelo ambiente de implantação. Configurar `SOCIALACCOUNT_PROVIDERS` somente quando o par de cada provedor estiver completo; assim o allauth não oferece um botão que terminaria em erro por falta de credenciais. Usar a configuração em settings, sem duplicar os mesmos provedores em `SocialApp` no admin.
- **Pedir somente identidade e e-mail.** Google usa `profile` e `email`; GitHub usa `read:user` e `user:email`. Para esses dois provedores confiáveis, tratar os e-mails declarados verificados como aptos a autenticar a conta Pixu correspondente (`EMAIL_AUTHENTICATION=True`). Não habilitar conexão automática da identidade social à conta local existente (`EMAIL_AUTHENTICATION_AUTO_CONNECT=False`); contas novas mantêm a associação social criada pelo fluxo normal do allauth para logins posteriores. Deixar `SOCIALACCOUNT_STORE_TOKENS=False` explícito.
- **Iniciar OAuth por POST.** Renderizar cada provedor configurado como formulário POST com CSRF e `provider_login_url`; isso preserva o padrão recomendado pelo allauth, cujo início por GET não é habilitado. Os botões ficam antes do formulário local, usam os rótulos e dimensões definidos no guia e SVGs inline locais do protótipo. Não carregar logos ou bibliotecas por CDN.
- **Conservar a entrada tradicional por e-mail ou usuário.** Ampliar o método de login local para e-mail e username e manter cadastro, confirmação de e-mail, logout e recuperação existentes. A tela conserva os rótulos pt-BR, o divisor “ou entre com e-mail e senha”, foco visível, semântica de botão e contraste de ambos os temas.
- **Registrar estado de onboarding sem alterar contas existentes.** Adicionar `onboarding_completed` ao usuário com padrão `True` para os registros já existentes; adapters de cadastro local e social definem `False` somente ao criar conta nova. Um middleware depois da autenticação redireciona contas novas ao onboarding mesmo se o login trouxer outro `next`; rotas de autenticação e onboarding continuam acessíveis. O onboarding salva nome, username e perfil Pix numa transação; “Fazer depois” salva os dois primeiros e mantém a chave vazia. Username é validado no servidor e a sugestão visual deriva do nome enquanto a pessoa não editar o campo.
- **Mostrar estado da chave sem bloquear o produto.** O dashboard consulta o perfil Pix e mostra o aviso definido em `docs/product-design.md` quando a chave estiver vazia. O formulário de cobrança informa a ausência quando o usuário atual é o recebedor, mas segue editável; não exigir chave para participar ou criar uma cobrança destinada a outra pessoa.

## Risks / Trade-offs

- **[Credenciais e callback não configurados]** O fluxo OAuth real falha se o client ID/secret ou a URI de retorno estiver incorreto → fornecer nomes de variáveis e callbacks no README e exemplos de ambiente; não cadastrar credenciais inventadas. Callbacks de desenvolvimento: `http://127.0.0.1:8000/accounts/google/login/callback/` e `http://127.0.0.1:8000/accounts/github/login/callback/`; produção deve usar domínio e HTTPS configurados.
- **[Pareamento por e-mail]** E-mail social pode autenticar uma conta local sem criar vínculo persistente → limitar essa política aos provedores Google e GitHub com e-mail confirmado e manter a conexão automática desabilitada; não armazenar tokens.
- **[Sugestão de username repetida]** Nomes e partes locais de e-mail podem colidir → permitir edição no onboarding e validar unicidade no servidor antes de salvar; erros não alteram a conta.
- **[Interrupção em implantação]** Aplicar a migração torna o novo estado de onboarding disponível → o valor inicial verdadeiro preserva acesso de contas existentes, e apenas os adapters de cadastro marcam novas contas como pendentes.

## Migration Plan

1. Fornecer credenciais OAuth no ambiente e cadastrar no Google/GitHub os callbacks do respectivo host.
2. Implantar a mudança e aplicar migrações Django; contas existentes permanecem com onboarding concluído.
3. Novos cadastros locais e sociais passam pelo onboarding; usuários existentes mantêm o acesso e podem configurar a chave pelo perfil.
4. Para rollback, remover os módulos/configuração social e os botões. A coluna de onboarding pode permanecer sem efeito; não remover contas sociais já criadas nem os dados das migrações do allauth.
