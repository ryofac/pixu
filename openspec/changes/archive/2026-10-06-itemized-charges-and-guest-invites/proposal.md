# Proposal

## Why

O fluxo atual só divide cobranças igualmente entre contas Pixu. O protótipo de itens e convites mostra como registrar consumos individuais e permitir que pessoas sem conta consultem e paguem somente sua cota, mantendo o Pix fora da aplicação e a confirmação manual pelo recebedor.

## What Changes

- Adicionar itens individuais a uma cobrança: cada item tem descrição, valor em centavos e participante responsável; o valor restante forma a base comum, dividida entre participantes com cotas que fecham exatamente o total.
- Permitir entradas anônimas identificadas por nome, sem exigir conta ou username global. A cobrança pode ser criada sem convidados; cada entrada cria sua própria identidade temporária e recalcula a cota comum enquanto as entradas estiverem abertas.
- Quando entradas anônimas forem habilitadas, exigir que o cobrador informe explicitamente o total de pessoas da conta (incluindo contas convidadas e vagas anônimas). Esse total fixa a base da cota e permite que uma pessoa anônima confirme e pague imediatamente, sem aguardar o fechamento do link; cobranças sem convidados anônimos mantêm o fluxo atual.
- Gerar um link compartilhado por cobrança e um código pessoal por entrada. O convidado informa apenas seu nome para entrar, recebe o link/código individual e fica restrito àquela cobrança e àquela cota, sem dashboard ou acesso às demais pessoas e cobranças.
- Exibir a discriminação da cota, a chave Pix do recebedor e permitir registrar pagamento parcial ou integral com comprovante privado opcional. O recebedor autenticado continua responsável por confirmar ou rejeitar manualmente.
- Atualizar a direção visual e os textos de `docs/product-design.md` antes de implementar as telas, usando o HTML como referência de fluxo, não como contrato literal de segurança ou cálculo.

## Capabilities

### New Capabilities

- `charges/guest-invites`: entrada dinâmica de convidados sem conta por link compartilhado, com identidade temporária e acesso limitado à cobrança e à própria cota.

### Modified Capabilities

- `charges`: incluir itens individuais na divisão, participantes convidados por nome e a discriminação persistida das cotas.
- `settlements/payments`: permitir que um convidado autorizado pelo link registre pagamento e comprovante na própria dívida, sem conceder ao convidado decisão de confirmação.

## Impact

- Afeta modelos, migrações, serviços, formulários, views e templates de `pixu/charges` e `pixu/settlements`, mais testes de domínio, autorização, concorrência e fluxo ponta a ponta.
- O modelo atual vincula `Participation`, `Debt` e `Payment` a contas Django e exige login para registrar pagamento. A implementação precisará representar a identidade convidada e autorizar operações pelo vínculo/token da participação sem transformar o convidado em conta global.
- Afeta a rota de compartilhamento, o detalhe/criação de cobranças, o formulário de pagamento convidado e o acesso protegido a comprovantes. Não adiciona integração bancária, confirmação automática, carteira ou pagamento de várias dívidas com uma transferência.
