# Design

## Context

Consulte `proposal.md` para o relato. O formulário envia separadamente a lista de participantes e o recebedor; a view passa ambos ao serviço de criação. O serviço grava a recebedora em `Charge.creditor` e cria participações `PENDING` para os IDs explicitamente selecionados como convidados. A lista “Convites” consulta participações pendentes do usuário, e o cartão já exibe criador, recebedor e cota. No aceite, a regra de domínio evita criar dívida contra a própria recebedora. Há testes de serviço para essa regra e testes de criação com recebedor externo, mas falta uma jornada integrada que valide criação com a mesma conta nos dois papéis e a exibição na caixa de convites.

A reprodução pela view revelou uma corrida entre a prévia HTMX do rateio e o POST tradicional de criação: se a lista de participantes muda e a criação é enviada antes da prévia nova, o POST pode trazer cotas da seleção anterior. A view monta os campos para a seleção atual; cotas ausentes ou pertencentes a outra seleção deixavam o formulário inválido, impedindo a criação e, consequentemente, a emissão do convite.

## Goals / Non-Goals

**Goals:**

- Reproduzir a ocorrência pelo fluxo real de criação e pela conta da pessoa convidada.
- Corrigir a menor fronteira que os testes identificarem como responsável pela perda ou ocultação da participação.
- Garantir convite visível, termos corretos, aceite sem dívida contra si mesma e espera pelos demais convites.

**Non-Goals:**

- Convidar automaticamente alguém escolhido apenas como recebedor.
- Enviar convites por e-mail ou link externo, alterar o modelo financeiro ou redesenhar a experiência de criação.

## Decisions

- **Cobrir a jornada, não apenas o serviço.** Adicionar teste de integração/E2E que cria a cobrança pelo formulário com Ana selecionada como recebedora e participante, autentica Ana e confere o convite pendente com título, criador, recebedora e cota. Isso valida o POST, a persistência, a consulta da lista e a renderização; testes isolados do serviço não cobrem esses limites.
- **Diagnosticar antes de alterar a regra de domínio.** O código atual aparenta preservar os dois papéis de forma independente. A correção deve seguir a falha reproduzida no teste — por exemplo, submissão do formulário, persistência da participação ou consulta da caixa — sem excluir a recebedora da lista de convidados nem adicioná-la implicitamente.
- **Ignorar uma prévia obsoleta no POST.** Cotas manuais só são reaproveitadas quando os campos enviados correspondem exatamente à lista atual de participantes. Se a seleção mudou enquanto a prévia HTMX ainda estava pendente, recalcular a divisão igualitária para a lista atual; não bloquear a criação nem persistir cotas de uma seleção diferente.
- **Manter o aceite como decisão explícita.** A recebedora convidada continua `PENDING` até aceitar ou recusar. Seu aceite não gera dívida contra si própria; as demais participações aceitas geram dívidas para a recebedora, e a cobrança só ativa quando todos os convites atuais forem aceitos.
- **Sem migração prevista.** O contrato usa os campos de cobrança, participação e dívida existentes. Só propor migração se a reprodução revelar uma necessidade concreta de dados ou modelo.

## Risks / Trade-offs

- **O teste local pode passar sem reproduzir a ocorrência relatada** → Confirmar que ele percorre a mesma seleção dos dois campos e a caixa da conta convidada; se passar, comparar versão e configuração do ambiente afetado antes de fazer uma alteração especulativa.
- **Confusão entre recebedor e participante pode voltar** → Manter um caso de fronteira em que selecionar alguém somente como recebedor não cria convite nem participação.
- **O aceite pode criar dívida contra a própria recebedora após uma regressão** → Asserir explicitamente a ausência dessa dívida e a direção correta das demais dívidas após a jornada de aceite.

## Migration Plan

Não há migração de banco prevista. A mudança consiste em cobertura de regressão e correção localizada do fluxo; rollback será a reversão do código alterado, sem transformação de dados.
