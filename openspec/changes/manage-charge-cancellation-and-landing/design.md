# Design

## Context

Consulte `proposal.md` para a motivação e as specs desta mudança para os contratos de comportamento. `Charge` atualmente só admite `AWAITING_ACCEPTANCE` e `ACTIVE`; `Participation` e `Payment` também não possuem estados de cancelamento. Dívidas e pagamentos usam `PROTECT`, enquanto compensações referenciam as duas dívidas protegidas. O detalhe da cobrança já admite acesso do criador, mas consulta dívidas apenas para pagador ou recebedor. O endpoint de comprovante autoriza pagador/recebedor e força download. A landing atual tem dois cartões de benefício, ocultos em parte dos breakpoints, sem uma sequência explicativa.

## Goals / Non-Goals

**Goals:**

- Preservar invariantes e histórico ao cancelar logicamente uma cobrança e ao excluir absolutamente uma cobrança elegível.
- Separar auditoria permanente mínima da limpeza transitória de objetos S3-like.
- Incluir o criador somente na autorização de leitura de comprovantes, sem ampliar autoridade sobre pagamentos.
- Apresentar os fluxos atuais numa sequência vertical acessível e coerente com ambos os temas.

**Non-Goals:**

- Fazer estorno, iniciar transferência, reabrir cobrança cancelada ou recriar dívidas.
- Permitir cancelar/excluir cobranças com compensações aplicadas.
- Criar extrato global, novos meios de pagamento ou decisões automáticas de pagamento.
- Expor exclusão absoluta na interface normal ou apresentar a exclusão administrativa como funcionalidade pública.

## Decisions

1. **Estados explícitos de cancelamento.** Acrescentar `CANCELLED` a `Charge` e `Participation`, e `REVOKED` a `Payment`, atualizando escolhas e constraints na mesma migração. A cobrança registra ator, data e motivo opcional; o estado `CANCELLED` é terminal. Convites ainda pendentes viram cancelados, e todo pagamento vinculado permanece no histórico como revogado. Alternativa considerada: apagar convites/pagamentos ou inferir cancelamento apenas por data; rejeitada por perder histórico e produzir estados ambíguos.

2. **Serviços de domínio transacionais.** Centralizar cancelamento e exclusão em serviços que bloqueiam a linha da cobrança, revalidam ator/estado e consultam compensações em ambos os lados das dívidas antes de alterar qualquer registro. A exclusão absoluta deve apagar explicitamente pagamentos e dívidas protegidos antes das participações e da cobrança. Alternativa considerada: exclusão diretamente em view/admin; rejeitada porque deixa autorização e integridade dependentes da interface.

3. **Auditoria mínima e permanente.** Criar registro independente sem FK para a cobrança apagada: ID original, superusuário, instante e motivo opcional limitado. Criá-lo na mesma transação que a exclusão. Não copiar título, valor, usuário pagante ou conteúdo de comprovante. Alternativa considerada: confiar apenas no log genérico do Django Admin; rejeitada porque pode não preservar o ID e o motivo no formato contratualmente requerido.

4. **Limpeza de storage desacoplada da auditoria.** Capturar os nomes/aliases dos comprovantes em uma fila transitória de exclusão, vinculada à transação de remoção, e despachar limpeza idempotente após commit. A tarefa Celery apaga no storage configurado, remove itens concluídos e repete falhas transitórias; itens pendentes permanecem processáveis sem manter conteúdo de pagamento na auditoria. A rota autenticada de comprovante continuará exigindo um pagamento existente e autorizado, portanto arquivo pendente de limpeza não fica acessível pela aplicação. Alternativa considerada: presumir que `FileField` apaga objetos ao excluir o model; rejeitada, pois o Django não garante essa remoção.

5. **Bloqueio compartilhado para qualquer compensação.** Tanto o serviço do criador quanto a ação administrativa verificam compensações em qualquer dívida ligada, seja como dívida alvo ou recíproca, antes de gravar mudanças. A checagem ocorre sob o bloqueio da cobrança e deve ser compatível com a ordenação de locks já usada ao aplicar compensações. Alternativa considerada: permitir que superusuário apague compensações; rejeitada porque apagaria parte de um evento financeiro recíproco.

6. **Admin restrito e explícito.** Registrar cobrança e auditoria no Django Admin, mas disponibilizar a ação absoluta somente após confirmação customizada e para `is_superuser`. Usuários staff comuns não recebem a permissão efetiva, mesmo que alcancem uma URL administrativa. Motivo é opcional. O bloqueio por compensação é apresentado antes da confirmação e novamente aplicado no serviço.

7. **Acesso a comprovante sem autoridade de decisão.** Reutilizar a rota autenticada de arquivo e estender a autorização ao criador da cobrança da dívida; adicionar links por pagamento na linha da pessoa pagante. Não reutilizar botões do recebedor: os POSTs de confirmar/rejeitar continuam autorizados exclusivamente pelo serviço de pagamentos. Para abrir no navegador, servir com `Content-Disposition: inline`, tipo validado e cabeçalho de segurança apropriado; o endpoint não gera URL pública ou assinada permanente.

8. **Narrativa em fluxo normal da página.** Reorganizar a landing em três seções sem snap obrigatório, sticky storytelling ou captura de rolagem. Mobile e desktop recebem a sequência completa; adaptar composição aos breakpoints e tokens existentes, mantendo logo, CTA e os temas. Exemplos abstratos permanecem representações de estados reais, sem rótulos “demo”/“demonstração”. Alternativa considerada: usar slides ou animação que controla a rolagem; rejeitada por acessibilidade, preferência por movimento reduzido e navegação móvel.

## Risks / Trade-offs

- [Cancelamento de pagamento confirmado pode ser entendido como devolução] → Mostrar explicitamente o estado revogado, manter a evidência histórica, informar que não há estorno e cobrir o cenário na confirmação da ação.
- [A remoção no storage não participa da transação SQL] → Registrar uma fila transitória na transação, usar tarefa idempotente com retry, monitorar itens pendentes e manter a rota sem acesso após remoção do pagamento.
- [Alteração de choices e constraints pode divergir entre migração e saldo] → Atualizar modelos, constraints, serviços, filtros do dashboard e testes no mesmo lote; estados `REVOKED` não reservam nem liquidam e cobranças canceladas ficam fora dos agregados ativos.
- [Link do comprovante no detalhe pode vazar para participante não autorizado] → Renderizar o link somente para o criador da cobrança e conservar a autorização server-side por pagamento, com testes de acesso por URL direta e HTMX.
- [Conteúdo de landing pode prometer capacidade parcialmente implementada] → Fazer a copy depender dos fluxos entregues por esta mudança, manter os exemplos abstratos e não apresentar exclusão administrativa ou extrato global como recurso ao público.

## Migration Plan

1. Atualizar `docs/product-design.md` com estados, ação de cancelamento, acesso a comprovantes e narrativa da landing.
2. Criar migração aditiva para estados, metadados de cancelamento/auditoria e limpeza transitória; preservar os registros atuais sem alteração de estado.
3. Implantar serviços e autorização; validar as migrações e o storage local/S3-like antes de habilitar a ação administrativa.
4. Implantar telas do detalhe, lista e landing; executar testes de unidade, integração e E2E em mobile/desktop e claro/escuro.
5. Rollback: desligar as ações de cancelamento/exclusão e reverter templates/rotas. Se a migração precisar ser revertida, não descartar cobranças já canceladas, auditorias ou filas pendentes; fazer migração corretiva para manter seus dados e estados legíveis até uma reversão segura. Nunca executar rollback que tente recriar cobranças/pagamentos já excluídos.
