"""Agente com ferramentas permitidas; nunca executa código gerado pelo modelo."""
import json
import os
import unicodedata
import requests
from metrics import scope, summary, monthly, top_cities

FUNCTIONS = {'resumo_vendas':summary, 'receita_mensal':monthly, 'top_cidades':top_cities}
DESCRIPTIONS = {'resumo_vendas':'Receita total, pedidos concluídos, ticket médio, clientes únicos, cancelamento e receita média por cliente.',
                'receita_mensal':'Receita de pedidos concluídos agrupada por mês.',
                'top_cidades':'As cinco cidades com maior receita de pedidos concluídos.'}
TOOLS = [{'type':'function','function':{'name':name,'description':desc,'parameters':{'type':'object','properties':{
    'category':{'type':'string','description':'Categoria exata; omitir para manter o filtro da tela.'},
    'start':{'type':'string','description':'Data inicial inclusiva YYYY-MM-DD'},
    'end':{'type':'string','description':'Data final inclusiva YYYY-MM-DD'}},'additionalProperties':False}}} for name,desc in DESCRIPTIONS.items()]

def execute(name, arguments, df):
    if name not in FUNCTIONS:
        raise ValueError('Ferramenta não permitida')
    if not isinstance(arguments,dict) or set(arguments)-{'category','start','end'}:
        raise ValueError('Parâmetros inválidos')
    if any(not isinstance(v,str) for v in arguments.values()):
        raise ValueError('Parâmetros devem ser textos')
    return FUNCTIONS[name](scope(df,**arguments))

def local_answer(question, df):
    """Demonstração determinística; não se apresenta como LLM."""
    normalized = ''.join(c for c in unicodedata.normalize('NFD',question.lower()) if unicodedata.category(c) != 'Mn')
    name = 'top_cidades' if 'cidade' in normalized else 'receita_mensal' if any(s in normalized for s in ['mensal','por mes']) else 'resumo_vendas'
    value = execute(name,{},df)
    return 'Demonstração local — resultado calculado em Python:', [{'ferramenta':name,'parametros':{},'resultado':value}]

def ask(question, df, key=None, model=None, transport=requests.post):
    key = key or os.getenv('OPENROUTER_API_KEY')
    if not key:
        raise ValueError('Configure OPENROUTER_API_KEY ou use a demonstração local.')
    context = {'categorias':sorted(df.category.unique().tolist()),'inicio':str(df.date.min().date()) if len(df) else None,'fim':str(df.date.max().date()) if len(df) else None}
    messages = [{'role':'system','content':'Responda em português. Use exclusivamente as ferramentas para obter números; nunca estime. Os dados já estão limitados pelos filtros da tela. Não há acesso a arquivos, código ou rede pelas ferramentas. Contexto: '+json.dumps(context,ensure_ascii=False)}, {'role':'user','content':question}]
    trace = []
    for _ in range(5):
        response = transport('https://openrouter.ai/api/v1/chat/completions',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json={'model':model or os.getenv('OPENROUTER_MODEL','openrouter/free'),'messages':messages,'tools':TOOLS,'tool_choice':'auto','provider':{'require_parameters':True},'temperature':0},timeout=60)
        if response.status_code != 200:
            raise ValueError(f'OpenRouter indisponível (HTTP {response.status_code}); confira chave, limite e suporte a ferramentas.')
        message = response.json()['choices'][0]['message']
        calls = message.get('tool_calls') or []
        if not calls:
            if not trace:
                raise ValueError('O modelo respondeu sem consultar ferramentas. Tente uma pergunta de métricas.')
            return message.get('content') or 'Consulte os resultados calculados abaixo.', trace
        messages.append({'role':'assistant','content':message.get('content'),'tool_calls':calls})
        for call in calls:
            name = call['function']['name']
            args = json.loads(call['function']['arguments'])
            result = execute(name,args,df)
            trace.append({'ferramenta':name,'parametros':args,'resultado':result})
            messages.append({'role':'tool','tool_call_id':call['id'],'content':json.dumps(result,ensure_ascii=False)})
    raise ValueError('Limite de chamadas atingido; simplifique a pergunta.')
