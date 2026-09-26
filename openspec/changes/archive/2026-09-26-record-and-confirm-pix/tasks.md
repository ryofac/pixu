# Tasks

## 1. Domínio e persistência

- [x] 1.1 Criar modelos `Payment` e metadados do comprovante no app `settlements`, com estados, constraints, índices e relações com `Debt`/usuários.
- [x] 1.2 Criar migrações reversíveis e registrar o app/rotas necessárias sem alterar dados reais de fixtures.
- [x] 1.3 Implementar serviços transacionais para saldo aberto, reservas, registro, confirmação e rejeição idempotentes, além da marcação de `Charge.locked_at`.
- [x] 1.4 Ajustar serviços de edição de cobrança para recusarem qualquer alteração após pagamento registrado, inclusive rejeitado.

## 2. Comprovantes e configuração

- [x] 2.1 Declarar limite e tipos de comprovante em `config/settings` e nos bridges `.envs`, com valores locais somente no `.env` ignorado.
- [x] 2.2 Configurar storage Django local e S3-like por ambiente, com bucket, endpoint, região, credenciais e opção de endereço; manter segredos somente no `.env` ignorado.
- [x] 2.3 Adicionar Garage em modo single-node ao `docker-compose.local.yml`, com volumes persistentes, criação automática do bucket privado e variáveis ligadas ao Django/worker.
- [x] 2.4 Implementar validação de tamanho, MIME e assinatura de PDF/JPEG/PNG, armazenamento privado e view autenticada de download.
- [x] 2.5 Implementar serviços autorizados para substituir/editar e remover comprovantes, apagando objetos antigos sem alterar estado ou saldo.
- [x] 2.6 Documentar no README a persistência, configuração S3-like/Garage e proteção do armazenamento privado sem publicar URLs de mídia.

## 3. Formulários e telas

- [x] 3.1 Exibir/editar a chave Pix do próprio usuário e mostrar a chave atual do recebedor no fluxo de pagamento, com aviso de não verificação bancária.
- [x] 3.2 Criar formulário e view para registrar pagamento parcial com referência e comprovante opcional, por POST convencional e fragmento HTMX.
- [x] 3.3 Criar ações do recebedor para confirmar/rejeitar e renderizar estados, auditoria e totais (aberto, pendente, confirmado) no detalhe da dívida.
- [x] 3.4 Aplicar layout responsivo existente: mobile-first e composição própria em `md:`/`lg:`/`xl:`, sem breakpoints CSS paralelos.

## 4. Autorização, testes e validação

- [x] 4.1 Testar regras de acesso do devedor, recebedor, terceiro e download de comprovante, incluindo CSRF e requisições HTMX.
- [x] 4.2 Testar valores inválidos, reservas, confirmação/rejeição idempotentes, bloqueio definitivo e concorrência no banco de produção quando disponível.
- [x] 4.3 Testar ciclo de vida do comprovante no Garage: criação, download autorizado, substituição, deleção e ausência de acesso público.
- [x] 4.4 Executar lint, migrações/check, suíte de testes, build Tailwind, smoke test do Garage e `git diff --check`; registrar evidências nesta mudança.

## 5. Internacionalização e consistência visual

- [x] 5.1 Inventariar textos visíveis das telas próprias, forms, validators, mensagens e fragmentos HTMX; substituir strings fixas por APIs de internacionalização do Django e verificar que o catálogo pt-BR cobre o inventário.
- [x] 5.2 Traduzir e/ou sobrescrever os templates do django-allauth para login, cadastro, recuperação, confirmação e gerenciamento de e-mail; verificar em cada rota que títulos, rótulos, placeholders, ações, ajuda e erros aparecem em pt-BR.
- [x] 5.3 Ajustar o parser monetário server-side para aceitar `150,00`, normalizar para centavos e exibir duas casas com vírgula; verificar POST convencional, prévia HTMX, ponto compatível e entradas inválidas sem alterar dados.
- [x] 5.4 Aplicar pluralização traduzível com `ngettext`/`blocktranslate count` para pessoas disponíveis, participantes e convites; verificar as formas singular e plural nos templates e testes.
- [x] 5.5 Padronizar cabeçalho, marca, navegação lateral/inferior e estado ativo nas rotas próprias e allauth; corrigir a área segura da navegação mobile e verificar que formulários longos mantêm campos e ações alcançáveis sem overflow horizontal.
- [x] 5.6 Revisar fixtures e dados de demonstração visíveis na UI, corrigindo erros ortográficos e removendo conteúdo impróprio ou identificadores que pareçam dados de produção; verificar que nenhum dado real entra em fixtures versionadas.
- [x] 5.7 Executar smoke test visual autenticado em mobile e desktop para login, cadastro, recuperação, e-mail, perfil, nova cobrança, prévia HTMX, detalhe, estados de pagamento e comprovante; registrar viewport, console, respostas HTTP, textos não traduzidos e capturas de evidência.
