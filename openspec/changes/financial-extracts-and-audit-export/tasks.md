## 1. Dependências de PDF

- [ ] 1.1 Fixar uma versão do WeasyPrint compatível com Python 3.14 em `pyproject.toml` e atualizar `uv.lock`; verificar a coerência do lock e a importação da biblioteca no ambiente Python do projeto.
- [ ] 1.2 Instalar as bibliotecas Pango necessárias nas imagens Django local e de produção; verificar build e renderização de um PDF mínimo nas duas imagens.

## 2. Consultas financeiras e eventos

- [ ] 2.1 Consolidar o cálculo em centavos do saldo aberto por dívida, contabilizando pagamentos confirmados e compensações dos dois lados e mantendo pagamentos pendentes apenas como reserva; verificar com cenários de dívida aberta, parcial, quitada e compensada.
- [ ] 2.2 Implementar consultas pagináveis e autorizadas de **A pagar** e **A receber**, agrupando contas por ID e convidados sem conta por participação; verificar cobranças ativas, aceites, saldo positivo, convidados, pagamentos parciais e exclusão de criadores sem relação financeira.
- [ ] 2.3 Normalizar pagamentos e compensações em linhas de **Já pago**, incluindo pagamento confirmado depois revogado somente quando houver `confirmed_at`, mantendo estado visível e excluindo seu valor do total; verificar confirmação manual/automática, compensação sem duplicação e eventos revogados.
- [ ] 2.4 Implementar busca por pessoa/título, período inclusivo em **Já pago**, ordenação e desempate estáveis; verificar datas-limite, datas inválidas, preservação dos filtros na paginação e uso da data efetiva de liquidação.

## 3. Dashboard

- [ ] 3.1 Tornar **A pagar**, **A receber** e **Já pago** atalhos para os extratos e calcular o total pago sem eventos revogados; remover o cartão global de compensação potencial e manter a recomendação junto a uma dívida elegível a pagar; verificar totais e destinos dos links.
- [ ] 3.2 Exibir até cinco pessoas em cada direção pela dívida aberta mais antiga, somando os saldos abertos ativos daquela direção; manter participações convidadas separadas mesmo com nomes iguais; verificar limite, prioridade, agregação e ausência de dívidas.
- [ ] 3.3 Separar a aba **Cobranças** em **A pagar primeiro** e **A receber primeiro**, ordenar cada grupo pela dívida em aberto mais antiga e preservar as demais cobranças em **Outras cobranças**; verificar agregação de múltiplas dívidas da mesma cobrança e retenção do histórico.

## 4. Páginas de extrato

- [ ] 4.1 Criar e registrar o app Django `pixu.extracts`, com namespace de URL próprio, templates do app e páginas autenticadas, responsivas e paginadas; renderizar dívidas individuais agrupadas por pessoa em **A pagar/A receber**, cada uma ligada ao detalhe existente, e eventos individuais em **Já pago**; verificar navegação, estados vazios, leitura mobile e teclado.
- [ ] 4.2 Adicionar formulários GET de busca e período, validação acessível e links de paginação/download que preservem filtros; verificar funcionamento sem JavaScript e que buscas não ampliem o escopo autorizado.

## 5. Exportações de auditoria

- [ ] 5.1 Gerar CSV UTF-8 com BOM, separador `;`, IDs estáveis, centavos exatos, datas e metadados de pagamento/compensação; escapar texto contra injeção de fórmulas; verificar conteúdo, acentuação, valores e texto iniciado por caracteres de fórmula.
- [ ] 5.2 Criar template de impressão Pixu e gerar PDF com filtros, data de geração, totais, páginas e todos os resultados filtrados; verificar tipo de arquivo, campos, quebra de páginas e inclusão de eventos revogados apenas como auditáveis.
- [ ] 5.3 Aplicar autorização às rotas de download e impedir exposição de conteúdo ou URL de comprovantes; verificar acesso direto por titular, recebedor, terceiro e criador sem relação financeira.

## 6. Validação da mudança

- [x] 6.1 Conferir que as especificações, o dashboard, as três páginas e os dois formatos concordam sobre saldo, eventos, filtros e permissões; verificar a mudança com `openspec validate financial-extracts-and-audit-export --strict --no-interactive`.
