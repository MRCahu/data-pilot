# Validação do Data Pilot

Data: 12/11/2026.

## Base completa após ETL

- 121 linhas recebidas; 120 pedidos únicos após remover uma duplicata exata.
- 99 pedidos concluídos.
- Receita: R$ 30.785,70.
- Ticket médio: R$ 310,97.
- 30 clientes únicos com compras concluídas.
- Taxa de cancelamento: 8,33% (10 / 120 pedidos).
- Receita média por cliente: R$ 1.026,19.

## Conferência independente

Uma base pequena no teste usa dois pedidos concluídos de R$ 20,20 e R$ 30,00, um cancelado de R$ 99,00 e um pendente de R$ 80,00. Resultados esperados: receita R$ 50,20, dois pedidos, ticket médio R$ 25,10, um cliente e cancelamento 25%. Essa expectativa é fixada no teste, sem ser derivada da própria função avaliada.

Há testes de deduplicação, conflitos, datas, números, recortes vazios, roundtrip CSV, funções não permitidas e fluxo de ferramentas com transporte simulado. A interface é executada pelo Streamlit AppTest; o botão de consulta local é acionado e seu resultado verificado.

## Limitações

Não houve chamada real ao OpenRouter, pois nenhuma chave foi fornecida. A demonstração local é determinística e identificada como tal. Não são apresentados prints de conversa com um LLM como se tivessem sido obtidos. As respostas do modelo real devem ser conferidas com o rastro das ferramentas.
