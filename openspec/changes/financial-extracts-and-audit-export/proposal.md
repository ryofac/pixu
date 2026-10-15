## Why

O dashboard resume os saldos, mas não leva a pessoa às dívidas que os compõem nem oferece uma linha do tempo exportável para conferência. Os extratos permitem localizar cada cobrança e manter uma cópia auditável de pagamentos confirmados e compensações.

## What Changes

- Tornar os saldos **A pagar**, **A receber** e **Já pago** atalhos para seus extratos.
- Manter a compensação contextual a uma dívida elegível em **A pagar**, sem cartão global de potencial de compensação.
- Resumir até cinco pessoas por direção pela dívida ativa mais antiga de cada uma, somando as dívidas da mesma direção com aquela pessoa.
- Organizar a aba **Cobranças** em grupos financeiros **A pagar primeiro** e **A receber primeiro**, sem remover cobranças pendentes, quitadas ou canceladas do histórico acessível.
- Criar extratos de A pagar e A receber agrupados por pessoa, com uma linha por dívida e link para o detalhe autorizado da cobrança.
- Criar o extrato Já pago como linha do tempo com uma linha por pagamento confirmado ou compensação, mantendo pagamentos confirmados posteriormente revogados identificados como revogados e fora do total liquidado.
- Permitir busca por pessoa ou título nos três extratos e intervalo de datas no Já pago; ordenar dívidas antigas primeiro e liquidações recentes primeiro.
- Exportar todos os resultados correspondentes aos filtros atuais em CSV para planilhas pt-BR e PDF estilizado, sem limitar a exportação à página visível.

## Capabilities

### New Capabilities

- `settlements/financial-extracts`: extratos de dívidas e eventos liquidados, pesquisa, ordenação e exportação auditável.

### Modified Capabilities

- `dashboard`: saldos navegáveis e resumo de pessoas com dívidas ativas mais antigas.

## Impact

Afeta `pixu/dashboard`, `pixu/charges`, o novo app `pixu/extracts` e as consultas financeiras que leem os registros de `pixu/settlements`, além de seus templates Django e rotas autenticadas. O app de extratos terá namespace e rotas próprias; pagamentos e compensações continuam sendo a fonte de dados em settlements. A geração do PDF pode exigir uma dependência compatível com Python 3.14 e com os contêineres de produção; CSV pode ser produzido no servidor sem serviço externo. Os arquivos devem respeitar as permissões dos extratos e não expor comprovantes privados.
