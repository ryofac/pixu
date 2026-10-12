# Tasks

## 1. Contexto financeiro e ordenação

- [x] 1.1 Extrair o construtor reutilizável do contexto do detalhe e montar, em lote, as linhas financeiras do recebedor com participação, dívida, Pix, compensação, itens e comprovantes autorizados; verificar com testes `pytest` que o resumo reproduz saldo aberto, reserva pendente e quitação sem consultas por linha.
- [x] 1.2 Implementar os grupos exclusivos Contas Pixu e Convites Anônimos e a chave de ordenação por atenção financeira, incluindo cota própria, convite pendente, saldo residual e tempo em aberto somente sem pagamento iniciado; verificar com testes de detalhe que cada pessoa ocorre uma vez, os grupos e a ordem esperados são renderizados e nenhum código/tokens de convidado aparece.

## 2. Detalhe do recebedor e confirmação contextual

- [x] 2.1 Substituir, apenas na visão do recebedor, os cartões paralelos de participantes e dívidas pelo cartão Participantes e Cotas do protótipo, preservando valores, itens, comprovantes e histórico sob demanda em modal desktop/bottom sheet mobile; verificar por testes de template e viewport que não há duplicação, overflow horizontal nem ação financeira para a cota própria.
- [x] 2.2 Inserir em cada Pix `PENDING` a orientação de conferência manual, os formulários de confirmar/rejeitar e o estado textual de saldo sem prometer confirmação automática; verificar com `pytest` que somente o recebedor vê e consegue executar as decisões e que múltiplos Pix pendentes permanecem decisões distintas.
- [x] 2.3 Fazer as respostas HTMX de decisão reconstruírem `#charge-content`, anunciarem o resultado e reaplicarem a ordenação do grupo; verificar com testes de view que confirmação, rejeição e erro preservam CSRF/autorização, retornam o fragmento correto e não exigem recarga completa.

## 3. Regressão e entrega visual

- [x] 3.1 Atualizar os testes de integração de cobrança e pagamento para cobrir Pix pendente, pagamento não iniciado há oito dias, saldo parcial/histórico, quitação por Pix ou compensação e criador que não é recebedor; verificar executando os módulos `pytest` afetados.
- [x] 3.2 Atualizar os testes E2E pytest do detalhe para desktop e celular, incluindo reordenação depois de confirmação HTMX, foco/feedback e a ausência de overflow ou ações indevidas; verificar executando os testes E2E afetados.
- [x] 3.3 Compilar os assets com `npm run build`, conferir o detalhe em navegador nos breakpoints móvel e desktop contra o protótipo aprovado e registrar qualquer ajuste necessário antes de marcar a mudança pronta.

## 4. Composição visível das cotas

- [x] 4.1 Registrar em `docs/product-design.md` que a linha de uma cota itemizada mostra base, cada item extra e total, e que o atalho de detalhes fica alinhado ao início; verificar a consistência com esta especificação e com o protótipo.
- [x] 4.2 Atualizar a linha do participante para mostrar a expressão monetária exata quando houver itens extras e alinhar “Ver detalhes da cota” à esquerda; adicionar cobertura da composição com dois extras e da cota sem extras, verificando com `just pytest pixu/charges/test_detail_hierarchy.py`.
- [x] 4.3 Compilar os estilos com `npm run build` e revisar a linha em viewport de 375 px e 1024 px, confirmando que a expressão quebra sem overflow e que o foco do atalho continua visível.
