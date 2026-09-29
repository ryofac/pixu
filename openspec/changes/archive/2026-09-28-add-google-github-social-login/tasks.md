# Tasks

## 1. Configuração dos provedores

- [x] 1.1 Habilitar os providers Google e GitHub do django-allauth e compor `SOCIALACCOUNT_PROVIDERS` a partir dos quatro valores OAuth do ambiente, com escopos mínimos, e-mail verificado, sem auto conexão de conta local e sem armazenamento de tokens; verificar a sintaxe Python com `python3 -m py_compile config/settings/base.py`.
- [x] 1.2 Declarar as variáveis nos ambientes local e de produção sem inserir segredos, documentar os callbacks e a configuração dos aplicativos OAuth no README; verificar a resolução do Compose local e a ausência de valores concretos nos arquivos versionados.

## 2. Entrada social e tradicional

- [x] 2.1 Criar o fragmento de botões Google/GitHub com SVG inline local e formulários POST com CSRF, aplicá-lo antes da entrada tradicional em pt-BR e seguir tokens e estados do guia de design; verificar a estrutura renderizada e as classes Tailwind no build local.
- [x] 2.2 Permitir entrada tradicional por e-mail ou nome de usuário e senha, mantendo cadastro, confirmação, logout e recuperação; verificar a configuração Django e o fluxo de formulários já existente.

## 3. Primeiro acesso e chave Pix

- [x] 3.1 Adicionar o estado de onboarding ao usuário, migrar contas existentes como concluídas e marcar somente novas contas tradicionais e sociais como pendentes; verificar o plano de migração e a criação do estado pelos adapters.
- [x] 3.2 Criar formulário, view, rota, template e proteção de navegação do onboarding, incluindo sugestão editável de `@username`, validação no servidor, salvamento da chave ou opção “Fazer depois”; verificar a implementação por inspeção estática e compilação Python.
- [x] 3.3 Mostrar o aviso de chave ausente no dashboard e no formulário quando a pessoa for a recebedora, sem bloquear participação nem criação; verificar a renderização condicional por inspeção estática.

## 4. Revisão integrada

- [x] 4.1 Validar todos os artefatos com `openspec validate --all --no-interactive`, executar `git diff --check` e revisar que nenhuma credencial concreta foi incluída; registrar que o handshake real exige client IDs/secrets e callbacks válidos do ambiente.
