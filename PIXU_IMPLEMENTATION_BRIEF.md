# Pixu — especificação de implementação para Codex + OpenSpec

**Estado:** especificação da primeira versão operacional · **Data:** 24/09/2026 · **Idioma do produto:** pt-BR  
**Público deste documento:** pessoa desenvolvedora e agente de codificação.  
**Fonte de contexto:** brainstorming “Planejamento Pixu”, decisões de produto e [exploração visual inicial](./pixu_projeto_demo.html).

> Este arquivo é o *brief* do produto e a referência para criar mudanças no OpenSpec. Ele não é, por si só, um `spec.md` validado pelo OpenSpec nem substitui os artefatos gerados no repositório. As mudanças propostas abaixo devem ser convertidas em `proposal.md`, especificações, `design.md` e `tasks.md` conforme o esquema instalado no projeto.

## 1. Objetivo

Construir uma aplicação web utilizável para dividir despesas entre amigos e acompanhar obrigações entre pessoas. Uma pessoa cria sua conta, cadastra sua chave Pix, cria uma cobrança e convida outros usuários cadastrados. Cada destinatário aceita sua participação. O pagamento é transferido diretamente pelo aplicativo bancário do pagador; no Pixu, ele informa o pagamento e o recebedor confirma o recebimento. Quando existem dívidas recíprocas aceitas, o pagador pode compensá-las, com registro distinto da transferência Pix.

**Exemplo de uso para aceitação:** Ryan pagou R$ 150,00 pelo churrasco de Ryan, Ana e Bruno. Cada um tem uma cota de R$ 50,00; Ana e Bruno devem R$ 50,00 a Ryan. Antes do churrasco, Ryan já devia R$ 30,00 a Ana. Ana escolhe compensar R$ 30,00 e registra Pix de R$ 20,00. Após Ryan confirmar o recebimento, a dívida de Ana é quitada; Bruno ainda deve R$ 50,00.

**Resultado esperado:** usuários reais conseguem criar conta, cadastrar chave Pix, criar e aceitar cobranças, registrar pagamentos parciais, confirmar recebimentos e compensar dívidas, com saldos persistidos e corretos. Os quatro personagens do exemplo são dados de teste opcionais; nenhum fluxo de produto depende deles. O HTML anterior é somente uma exploração visual inicial.

### 1.1 Decisões fixas

| Tema | Decisão da primeira versão |
| --- | --- |
| Backend e dados | Django, templates renderizados no servidor e PostgreSQL para o fluxo financeiro. |
| Frontend obrigatório | **HTMX para interações dinâmicas e Tailwind CSS instalado, configurado e compilado dentro do projeto.** O Tailwind não pode depender de CDN em desenvolvimento nem na entrega. |
| Processo de design | Definir fluxos, estados, wireframes e componentes antes de implementar visualmente as telas em Django. Registrar as decisões em `docs/product-design.md`. |
| Identidade | Cadastro, login, recuperação de senha e edição de perfil/chave Pix reais via Django auth e funcionalidades associadas. Contas de exemplo existem apenas em fixtures locais e testes. |
| Cobrança | O criador é o único recebedor; a divisão igualitária inclui sua própria cota; pode editar os valores antes de operações financeiras. |
| Participação | O criador convida usuários cadastrados por identificador; o destinatário vê o convite na aplicação e aceita antes de assumir a dívida. |
| Pagamento | Transferência Pix é feita fora do Pixu. O pagador registra valor e pode anexar comprovante privado; o recebedor confirma ou rejeita. |
| Confirmação | A primeira versão exige confirmação explícita do recebedor. Confirmação automática só poderá ser adicionada em uma mudança posterior baseada em verificação real. |
| Crédito | Não existe carteira. “Crédito disponível” é a possibilidade de compensar uma dívida inversa ainda aberta, aceita e não reservada. |
| Compensação | Sugerida entre as mesmas duas pessoas; aplicada somente após ação do pagador; reduz ambas as dívidas pelo mesmo valor numa transação. |
| Escopo | Um pagamento registrado se refere a uma dívida. Um único Pix para várias cobranças fica para evolução posterior. |

### 1.2 Limites da primeira versão

O Pixu registra obrigações e pagamentos informados pelas pessoas, sem movimentar dinheiro. Integração bancária, geração de cobrança Pix/QR dinâmico, confirmação automática, OCR/IA de comprovantes, cobrança direta sem aceite, grupos, múltiplos recebedores, pagamento excedente, reembolso automático, compensações triangulares, rateio por itens, convite por e-mail ou link externo e distribuição de um único Pix por várias dívidas são evoluções separadas. A ausência dessas funções não impede o uso dos fluxos descritos neste documento.

## 2. Linguagem do domínio

- **Cobrança (`Charge`):** descrição da despesa coletiva, valor total e único recebedor. Não equivale ao saldo de uma pessoa.
- **Participação (`Participation`):** pessoa selecionada, sua cota e aceite. A participação do criador é automaticamente aceita, sem dívida contra si mesmo.
- **Dívida (`Debt`):** obrigação de um usuário pagar a outro por uma participação aceita. Existe uma dívida separada para cada participante pagador.
- **Pagamento (`Payment`):** registro de um Pix informado pelo pagador, vinculado a uma dívida. Só reduz saldo após confirmação explícita do recebedor; o comprovante anexado ajuda na conferência, mas não valida o Pix sozinho.
- **Compensação (`Compensation`):** evento que reduz, em igual quantia, duas dívidas abertas em sentidos opostos. Não é Pix e não transfere dinheiro.
- **Saldo aberto:** valor original menos pagamentos confirmados e compensações aplicadas.
- **Valor disponível para liquidar:** saldo aberto menos pagamentos pendentes reservados. Evita gastar duas vezes a mesma parte da dívida.
- **Potencial de compensação:** para cada par de pessoas, o menor valor entre o total que uma deve à outra e o total na direção contrária, considerando apenas parcelas disponíveis. É uma estimativa de oportunidade, não saldo financeiro em conta.

## 3. Regras normativas e critérios de aceite

Os identificadores `Rxx` são estáveis para rastrear requisitos, testes e tarefas. “DEVE” indica comportamento obrigatório na primeira versão operacional.

### 3.1 Identidade e participação

**R01 — Contas e acesso.** Uma pessoa DEVE poder criar conta, entrar, sair, recuperar acesso por e-mail configurado e editar sua chave Pix. O sistema DEVE exigir login para cobranças, saldos e comprovantes. Usuários só DEVEM acessar cobranças de que são criadores ou participantes. Ações de confirmar/rejeitar Pix são exclusivas do recebedor; aceitar/recusar convite, registrar Pix e aceitar compensação são exclusivas do próprio participante. A autorização DEVE ser validada no servidor em toda requisição HTMX ou convencional.

**R02 — Convite interno e aceite.** O criador escolhe contas já registradas; cada destinatário recebe uma participação `PENDING` visível em “Convites”. Ele pode aceitar ou recusar. Aceitar gera sua dívida exatamente uma vez; repetir aceite não duplica nada. Até que todos os convidados ativos aceitem, a cobrança permanece `AWAITING_ACCEPTANCE`, suas dívidas não entram nos totais e ninguém pode pagar ou compensar. Em caso de recusa, o criador pode substituir o destinatário e ajustar cotas ainda não aceitas antes da primeira operação financeira. A cobrança só fica `ACTIVE` depois de todos os aceites e a soma das cotas continuar igual ao total.

**R03 — Chave Pix.** Cada usuário pode cadastrar e alterar sua chave Pix no perfil. O pagador vê a chave atual do recebedor da dívida e um botão de copiar. O sistema informa que a chave foi fornecida pelo usuário e NÃO afirma tê-la verificado junto a uma instituição financeira.

### 3.2 Cobrança e divisão

**R04 — Criação.** Um usuário autenticado DEVE poder criar cobrança com título, descrição opcional, valor positivo em centavos e participantes existentes. O criador é incluído automaticamente e é o único recebedor. O mesmo usuário não pode ser incluído duas vezes.

**R05 — Divisão igualitária.** A divisão padrão DEVE incluir o criador, preservar o total exato e produzir cotas inteiras em centavos. Para centavos residuais, usar uma ordem determinística estável entre participantes e mostrar as cotas antes de confirmar. A cota do criador NÃO gera dívida contra ele mesmo.

**R06 — Edição manual.** Antes de qualquer pagamento registrado ou compensação executada, o criador pode editar cotas de participações ainda pendentes e sua própria cota; a soma das cotas DEVE ser exatamente o total e nenhuma cota pode ser negativa. Depois do aceite, a cota daquele participante fica imutável, ainda que as cotas pendentes possam ser ajustadas. O formulário deve impedir combinações que não fechem o total. Para mudar uma cota já aceita será necessário criar outra cobrança nesta versão.

**R07 — Bloqueio.** Desde o primeiro pagamento registrado, inclusive pendente, ou da primeira compensação aplicada, a cobrança DEVE bloquear alteração de valor total, participantes e cotas. Esse bloqueio é definitivo nesta versão, mesmo que o pagamento seja rejeitado, para manter o histórico coerente.

### 3.3 Pagamentos

**R08 — Registro.** Somente o devedor de uma cobrança `ACTIVE` DEVE poder informar um pagamento positivo, de até seu valor disponível para liquidar, vinculado a uma única dívida. Ele pode adicionar referência textual e comprovante opcional (imagem ou PDF), acessível somente ao pagador e recebedor. Ao registrar, o pagamento fica `PENDING`; o saldo aberto não muda, mas a quantia fica reservada. A interface exibe separadamente saldo aberto e valor aguardando confirmação.

**R09 — Confirmação/rejeição.** Somente o recebedor DEVE confirmar ou rejeitar `PENDING`. Confirmar muda para `CONFIRMED`, lança a liquidação uma única vez e reduz o saldo. Rejeitar muda para `REJECTED` e libera a reserva sem reduzir o saldo. Repetir ação ou processar estado já final não pode aplicar a mesma liquidação outra vez. Sem correção de valor: rejeitar e registrar novo pagamento.

**R10 — Origem da confirmação.** A primeira versão DEVE permitir somente a confirmação manual pelo recebedor e registrar quem confirmou e quando. O sistema NÃO DEVE confirmar automaticamente a partir do envio de comprovante. Uma futura validação automática exigirá integração capaz de verificar o recebimento e uma mudança OpenSpec própria; a interface atual não promete nem simula essa validação.

### 3.4 Compensação

**R11 — Elegibilidade.** Quando Ana deve a Ryan e Ryan deve a Ana, ambas as cobranças `ACTIVE`, dívidas aceitas e com valor disponível positivo, o Pixu DEVE mostrar uma sugestão para Ana na tela de sua dívida. Uma dívida ainda pendente de aceite, quitada ou com todo o saldo reservado para Pix NÃO é elegível. Crédito de dívida quitada por pagamento confirmado não pode ser usado.

**R12 — Aceite do pagador.** Ana escolhe a dívida inversa e aceita compensar um valor positivo até `min(disponível de Ana→Ryan, disponível de Ryan→Ana)`. A interface mostra quanto de cada dívida será reduzido e o Pix restante. O sistema DEVE conferir novamente disponibilidade e titularidade ao executar a ação; exibir sugestão não reserva valores.

**R13 — Atomicidade e rastreabilidade.** O evento de compensação DEVE apontar para as duas dívidas distintas e opostas, registrar quem o iniciou, valor e momento. A operação reduz as duas dívidas pelo mesmo valor, uma só vez, ou falha sem reduzir nenhuma. Ambas ficam imutáveis quanto ao histórico anterior; a compensação não é representada como Pix nem como crédito avulso.

### 3.5 Cálculo, exibição e segurança

**R14 — Invariantes.** Valores monetários em centavos inteiros (ou `Decimal` com duas casas na fronteira; proibido `float`). Para cada dívida: `0 ≤ saldo_aberto ≤ valor_original`; `saldo_aberto = valor_original − soma(Pix CONFIRMED) − soma(compensações)`; `0 ≤ reservas_Pix_PENDENTEs ≤ saldo_aberto`. Persistência de evento e atualização de qualquer saldo materializado DEVEM ocorrer juntas. Operações simultâneas não podem produzir saldo negativo ou dupla liquidação.

**R15 — Apresentação.** Uma dívida exibe valor original, Pix confirmado, compensado, Pix pendente e saldo aberto. O dashboard mostra “A receber”, “A pagar” e “Potencial de compensação”, além de convites pendentes e listas curtas de cobranças criadas e participadas. Os totais a receber/pagar são brutos e calculados só a partir de dívidas de cobranças `ACTIVE`; o potencial não é somado a eles.

**R16 — Formulários, arquivos e proteção de dados.** Validar valores e permissões no backend. Usar CSRF, escapar textos apresentados e limitar título, descrição e referência. Para anexos: impor limite configurado de tamanho e tipos aceitos (PDF, JPEG, PNG), validar conteúdo recebido, salvar em armazenamento privado e servir somente após autorização do pagador ou recebedor. Não expor comprovantes por URL pública; registrar apenas metadados e referência ao arquivo no banco. Não incluir chaves Pix ou comprovantes reais em fixtures versionadas. Mostrar erros acionáveis em formulários.

**R17 — Frontend e design.** A interface DEVE usar **Django templates + HTMX + Tailwind CSS configurado no repositório**. O build local do Tailwind DEVE gerar CSS para desenvolvimento e para a entrega, incluindo as classes usadas em páginas e fragmentos HTMX. NÃO usar Tailwind por CDN como solução do projeto. As decisões de navegação, estados, linguagem visual e componentes DEVEM constar em `docs/product-design.md` antes da implementação das telas. HTMX não pode substituir validação ou autorização no servidor.

## 4. Cenários Given / When / Then de referência

1. **Divisão:** dado Ryan, Ana e Bruno e cobrança de R$ 150,00, quando Ryan confirma a divisão igual, então cada cota é R$ 50,00; depois dos aceites de Ana e Bruno a cobrança fica `ACTIVE` e existem apenas Ana→Ryan R$ 50,00 e Bruno→Ryan R$ 50,00.
2. **Centavos:** dado R$ 100,00 dividido igualmente entre três pessoas, quando o rateio é calculado, então as cotas somam R$ 100,00 sem fração de centavo e a mesma entrada produz sempre o mesmo resultado.
3. **Cadastro e convite:** dada uma conta criada por Ana, quando Ryan a convida para uma cobrança, então Ana vê um convite pendente; ao aceitar, a dívida é criada uma vez, e ao repetir o aceite não há duplicidade.
4. **Participação pendente:** dada uma cobrança aguardando a resposta de Ana, quando qualquer participante consulta suas obrigações, então nenhuma dívida dessa cobrança integra os totais nem qualquer sugestão de compensação; pagamentos ficam indisponíveis até todos os aceites.
5. **Recusa:** dado um convite recusado por Ana antes de qualquer operação, quando Ryan ajusta a cobrança e convida outro usuário mantendo o total exato, então a cobrança só fica ativa após todos os convites válidos serem aceitos.
6. **Crédito recíproco:** dadas dívidas aceitas e ativas Ana→Ryan R$ 50,00 e Ryan→Ana R$ 30,00, quando Ana abre a primeira, então o máximo sugerido é R$ 30,00.
7. **Aplicação:** dadas essas dívidas e nenhum Pix pendente, quando Ana aceita R$ 30,00, então os saldos ficam R$ 20,00 e R$ 0,00, com um evento de compensação de R$ 30,00.
8. **Pix pendente:** dado Ana→Ryan R$ 20,00, quando Ana registra Pix de R$ 20,00, então o saldo aberto continua R$ 20,00 e o disponível fica R$ 0,00. Segundo pagamento ou compensação sobre esses R$ 20,00 é rejeitado.
9. **Comprovante privado:** dado um pagamento com PDF anexado por Ana, quando Bruno tenta acessar o arquivo, então recebe acesso negado; Ana e Ryan conseguem visualizá-lo autenticados.
10. **Confirmação:** dado o Pix pendente anterior, quando Ryan confirma manualmente, então o saldo de Ana fica R$ 0,00; o detalhe discrimina R$ 30,00 compensados e R$ 20,00 confirmados via Pix na obrigação original.
11. **Rejeição:** dado Pix pendente de R$ 20,00, quando Ryan rejeita, então o saldo aberto segue R$ 20,00 e volta a estar disponível para novo registro.
12. **Duplicidade:** dado um pagamento já confirmado ou uma compensação já aplicada, quando a mesma ação é repetida, então não há novo evento de liquidação nem saldo negativo; a aplicação responde de forma segura.
13. **Corrida:** dadas duas tentativas concorrentes de pagar/compensar uma mesma parcela, quando processadas, então no máximo o valor disponível é liquidado; uma tentativa recebe erro de conflito ou valor indisponível.
14. **Acesso:** dado Bruno autenticado, quando tenta confirmar Pix de Ana para Ryan, então recebe resposta de acesso negado e o estado não muda.
15. **Trava:** dado pagamento registrado em cobrança, mesmo que depois rejeitado, quando o criador tenta mudar participantes ou cotas, então o servidor recusa a edição.
16. **Recuperação de acesso:** dado um usuário cadastrado com e-mail válido, quando solicita redefinição de senha, então recebe o fluxo configurado, altera a senha e consegue entrar; o link de redefinição não revela a senha nem dá acesso a terceiros.
17. **Uso contínuo:** dadas cobranças, Pix confirmado e comprovante autorizado, quando a aplicação é reiniciada, então contas, histórico, saldos e acesso ao arquivo permanecem corretos; o arquivo não fica disponível por URL pública.

## 5. Modelo de dados sugerido

É um desenho lógico, não uma exigência de nomes exatos de classes. O `design.md` de cada mudança deve registrar constraints, índices e migrações antes da implementação.

| Entidade | Campos essenciais | Restrições |
| --- | --- | --- |
| `User`/`PixProfile` | usuário Django, e-mail para recuperação, chave Pix cadastrada | Exposição da chave apenas a quem participa de uma obrigação de pagamento; uma chave principal por usuário nesta versão. |
| `Charge` | criador/recebedor, título, descrição, total_centavos, estado, criado_em, bloqueado_em | Total > 0; recebedor = criador; `AWAITING_ACCEPTANCE` até todos os aceites, depois `ACTIVE`; bloquear edição após a primeira operação. |
| `Participation` | cobrança, usuário, cota_centavos, estado (`PENDING`, `ACCEPTED`, `DECLINED`), aceito_em | Unicidade `(charge, user)` para participações ativas; soma das cotas válidas = total ao ativar a cobrança. Convite recusado não gera dívida. |
| `Debt` | participação, devedor, recebedor, valor_original_centavos | Uma por participação aceita que não seja do criador; devedor ≠ recebedor; identidade estável. |
| `Payment` | dívida, pagador, recebedor, valor_centavos, estado, referência_texto, comprovante_privado, confirmado_por, criado_em, confirmado_em | Valor > 0; `PENDING` reserva; `CONFIRMED` liquida; `REJECTED` libera. Um pagamento registrado se refere a uma dívida. |
| `Compensation` | dívida_alvo, dívida_inversa, valor_centavos, iniciado_por, criado_em | Dívidas opostas e distintas; valor > 0; dois saldos reduzidos atomicamente. |

**Fonte de verdade:** a soma das liquidações confirmadas e das compensações, subtraída do valor original, calcula o saldo. Reservas correspondem apenas a pagamentos `PENDING`. Se decidir armazenar `remaining_amount`, justificar o motivo e atualizar em transação com os eventos. O sistema não precisa de uma entidade independente `Credit` nesta versão.

**Transação de compensação:** autenticar pagador; carregar duas dívidas com bloqueio de linha em ordem estável de IDs no PostgreSQL; validar reciprocidade, aceites e disponibilidade já considerando reservas; inserir evento; atualizar qualquer saldo materializado; confirmar transação. Confirmação de Pix usa regra equivalente para sua dívida. Ensaiar concorrência com teste transacional no PostgreSQL, pois testes com SQLite podem não exercitar o mesmo bloqueio.

## 6. Interface e fluxos

| Tela | Conteúdo e ações mínimas |
| --- | --- |
| Cadastro e login | Criar conta, entrar, sair, recuperar acesso e editar perfil/chave Pix. |
| Convites | Listar cobranças recebidas; visualizar valor e participantes; aceitar ou recusar. |
| Dashboard | A receber, a pagar, potencial de compensação; cobranças criadas e participadas. |
| Criar cobrança | Título, total, convidados; prévia das cotas; edição manual conforme os aceites e o bloqueio por operação. |
| Detalhe da cobrança | Participantes, cotas, estado de aceite, dívidas, pagamentos e valores compensados; aceitar se destinatário. |
| Minhas dívidas | Obrigações aceitas, saldo, Pix pendente e indicação de compensação. |
| Registrar pagamento | Chave Pix do recebedor, copiar, valor, referência opcional, anexo privado opcional e registro de envio informado. |
| Créditos/compensações | Dívidas inversas elegíveis, valor máximo, revisão antes de aplicar e histórico das compensações executadas. |

### 6.1 Decisões obrigatórias de frontend

- **Renderização:** Django templates são a base das páginas; fragmentos reutilizáveis são retornados para interações HTMX. A primeira versão não exige SPA ou framework JavaScript de componentes.
- **Interatividade:** HTMX atualiza cards, saldos e formulários após ações. Todo endpoint HTMX aplica CSRF, autorização e validação de domínio, como qualquer requisição convencional. Usar JavaScript pequeno apenas quando necessário para recursos do navegador, como copiar a chave Pix.
- **Estilos:** Tailwind CSS é dependência instalada e travada no projeto, com entrada de CSS e processo de compilação documentados. O build inclui templates e fragmentos HTMX, funciona localmente e produz os arquivos servidos por Django no ambiente de execução. Não carregar Tailwind via CDN.
- **Design visual:** `docs/product-design.md` registra tokens de cor e tipografia, espaçamento, estados e componentes recorrentes. A paleta e a composição devem ser decididas na wave de design; o HTML anterior é referência de conteúdo, não contrato visual definitivo.
- **Acessibilidade e responsividade:** telas prioritariamente legíveis em mobile; botões com rótulos claros; estados de pagamento descritos por texto e não somente por cor; erros e mudanças importantes de estado perceptíveis após atualizações HTMX.

### 6.2 Entregáveis da wave de design

Antes de implementar as telas, produzir: (1) jornada de criador e devedor, incluindo cadastro e convites; (2) wireframes das telas listadas acima; (3) matriz de estados para aceite, Pix pendente/confirmado/rejeitado e compensação; (4) fluxo navegável de design com valores de exemplo; (5) `docs/product-design.md` com componentes, textos de interface e regras de uso do HTMX e Tailwind. Validar se uma pessoa entende “Pix pendente”, “saldo aberto” e “compensado” sem explicação verbal. O fluxo de design é um instrumento de revisão; a entrega do produto são as telas funcionais conectadas ao backend.

## 7. Arquitetura de referência

```text
pixu/
├── config/                 # settings e URLs
├── accounts/               # autenticação e perfil Pix
├── charges/                # cobrança, participação, dívida e divisão
├── settlements/            # pagamentos, reservas e compensações
├── private_uploads/         # interface de armazenamento protegido de comprovantes
├── dashboard/              # consultas agregadas, sem escrita monetária
├── templates/              # páginas e fragmentos HTMX
├── assets/                 # entrada e build local do Tailwind CSS
├── docs/product-design.md  # decisões de experiência e interface
└── tests/                  # cenários de domínio, autorização e integração
```

Serviços de aplicação sugeridos: `create_charge`, `calculate_shares`, `accept_participation`, `record_payment`, `confirm_payment`, `reject_payment`, `suggest_compensations`, `apply_compensation`. Views chamam esses serviços e renderizam resposta; não executam regras de saldo por conta própria. Consultas do dashboard reutilizam a definição única de saldo.

**Execução e operação:** Python e dependências declaradas e travadas no repositório, PostgreSQL configurado por ambiente, segredos fora do código, serviço de e-mail para recuperação de senha e armazenamento privado de comprovantes. Tailwind CSS e ferramenta de build instalados como dependências do projeto, com scripts para observar alterações em desenvolvimento e compilar CSS na entrega. Documentar migração do banco, publicação dos arquivos estáticos, inicialização da aplicação, backups, restauração e política de retenção de anexos. Configurar HTTPS, hosts permitidos, `DEBUG=False`, cookies adequados ao ambiente e verificações de implantação do Django. Dados de exemplo são fixtures idempotentes exclusivas de desenvolvimento/teste e nunca são pré-requisito para cadastrar usuários ou criar cobranças. Escolher versões suportadas de Django, Python, PostgreSQL, HTMX e Tailwind CSS no repositório e registrar no README. Consultar o [checklist oficial de implantação do Django](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/) compatível com a versão escolhida.

## 8. Sequência de mudanças no OpenSpec

Uma mudança por vez. O agente deve criar os artefatos, revisar suas contradições, implementar somente o lote aprovado pela especificação e validar seus cenários antes de iniciar o seguinte. O OpenSpec usa por padrão `openspec/changes/<nome>/` com `proposal.md`, especificações de capacidades, `design.md` e `tasks.md`; a forma exata depende do esquema configurado. Documentação oficial: [configuração](https://openspec.dev/docs/setup) e [skills](https://openspec.dev/docs/skills).

**Wave 0 — design antes das mudanças de código:** produzir e revisar os entregáveis da seção 6.2. A escolha de HTMX + Tailwind CSS já está fixada; esta wave decide a experiência e a apresentação visual. O `docs/product-design.md` complementa o `design.md` técnico de cada mudança OpenSpec.

| Ordem | Nome sugerido | Entrega observável | Requisitos |
| --- | --- | --- | --- |
| 1 | `bootstrap-pixu-and-charges` | Cadastro, login, recuperação de senha, criação e rateio de cobrança, convites internos, aceites/recusas, ativação, dívidas e testes; Tailwind configurado nos templates iniciais. | R01–R02, R04–R06, R16–R17 |
| 2 | `record-and-confirm-pix` | Perfil e chave Pix, Pix parcial, anexo privado opcional, reserva, confirmação manual, rejeição, status e bloqueio de edição. | R03, R07–R10, R14, R16 |
| 3 | `offset-reciprocal-debts` | Sugestão, aceite e compensação transacional de dívidas recíprocas, sem carteira virtual. | R11–R14 |
| 4 | `complete-product-experience` | Dashboard, convites, histórico e telas HTMX responsivas; fluxo integral percorrido com contas recém-criadas e sem intervenção no banco. | R01–R03, R15–R17 |

### 8.1 Critério de conclusão de cada mudança

- Proposta, requisitos em cenários e desenho não se contradizem; tarefas pequenas podem ser verificadas individualmente.
- Migrações e constraints correspondem ao desenho; autorização é testada inclusive em ações HTMX.
- Testes de domínio relevantes passam no banco escolhido; a mudança não quebra os cenários dos lotes anteriores.
- README contém os comandos reais de instalar, migrar, semear, testar e iniciar; não escrever comandos que não foram executados.
- O build local do Tailwind compila o CSS usado nas páginas e fragmentos HTMX, sem CDN; as telas seguem `docs/product-design.md`.
- Cadastro, convite, recuperação de acesso, upload protegido e operações financeiras são exercitados com usuários criados pela própria aplicação. Configuração de e-mail, backup e armazenamento privado está documentada e testada no ambiente de entrega.
- Ao descobrir nova regra, revisar artefatos OpenSpec antes de alterar a implementação; concluir um lote antes de iniciar outro.

### 8.2 Prompt inicial para o Codex no repositório

Copiar este arquivo para a raiz do futuro repositório Pixu como `PIXU_IMPLEMENTATION_BRIEF.md`. Primeiro executar a wave 0:

> Leia `PIXU_IMPLEMENTATION_BRIEF.md` integralmente. Defina a experiência da primeira versão operacional do Pixu antes de codificar: jornadas de cadastro, convite, cobrança, Pix e compensação; wireframes das telas; matriz de estados; e fluxo navegável de revisão. Registre escolhas visuais e componentes em `docs/product-design.md`. A implementação final usará Django templates + HTMX + Tailwind CSS instalado e compilado no projeto, sem CDN. Entregue os artefatos de design para revisão antes de implementar as telas.

Depois de revisar o design, iniciar a primeira mudança OpenSpec:

> Leia `PIXU_IMPLEMENTATION_BRIEF.md` e `docs/product-design.md`. Inspecione o repositório e os arquivos `AGENTS.md` aplicáveis. Inicialize ou utilize o OpenSpec já existente neste repositório; siga o esquema e as instruções que ele gerar. Crie **somente** os artefatos da mudança `bootstrap-pixu-and-charges` nesta rodada: proposta, especificações com cenários para R01–R02, R04–R06 e R16–R17, design técnico e tarefas pequenas com critérios verificáveis. Cubra cadastro e recuperação de senha reais, convites internos aceitos/recusados e ativação de cobranças. Inclua Tailwind CSS compilado localmente e HTMX nos templates aplicáveis. Não comece a codificar antes de revisar contradições entre os artefatos; não invente integração bancária nem carteira de créditos.

Depois de revisar os artefatos da primeira mudança, pedir ao Codex para implementar a mudança seguindo suas tarefas. Repetir o ciclo nas demais mudanças. Na instalação atual do OpenSpec, `openspec init` configura o projeto e as skills de planejamento e aplicação cuidam das etapas seguintes; a grafia disponível no Codex depende dos arquivos gerados pelo init. Consulte [instalação](https://openspec.dev/docs/installation) e [fluxos de trabalho](https://openspec.dev/docs/skills).

## 9. Jornada ponta a ponta para aceitação da primeira versão

1. Criar contas de Ryan, Ana e Bruno pela interface; entrar e configurar a chave Pix do recebedor.
2. Ana cria uma cobrança anterior em que Ryan aceita dever R$ 30,00 a ela.
3. Ryan cria “Churrasco de sábado” por R$ 150,00 e convida Ana e Bruno; a aplicação mostra três cotas de R$ 50,00 e aguarda aceites.
4. Ana e Bruno aceitam pelos seus próprios acessos; a cobrança fica ativa. Como Ana, abrir a dívida de R$ 50,00, ver a sugestão de R$ 30,00 e aceitar. Conferir Ana→Ryan R$ 20,00 e Ryan→Ana R$ 0,00.
5. Ana copia a chave cadastrada por Ryan, realiza o Pix fora do Pixu e registra R$ 20,00, com anexo opcional; a aplicação mostra pagamento pendente sem queda prematura do saldo aberto.
6. Ryan confere o recebimento no próprio banco e confirma no Pixu; o detalhe discrimina R$ 30,00 compensados e R$ 20,00 confirmados via Pix.
7. Bruno continua devendo R$ 50,00. Repetir uma confirmação ou compensação não altera saldos pela segunda vez.

**Critério global de pronto:** concluir essa jornada com contas criadas pela interface, e-mail de recuperação operacional, comprovantes protegidos, estados coerentes em todas as telas e saldos corretos sem ajustes manuais no banco. Confirmar um Pix no Pixu sempre depende da ação do recebedor, que deve ter conferido o dinheiro fora da aplicação.

## 10. Decisões que continuam abertas, sem bloquear o primeiro lote

1. **Chave Pix:** usar campo textual informado pelo usuário, sem inferir validade bancária; verificação e múltiplas chaves ficam para mudança futura.
2. **Comprovantes:** definir a duração de retenção e o procedimento de exclusão durante a mudança `record-and-confirm-pix`, antes de habilitar upload no ambiente de uso. Controle de acesso, limite de tamanho e tipos aceitos fazem parte desta versão.
3. **Pagamento entre várias cobranças:** modelar alocações de uma transferência para várias dívidas somente numa mudança posterior, junto com idempotência e reconciliação de valores.

As demais capacidades listadas fora da primeira versão exigem mudanças OpenSpec próprias; não são pressupostos dos fluxos operacionais aqui definidos.
