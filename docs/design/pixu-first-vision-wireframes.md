# Pixu — wireframes e matriz de estados da primeira visão

**Status:** proposta de experiência para revisão da Wave 0  
**Escopo:** cadastro, perfil Pix, criação de cobrança, convites e aceite/recusa.

Este documento traduz os requisitos R01–R06 em jornadas e wireframes. O brief e os artefatos OpenSpec continuam sendo a fonte normativa das regras. Os pagamentos Pix e as compensações aparecem apenas como estados futuros descritos no brief; não fazem parte das telas implementadas nesta mudança.

Os wireframes priorizam o celular e usam navegação inferior. Eles não especificam nem demonstram funcionamento offline; a política de dados em cache e sincronização segue pendente.

## 1. Jornada do criador

1. Cria conta com e-mail, nome de usuário e senha.
2. Confirma o e-mail pelo link enviado pelo ambiente.
3. Entra e, se quiser, cadastra a chave Pix fornecida por ele no perfil.
4. Abre “Nova cobrança”, informa título e total, e seleciona contas já cadastradas.
5. Confere a prévia: sua própria participação mais a cota de cada convidado. O centavo residual segue a ordem estável por identificador persistente.
6. Confirma a cobrança. Os participantes convidados recebem convites pendentes e nenhuma dívida entra nos saldos enquanto faltar aceite.
7. Acompanha as respostas. Pode substituir uma participação recusada antes da primeira operação financeira e ajustar somente cotas ainda pendentes e a própria cota.

## 2. Jornada do participante

1. Entra na conta e abre “Convites”.
2. Confere o título, o valor total, os participantes e a própria cota.
3. Aceita ou recusa. Recusar não cria dívida. Aceitar cria uma dívida uma única vez.
4. Enquanto algum convite atual estiver pendente, a cobrança permanece aguardando aceite. Após o último aceite e a conferência do total das cotas, ela fica ativa.

## 3. Wireframes

### 3.1 Nova cobrança — mobile

```text
┌───────────────────────────────┐
│ PiXu                   Ryan ▾ │
├───────────────────────────────┤
│ Nova cobrança                 │
│                               │
│ Título                        │
│ [ Churrasco de sábado       ] │
│ Descrição (opcional)          │
│ [ Encontro na casa da Ana   ] │
│ Valor total                   │
│ [ R$ 150,00                 ] │
│ Convidar pessoas              │
│ [ ] Ana          [ ] Bruno   │
│                               │
│ Prévia do rateio              │
│ Ryan (criador)       R$ 50,00 │
│ Ana · pendente       R$ 50,00 │
│ Bruno · pendente     R$ 50,00 │
│ Total                R$ 150,00│
│                               │
│ [     Criar cobrança       ]  │
├───────────────────────────────┤
│ Cobranças  Convites  Perfil   │
└───────────────────────────────┘
```

### 3.2 Convite recebido — mobile

```text
+-------------------------------+
| Pixu                    Perfil |
| Convites                      |
|                               |
| Churrasco de sábado           |
| Criada por Ryan               |
| Total da cobrança  R$ 150,00  |
| Sua cota            R$ 50,00  |
|                               |
| Participantes                 |
| Ryan                 Criador  |
| Ana                  Pendente |
| Bruno                Pendente |
|                               |
| A cobrança só fica ativa      |
| quando todos aceitarem.       |
|                               |
| [ Aceitar participação ]      |
| [ Recusar convite ]           |
|                               |
+-------------------------------+
| Cobranças   Convites   Perfil |
+-------------------------------+
```

### 3.3 Perfil — mobile

```text
┌───────────────────────────────┐
│ PiXu                   Ryan ▾ │
├───────────────────────────────┤
│ Meu perfil                    │
│ Nome de exibição              │
│ [ Ana                       ] │
│ Chave Pix                     │
│ [ telefone, e-mail, ...    ] │
│                               │
│ A chave é informada por você. │
│ O Pixu não verifica a chave   │
│ junto ao banco.               │
│                               │
│ [    Salvar alterações     ]  │
├───────────────────────────────┤
│ Cobranças  Convites  Perfil   │
└───────────────────────────────┘
```

### 3.4 Telas maiores

O conteúdo permanece centralizado em uma coluna confortável. A navegação inferior pode ter largura contida e alinhada ao conteúdo; não se converte em sidebar.

## 4. Matriz de estados

| Objeto | Estado | O que a pessoa vê | Ação permitida nesta mudança |
| --- | --- | --- | --- |
| Conta | Não autenticada | Entrar, criar conta ou recuperar acesso | Cadastrar, entrar ou solicitar recuperação |
| Conta | Confirmação pendente | Aviso para confirmar o e-mail | Abrir o link enviado pelo ambiente |
| Participação | Pendente | Convite, cota e lista de participantes | Destinatário aceita ou recusa |
| Participação | Aceita | Aceite registrado; cobrança pode continuar aguardando outras pessoas | Sem alterar a cota aceita |
| Participação | Recusada | Recusa registrada | Criador pode substituir antes de operação financeira |
| Cobrança | Aguardando aceite | Respostas pendentes e cotas | Aceitar/recusar; criador ajusta cotas permitidas |
| Cobrança | Ativa | Todas as participações atuais foram aceitas e as cotas fecham o total | Pagamentos pertencem a uma mudança posterior |
| Cota | Editável | Cotas próprias e de participações pendentes | Criador pode ajustar antes de aceite/operação |
| Cota | Imutável | Cota aceita ou cobrança bloqueada por operação financeira | Não pode alterar nesta versão |

## 5. Estados financeiros planejados para telas futuras

Estes estados são registrados para consistência do produto, sem habilitar operações financeiras na mudança atual:

| Objeto | Estados futuros do brief | Regra de apresentação |
| --- | --- | --- |
| Pagamento Pix | Pendente, confirmado ou rejeitado | Pendente reserva disponibilidade, mas não reduz o saldo aberto; confirmação é manual pelo recebedor |
| Dívida | Aberta ou quitada | Mostrar valor original, Pix confirmado, compensado, Pix pendente e saldo aberto |
| Compensação | Sugerida e aplicada | Sugestão não reserva; aplicação exige ação do pagador e reduz duas dívidas recíprocas |

## 6. Estados globais das telas

- **Vazio:** explicar o próximo passo e oferecer ação principal, como “Criar cobrança” ou “Nenhum convite recebido”.
- **Carregando:** manter o contexto e sinalizar a região atualizada por HTMX com `aria-live="polite"`.
- **Erro de validação:** preservar os dados digitados, destacar o campo e explicar como corrigir.
- **Sem permissão ou recurso inexistente:** exibir resposta segura sem revelar dados da cobrança.
- **Sucesso:** confirmar a ação e atualizar o estado sem duplicar submissões.

## 7. Relação com os requisitos

- Cadastro, sessão e recuperação: R01.
- Convites recebidos, aceite/recusa e dívida somente após aceite: R02.
- Chave Pix fornecida pelo próprio usuário: R03.
- Criação, recebedor único e participantes existentes: R04.
- Prévia e rateio exato em centavos: R05.
- Ajuste somente das cotas permitidas: R06.
- Proteção e formulários: R16.
- Padrões de templates, HTMX e Tailwind local: R17.
