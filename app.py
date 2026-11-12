from pathlib import Path
import os
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from metrics import load_data, scope, summary, monthly, top_cities
from agent import ask, local_answer

ROOT = Path(__file__).parent
load_dotenv(ROOT / '.env')
st.set_page_config(page_title='Data Pilot | Mauro Cahu',page_icon='📊',layout='wide')
st.title('📊 Data Pilot')
st.caption('Mauro Roberto Barbosa Cahu • Santander — Dados com Python e IA')
st.info('Base demonstrativa sintética. Valores calculados em Python; não representam vendas reais.')
df = load_data(ROOT / 'data/sales_clean.csv')
page = st.sidebar.radio('Navegação',['Painel de vendas','Converse com os dados'])
category = st.sidebar.selectbox('Categoria',['Todas']+sorted(df.category.unique().tolist()))
dates = st.sidebar.date_input('Período',(df.date.min().date(),df.date.max().date()),min_value=df.date.min().date(),max_value=df.date.max().date())
if len(dates) != 2:
    st.warning('Selecione as duas datas do período.'); st.stop()
filtered = scope(df,None if category == 'Todas' else category,str(dates[0]),str(dates[1]))
values = summary(filtered)
def brl(value):
    return 'R$ '+f'{value:,.2f}'.replace(',','X').replace('.',',').replace('X','.')
if page == 'Painel de vendas':
    columns = st.columns(4)
    for col,label,value in zip(columns,['Receita total','Pedidos concluídos','Ticket médio','Clientes únicos'],[brl(values['receita']),str(values['pedidos']),brl(values['ticket_medio']),str(values['clientes_unicos'])]):
        col.metric(label,value)
    cols = st.columns(2)
    cols[0].metric('Taxa de cancelamento',f"{values['taxa_cancelamento_pct']:.2f}%")
    cols[1].metric('Receita média por cliente',brl(values['receita_media_cliente']))
    rows = monthly(filtered)
    if rows:
        st.plotly_chart(px.bar(pd.DataFrame(rows),x='mes',y='receita',title='Receita mensal • pedidos concluídos',labels={'mes':'Mês','receita':'Receita (R$)'}),use_container_width=True)
        st.plotly_chart(px.bar(pd.DataFrame(top_cities(filtered)),x='cidade',y='receita',title='Top 5 cidades',labels={'cidade':'Cidade','receita':'Receita (R$)'}),use_container_width=True)
    else:
        st.warning('Não há pedidos concluídos neste recorte.')
    with st.expander('Dados e definições'):
        st.write('Uma linha por pedido. Receita = quantidade × preço unitário. Cancelamento = pedidos cancelados / todos os pedidos no recorte. Clientes e demais métricas financeiras consideram apenas concluídos.')
        st.dataframe(filtered,hide_index=True)
    st.download_button('Baixar recorte CSV',filtered.to_csv(index=False,sep=';',decimal=',').encode('utf-8-sig'),'recorte.csv','text/csv')
else:
    st.subheader('Converse com os dados')
    mode = st.radio('Modo',['Demonstração local (sem LLM)','OpenRouter (LLM com ferramentas)'])
    st.caption('Exemplos: Qual a receita e o ticket médio? Receita por mês? Quais cidades mais vendem? Os filtros da barra lateral limitam todas as respostas.')
    if mode.startswith('OpenRouter'):
        st.caption('Ao enviar, sua pergunta, categorias e métricas agregadas do recorte serão transmitidas ao OpenRouter. A base linha a linha não é enviada. Configure a chave no .env.')
    question = st.text_input('Sua pergunta',value='Qual a receita e o ticket médio?')
    if st.button('Consultar dados'):
        try:
            with st.spinner('Consultando métricas…'):
                answer, trace = local_answer(question,filtered) if mode.startswith('Demonstração') else ask(question,filtered)
            st.write(answer)
            st.subheader('Resultados verificáveis das ferramentas')
            for item in trace:
                st.caption(item['ferramenta'])
                result = item['resultado']
                if isinstance(result,dict):
                    st.dataframe(pd.DataFrame([result]),hide_index=True)
                elif result:
                    st.dataframe(pd.DataFrame(result),hide_index=True)
                else:
                    st.info('Sem resultados no recorte.')
                with st.expander('Rastro da chamada'):
                    st.json(item)
            st.caption('A explicação do LLM pode conter erros. Os resultados das ferramentas acima são a referência numérica.')
        except (ValueError,KeyError,TypeError, OSError) as error:
            st.error(str(error))
        except Exception:
            st.error('Falha na consulta. Verifique conectividade e configuração e tente novamente.')
