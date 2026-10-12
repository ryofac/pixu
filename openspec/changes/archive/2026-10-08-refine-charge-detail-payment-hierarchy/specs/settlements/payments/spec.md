# Spec Delta

## ADDED Requirements

### Requirement: Confirmação manual contextual no detalhe da cobrança

Quando o recebedor autenticado visualiza uma participação com pagamento `PENDING`, a linha dessa participação MUST identificar que o Pix aguarda confirmação manual, discriminar o valor pendente sem reduzir prematuramente o saldo aberto e oferecer a ação rápida **“Confirmar recebimento”**. A interface MUST orientar a conferência no extrato antes da decisão e MUST NOT sugerir verificação bancária automática pelo Pixu.

A ação de confirmar ou rejeitar MUST continuar disponível somente ao recebedor da dívida. Criadores que não são recebedores, outros participantes e convidados MUST NOT receber ação de decisão na linha; uma tentativa direta no servidor continua negada. Após uma decisão válida por HTMX, a atualização MUST substituir o conteúdo financeiro afetado, anunciar o resultado e reordenar a participação conforme o novo estado sem exigir recarregamento completo.

#### Scenario: Recebedor confirma Pix pendente pela linha da pessoa

- **WHEN** o recebedor confere o extrato e aciona “Confirmar recebimento” para um Pix `PENDING` no detalhe da cobrança
- **THEN** o pagamento é confirmado pelas regras existentes, a linha atualiza saldo e estado, e a pessoa é reordenada dentro de seu grupo de identidade

#### Scenario: Criador sem papel de recebedor não vê decisão

- **WHEN** o criador abre a cobrança mas não é o recebedor de uma dívida com Pix `PENDING`
- **THEN** pode manter os acessos de leitura já autorizados, mas não vê ações de confirmar ou rejeitar e o servidor recusa uma tentativa forjada de decisão

#### Scenario: Pix pendente preserva saldo aberto

- **WHEN** o recebedor vê uma cota com saldo aberto de R$ 117,50 e Pix `PENDING` de R$ 117,50
- **THEN** a linha identifica o Pix aguardando confirmação e continua apresentando R$ 117,50 como saldo aberto até a confirmação manual
