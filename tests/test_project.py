import json
import pandas as pd
import pytest
from metrics import clean_data, summary, scope, monthly, top_cities, load_data
from agent import execute, ask, local_answer

def sample():
    return pd.DataFrame([
        ['1','2026-01-02','A','Casa','Recife',' Concluído ',2,10.10],
        ['2','2026-02-03','A','Casa','Olinda','completed',1,30],
        ['3','2026-02-04','B','Tecnologia','Recife','cancelado',1,99],
        ['4','2026-02-05','C','Casa','Recife','pending',1,80]],columns=['order_id','date','customer_id','category','city','status','quantity','unit_price'])

def test_metrics_and_denominators():
    df=clean_data(sample())
    assert summary(df)=={'receita':50.2,'pedidos':2,'ticket_medio':25.1,'clientes_unicos':1,'taxa_cancelamento_pct':25.0,'receita_media_cliente':50.2,'pedidos_no_recorte':4}
    assert monthly(df)==[{'mes':'2026-01','receita':20.2},{'mes':'2026-02','receita':30.0}]
    assert top_cities(df)[0]=={'cidade':'Olinda','receita':30.0}

def test_empty_and_filter():
    df=clean_data(sample())
    assert summary(scope(df,start='2026-03-01'))['receita']==0
    assert summary(scope(df,category='Casa',end='2026-01-02'))['pedidos']==1
    with pytest.raises(ValueError): scope(df,start='2026-03-01',end='2026-01-01')

def test_duplicates_and_conflicts():
    raw=sample()
    assert len(clean_data(pd.concat([raw,raw.iloc[:1]])))==4
    bad=raw.iloc[:1].copy();bad['quantity']=3
    with pytest.raises(ValueError): clean_data(pd.concat([raw,bad]))

@pytest.mark.parametrize('column,value',[('quantity',-1),('quantity',1.5),('unit_price',float('inf')),('status','other'),('date',None),('customer_id','')])
def test_bad_data(column,value):
    df=sample().astype(object);df.loc[0,column]=value
    with pytest.raises((ValueError,TypeError)): clean_data(df)

def test_csv_roundtrip(tmp_path):
    df=clean_data(sample()); path=tmp_path/'data.csv'
    df.to_csv(path,index=False,sep=';',decimal=',')
    assert summary(load_data(path))==summary(df)

def test_tool_validation():
    df=clean_data(sample())
    for name,args in [('exec',{}),('resumo_vendas',{'code':'print(1)'}),('resumo_vendas',{'start':1})]:
        with pytest.raises(ValueError):execute(name,args,df)

def test_agent_tool_loop():
    class Response:
        status_code=200
        def __init__(self,message):self.message=message
        def json(self):return {'choices':[{'message':self.message}]}
    calls=[]
    def transport(url,**kwargs):
        calls.append(json.loads(json.dumps(kwargs['json'])))
        if len(calls)==1:
            return Response({'role':'assistant','content':None,'tool_calls':[{'id':'tool1','type':'function','function':{'name':'resumo_vendas','arguments':'{}'}}]})
        assert json.loads(calls[-1]['messages'][-1]['content'])['receita']==50.2
        return Response({'role':'assistant','content':'Receita: R$ 50,20.'})
    answer,trace=ask('Qual a receita?',clean_data(sample()),key='test-not-real',transport=transport)
    assert '50,20' in answer and trace[0]['resultado']['receita']==50.2
    assert len(calls)==2

def test_local_demo():
    _,trace=local_answer('Quais cidades vendem mais?',clean_data(sample()))
    assert trace[0]['ferramenta']=='top_cidades'

def test_app_dashboard_and_chat():
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_file('../app.py').run(timeout=20)
    assert not app.exception
    assert app.metric[0].label=='Receita total'
    app.sidebar.radio[0].set_value('Converse com os dados').run()
    app.button[0].click().run()
    assert not app.exception
    assert len(app.dataframe)==1
