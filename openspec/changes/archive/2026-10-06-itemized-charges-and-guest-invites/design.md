# Design

## Context

Veja `proposal.md` para a motivação e os `specs/` desta mudança para os contratos de comportamento. Hoje `Participation.user`, `Debt.debtor` e `Payment.payer` são relações obrigatórias com a conta Django; os formulários de criação aceitam somente contas existentes, e as views de pagamento/comprovante exigem login. Valores são tratados em centavos e a aplicação já usa serviços transacionais, templates Django, HTMX e armazenamento privado de comprovantes.

O HTML de referência é uma simulação estática: contém participantes e valores hard-coded, calcula com `parseFloat`, insere texto em HTML e usa um código curto ilustrativo. Sua sequência de telas inspira a jornada, mas esses detalhes não são adequados como cálculo ou autorização de produção.

## Goals / Non-Goals

**Goals:**

- Persistir uma decomposição verificável entre base comum, itens individuais e cotas finais.
- Representar participação convidada sem credencial global, mantendo dívidas e pagamentos no mesmo histórico financeiro das contas registradas.
- Permitir uma credencial compartilhada por cobrança, com escopo limitado às entradas abertas, expiração, revogação e trilha de autorização no servidor.
- Reutilizar as validações monetárias, transações, confirmação manual e armazenamento privado existentes.

**Non-Goals:**

- Verificar nome, identidade civil, username ou titularidade bancária do convidado.
- Criar dashboard, perfil Pix, recuperação de senha ou compensações para convidado.
- Criar, confirmar ou movimentar Pix automaticamente; fazer integração bancária, OCR ou ratear um pagamento entre dívidas.
- Transformar o protótipo HTML em página servida pelo Django.

## Decisions

1. **Convidado é uma participação de cobrança, não uma conta Pixu.** Acrescentar à `Participation` um nome de exibição e sua forma normalizada, mantendo `user` nulo exclusivamente para participações convidadas. Uma constraint garante exatamente uma identidade: conta ou convidado. Nomes convidados podem se repetir na mesma cobrança porque cada entrada recebe um código pessoal diferente; não competem com usernames, nomes ou e-mails de contas e podem reaparecer em outras cobranças. A alternativa de criar contas Django inativas com username sintético foi descartada porque mistura identidade local com acesso global e exige excluir essas linhas de login, busca e recuperação de conta.

2. **Entradas anônimas têm total explícito e limite separado.** A tela de criação permite habilitar entradas anônimas, exige o total de pessoas da conta e mantém o limite de entradas default 10 editável. O total inclui o criador quando participa, contas selecionadas e vagas anônimas; deve ser maior ou igual às participações iniciais. O link compartilhado aceita nome enquanto aberto; cada entrada ocupa uma vaga e recalcula somente identidades ainda não confirmadas sobre o denominador fixo. Cobranças antigas sem total preservam o comportamento dinâmico até serem encerradas.

3. **A conta usa uma base comum e itens atribuídos.** O servidor calcula `base = total − soma(itens)`, distribui a base em centavos por uma ordenação estável de vagas do total declarado e soma os itens de cada participante. Nenhum cálculo financeiro usa `float`. A prévia HTMX e o POST convencional chamam a mesma regra de domínio. A discriminação de itens fica persistida para que o convidado veja a origem de sua cota; vagas ainda vazias não criam dívida.

4. **Fechamento separa entrada de pagamento, salvo total fixo.** Em cobranças legadas sem total, adicionar ou sair enquanto as entradas estiverem abertas recalcula cotas e o criador fecha antes da confirmação. Em cobranças com total explícito, a entrada ainda pode ocorrer até o limite, mas a cota usa o denominador fixo e uma identidade pode confirmar e pagar imediatamente, mesmo que outro convite ainda esteja pendente; o criador continua podendo fechar ou revogar o link. Depois do primeiro pagamento, itens, responsáveis e cotas já confirmadas ficam congelados.

5. **Link compartilhado e código pessoal têm papéis distintos.** O link usa segredo aleatório de alta entropia armazenado como digest e só autoriza novas entradas enquanto aberto. Cada entrada gera um segredo pessoal armazenado como digest e mostrado uma vez; sua sessão fica fixa à participação. O código pessoal expira quando a dívida é quitada ou no TTL configurável (default sete dias, estendido para sete dias após o fechamento quando necessário), o que ocorrer primeiro. Revogar/renovar o link não troca códigos pessoais já emitidos; cancelar a cobrança invalida todos.

6. **O nome é autodeclarado, e isso é informado sem ambiguidade.** Quem tiver o link pode criar uma entrada com qualquer nome, inclusive repetido. O nome não prova quem está usando o link; a tela avisa isso e entrega um código pessoal para retornar. Aplicar limitação de tentativas e erros que não enumerem nomes ou cotas. Login opcional pode vincular uma entrada à conta, mas nunca é criado usuário automaticamente.

7. **Dívida convidada mantém recebedor registrado e não participa de compensação.** Tornar `Participation.user`, `Debt.debtor` e `Payment.payer` opcionais apenas para o caminho convidado; a identidade convidada continua acessível pela participação/dívida. Restrições no banco e validações de serviço mantêm uma conta ou convidado por participação e evitam devedor igual ao recebedor para dívidas de conta. Recebedor continua sendo conta cadastrada com chave Pix. Consultas de compensação e dashboard continuam somente para contas; dívida convidada segue saldo normal da cobrança e aparece ao criador/recebedor autenticados.

8. **Pagamento e comprovante usam a mesma fonte de verdade.** Adicionar um caminho de autorização convidada que valida sessão, participação, cobrança ativa e dívida no servidor; chamar a mesma regra monetária/transacional de pagamento sem confiar em IDs enviados pelo navegador. Pagamentos convidados ficam pendentes e usam `payer = NULL`; dívida e participação identificam a cota responsável. A view privada de comprovante aceita, além dos atores autenticados já permitidos, a sessão válida daquela participação e só para os pagamentos da própria dívida. Nunca servir URL pública de storage.

9. **As telas permanecem server-rendered e seguem Wave 0.** Antes de alterar templates, atualizar `docs/product-design.md` com jornada, composição do formulário de itens/entradas, estados de link expirado/fechado e conteúdo permitido da tela pública. Manter Django templates + HTMX + Tailwind compilado localmente; JavaScript limitado a adicionar/remover linhas e copiar link/chave, sem cálculos monetários autoritativos. Escapar nomes e descrições fornecidos por pessoas.

## Risks / Trade-offs

- [Nome autodeclarado não autentica uma pessoa →] avisar criador e convidado que quem possui o link pode criar uma entrada; restringir a sessão a uma participação, aplicar rate limit, não expor lista/cotas antes da entrada e permitir revogação imediata.
- [Um link compartilhado pode ser encaminhado fora do grupo →] token imprevisível, validade apenas enquanto as entradas estiverem abertas, revogação/renovação pelo criador, invalidação no cancelamento e nenhuma autorização pelo identificador público isolado.
- [Migrar chaves estrangeiras para permitir convidados pode afetar saldos e relatórios →] preservar linhas existentes, adicionar constraints condicionais, cobrir consultas de dashboard/compensação com testes de regressão e não backfill de dados financeiros.
- [Recibos convidados elevam o risco de exposição →] reutilizar validação de arquivo e storage privado existentes; testar acesso autorizado e negação cruzada por ID/tentativa de caminho.
- [Itens e cotas podem divergir após aceite se edição ficar parcial →] congelar juntos participantes, itens e cotas itemizadas no primeiro aceite externo e manter o bloqueio no serviço, não só nos controles da interface.

## Migration Plan

1. Adicionar campos opcionais de nome convidado e vínculo da credencial; tornar as FKs para conta/devedor/pagador opcionais com constraints condicionais. Manter intactos os valores de todas as participações, dívidas e pagamentos existentes.
2. Criar persistência de itens e regras de unicidade local para nomes convidados; criar migração reversível enquanto nenhuma cobrança convidada tiver sido criada.
3. Implantar serviços e rotas com a credencial habilitada somente após a migração; preservar login obrigatório em todas as rotas existentes.
4. Validar o fluxo de conta registrada e convidado, inclusive arquivo privado e transações, antes de habilitar em produção.

Rollback: desabilitar a criação e os links convidados, preservando dados registrados. Depois que houver participações/pagamentos convidados, não reverter a migração destrutivamente; publicar correção forward ou exportar e resolver essas cobranças antes de remover suporte.
