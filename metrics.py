"""ETL e métricas: uma linha por pedido, valores monetários em centavos."""
from pathlib import Path
import pandas as pd

REQUIRED = {'order_id','date','customer_id','category','city','status','quantity','unit_price'}

def clean_data(raw):
    missing = REQUIRED - set(raw.columns)
    if missing:
        raise ValueError(f'Colunas ausentes: {sorted(missing)}')
    df = raw.copy().drop_duplicates()
    for col in ['order_id','customer_id','category','city','status']:
        if df[col].isna().any():
            raise ValueError(f'Valor ausente em {col}')
        df[col] = df[col].astype(str).str.strip()
        if df[col].eq('').any():
            raise ValueError(f'Valor vazio em {col}')
    if df.order_id.duplicated().any():
        raise ValueError('Pedidos conflitantes com o mesmo order_id')
    df['date'] = pd.to_datetime(df.date, errors='raise').dt.normalize()
    if df.date.isna().any():
        raise ValueError('Data ausente')
    df['status'] = df.status.str.lower().replace({'concluído':'completed','concluido':'completed','cancelado':'cancelled','pendente':'pending'})
    if not df.status.isin(['completed','cancelled','pending']).all():
        raise ValueError('Status desconhecido')
    for col in ['quantity','unit_price']:
        df[col] = pd.to_numeric(df[col], errors='raise')
        if df[col].isna().any() or not df[col].map(lambda x: float('-inf') < x < float('inf')).all():
            raise ValueError(f'Número inválido em {col}')
    if (df.quantity <= 0).any() or (df.quantity % 1 != 0).any() or (df.unit_price < 0).any():
        raise ValueError('Quantidade deve ser inteira positiva e preço não negativo')
    df['unit_price_cents'] = (df.unit_price * 100).round().astype('int64')
    df['revenue_cents'] = df.quantity.astype('int64') * df.unit_price_cents
    df['revenue'] = df.revenue_cents / 100
    return df.sort_values(['date','order_id']).reset_index(drop=True)

def prepare(source='data/sales.csv', target='data/sales_clean.csv'):
    df = clean_data(pd.read_csv(source))
    df.to_csv(target, index=False, sep=';', decimal=',', date_format='%Y-%m-%d')
    return df

def load_data(path='data/sales_clean.csv'):
    return clean_data(pd.read_csv(path, sep=';', decimal=','))

def scope(df, category=None, start=None, end=None):
    result = df
    if category:
        if category not in df.category.unique():
            raise ValueError('Categoria inexistente')
        result = result[result.category == category]
    if start and end and pd.Timestamp(start) > pd.Timestamp(end):
        raise ValueError('Data inicial posterior à final')
    if start:
        result = result[result.date >= pd.Timestamp(start)]
    if end:
        result = result[result.date <= pd.Timestamp(end)]
    return result

def summary(df):
    done = df[df.status == 'completed']
    revenue = int(done.revenue_cents.sum()) / 100
    orders = int(len(done))
    clients = int(done.customer_id.nunique())
    return {'receita':revenue, 'pedidos':orders, 'ticket_medio':round(revenue/orders,2) if orders else 0,
            'clientes_unicos':clients, 'taxa_cancelamento_pct':round(100*df.status.eq('cancelled').sum()/len(df),2) if len(df) else 0,
            'receita_media_cliente':round(revenue/clients,2) if clients else 0, 'pedidos_no_recorte':int(len(df))}

def monthly(df):
    done = df[df.status == 'completed'].copy()
    done['mes'] = done.date.dt.strftime('%Y-%m')
    result = done.groupby('mes',as_index=False).revenue_cents.sum()
    result['receita'] = result.pop('revenue_cents') / 100
    return result.to_dict('records')

def top_cities(df):
    result = df[df.status == 'completed'].groupby('city',as_index=False).revenue_cents.sum()
    result = result.sort_values(['revenue_cents','city'],ascending=[False,True]).head(5)
    result['receita'] = result.pop('revenue_cents') / 100
    return result.rename(columns={'city':'cidade'}).to_dict('records')

if __name__ == '__main__':
    print(summary(prepare()))
