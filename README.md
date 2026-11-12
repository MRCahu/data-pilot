# 📊 Data Pilot — análise inteligente de vendas

**Autor:** Mauro Roberto Barbosa Cahu ([MRCahu](https://github.com/MRCahu))  
**Desafio:** Data Pilot — Análise Inteligente de Dados com Agentes de IA  
**Bootcamp:** Santander — Dados com Python e IA | DIO

Aplicação em Python com dois menus: **Painel de vendas** e **Converse com os dados**. As funções Python calculam os indicadores; o modelo escolhe ferramentas e explica seus resultados. O rastro de cada chamada fica visível para conferência.

## Executar

Python 3.11 ou 3.12. No terminal:

```bash
git clone https://github.com/MRCahu/data-pilot.git
cd data-pilot
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python metrics.py
streamlit run app.py
```

Abra a URL local informada pelo Streamlit. A demonstração local funciona sem chave e **não usa LLM**. Ela reconhece perguntas simples de resumo, receita mensal e cidades; não interpreta datas escritas na pergunta. Use os filtros da tela.

Para o agente real:

1. Copie `.env.example` para `.env` na pasta do projeto.
2. Configure `OPENROUTER_API_KEY` com sua própria chave e mantenha `OPENROUTER_MODEL=openrouter/free` ou escolha outro modelo que suporte ferramentas.
3. Reinicie o aplicativo e selecione **OpenRouter (LLM com ferramentas)**.
4. Pergunte: “Qual a receita e o ticket médio?”, “Receita por mês?” ou “Quais cidades mais vendem?”.

A integração envia perguntas, categorias e resultados agregados ao OpenRouter; não envia linhas da base. O serviço pode aplicar limites ou indisponibilidade. A chave nunca deve ser publicada. O `.env` está ignorado pelo Git. O código trata falhas sem mostrar a resposta bruta do provedor.

## Dados e ETL

`data/sales.csv` é uma **base sintética própria**, sem informações pessoais reais, criada com semente 42 para este projeto. Não é o dataset do instrutor. Contém 120 pedidos e uma repetição exata proposital. Não foram copiados códigos ou dados do repositório do instrutor.

| Campo | Significado |
|---|---|
| `order_id` | Identificador único do pedido; uma linha por pedido |
| `date` | Data do pedido |
| `customer_id` | Identificador fictício do cliente |
| `category`, `city` | Categoria e cidade |
| `status` | completed, cancelled ou pending |
| `quantity`, `unit_price` | Quantidade e preço unitário |

O ETL converte datas, padroniza status, remove duplicatas exatas e rejeita IDs conflitantes, campos vazios, números não finitos e quantidades inválidas. Preços são arredondados para centavos antes da multiplicação. O arquivo tratado `data/sales_clean.csv` usa **ponto e vírgula como separador e vírgula decimal**, na escrita e leitura. O grão atual não representa múltiplos itens de um mesmo pedido; uma base com itens exige adaptar o ETL antes de usá-la.

## Indicadores e ferramentas

Todas as ferramentas respeitam o recorte de categoria e período da tela. Parâmetros opcionais podem restringir ainda mais o recorte; não recuperam dados excluídos pelos filtros.

| Ferramenta | Resultado |
|---|---|
| `resumo_vendas` | Receita, pedidos concluídos, ticket médio, clientes únicos, taxa de cancelamento e receita média por cliente |
| `receita_mensal` | Receita por mês |
| `top_cidades` | Cinco cidades com maior receita |

Parâmetros opcionais: `category` (nome exato), `start` e `end` (YYYY-MM-DD, limites inclusivos). O agente aceita apenas funções da lista permitida, valida parâmetros e limita a cinco rodadas de chamadas. Não usa `eval`, execução de Python/SQL gerado nem framework de agentes.

| Métrica | Definição |
|---|---|
| Receita | Soma de quantidade × preço unitário dos pedidos concluídos |
| Pedidos | Quantidade de pedidos concluídos |
| Ticket médio | Receita / pedidos concluídos |
| Clientes únicos | Clientes distintos com pedidos concluídos |
| Cancelamento | Cancelados / **todos os pedidos do recorte**, inclusive pendentes |
| Receita média por cliente | Receita / clientes únicos com pedidos concluídos |

Divisões sem denominador retornam zero. Meses sem pedidos concluídos não aparecem no gráfico. A taxa de cancelamento precisa considerar todos os status, ao contrário das métricas financeiras.

**Melhorias implementadas:** receita média por cliente, ranking de cidades, filtro por intervalo de datas, exportação CSV e trilha verificável de ferramentas.

## Arquitetura

- `metrics.py`: ETL, leitura, filtros e cálculos compartilhados pelo painel e chat.
- `agent.py`: descrição de ferramentas, validação, chamadas OpenRouter e demonstração local.
- `app.py`: interface Streamlit, gráficos Plotly e resultados auditáveis.
- `data/`: entrada sintética e saída tratada.
- `tests/test_project.py`: casos numéricos, filtros, qualidade, contrato do agente e interface.
- `.github/workflows/tests.yml`: execução automática dos testes.
- `docs/validacao.md`: evidências e limites da validação.

## Testar

```bash
python -m pytest -q
```

Os testes do agente simulam o transporte HTTP para conferir o ciclo modelo → ferramenta → resultado → resposta. **Não equivalem a uma execução real no OpenRouter**. A aplicação também é testada com Streamlit AppTest nos dois menus. Não há chave OpenRouter incluída ou chamada real ao provedor nesta entrega. O texto do LLM ainda pode conter erros; os resultados calculados e exibidos na tabela são a referência numérica.

## Referências

- [Desafio DIO](https://web.dio.me/track/santander-dados-com-python-e-ia)
- [OpenRouter API e ferramentas](https://openrouter.ai/docs/api/reference/overview)
- [Streamlit](https://docs.streamlit.io/)
- [pandas](https://pandas.pydata.org/docs/)
- [Plotly](https://plotly.com/python/)

Projeto educacional desenvolvido com assistência de IA, com testes automatizados e limitações descritas acima.
