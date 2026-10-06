# Tasks

## 1. Reproduzir o convite ausente

- [x] 1.1 Adicionar um cenário E2E que cria uma cobrança pela interface com a mesma pessoa marcada em “Quem recebe” e “Convidar pessoas cadastradas”, entra na conta dela e verifica o convite pendente, título, criador, recebedor e cota; verificar com `just e2e tests/e2e/test_charges.py`.
- [x] 1.2 Adicionar um teste de view que submete a criação com a recebedora também convidada e consulta a lista de convites como essa conta; verificar a participação `PENDING` e os termos exibidos com `just pytest pixu/charges/tests.py`.

## 2. Corrigir o fluxo e proteger as regras de aceite

- [x] 2.1 Reproduzir a seleção atual com cotas de uma prévia anterior, identificar a falha no POST e recalcular o rateio quando os campos enviados não correspondem exatamente aos participantes atuais; confirmar a criação e a exibição do convite nos testes de view e E2E.
- [x] 2.2 Cobrir o aceite da participação pela própria recebedora e o limite de seleção apenas como recebedora; verificar que não há convite sem seleção explícita, não nasce dívida contra a recebedora, outras dívidas apontam a ela e a cobrança aguarda os demais aceites com `just pytest pixu/charges/tests.py`.

## 3. Validar a jornada integrada

- [x] 3.1 Executar `just pytest` e `just e2e tests/e2e/test_charges.py`; confirmar que os convites comuns, o caso recebedora-convidada e os aceites existentes continuam passando.
- [x] 3.2 Executar `openspec validate --all --no-interactive` e confirmar que a mudança e todas as specs continuam válidas.
