import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from urllib.parse import quote
from dash import Dash, dcc, html
import re

# цветовая тема
THEME = {
    'background': '#f2f2f2',    # фон подложки дашборда
    'primary': '#1f77b4',       # синий для заголовков и узлов
    'text': '#2ca02c',          # зелёный для основного текста
    'border': '#1f77b4',        # синий для рамок и ребер
    'frame_bg': '#FFFFFF',      # фон панелей
    'link': '#4a4a4a'           # тёмно‑серый для ссылок
}

BASE_RAW = "https://raw.githubusercontent.com/annkaewstic/AdmisStudents/release/"
CSV_URL = BASE_RAW + quote("Список студентов для расчета контингента на 06.2025.csv")
APPL_URL = BASE_RAW + quote("2024 год.csv")
APPL_URL_1 = BASE_RAW + quote("Итоги приема 2024.csv")

PDF_FILES = [
    "Количество мест на обучение в 2024 году. Очная.pdf",
    "Количество мест на обучение в 2024 году. Очно-заочная.pdf",
    "Количество мест на обучение в 2024 году. заочная.pdf"
]
PDF_LINKS = [(name, BASE_RAW + quote(name)) for name in PDF_FILES]

# загрузка и подготовка данных
df = pd.read_csv(CSV_URL, sep=';', encoding='cp1251')
apps = pd.read_csv(APPL_URL, sep=',', encoding='utf-8')
apps1 = pd.read_csv(APPL_URL_1, sep=',', encoding='utf-8')
df.columns = [c.strip() for c in df.columns]
total_students = len(apps1)
# аббревиатуры и полные названия
df['Fac_abbr']  = df['Факультет'].str.extract(r'\((.*?)\)')
df['Dept_abbr'] = df['Кафедра'].str.extract(r'\((.*?)\)')
fac_full = df.dropna(subset=['Fac_abbr']).drop_duplicates('Fac_abbr').set_index('Fac_abbr')['Факультет'].to_dict()
dept_full = df.dropna(subset=['Dept_abbr']).drop_duplicates('Dept_abbr').set_index('Dept_abbr')['Кафедра'].to_dict()

apps['Fac_abbr']  = apps['Факультет'].str.extract(r'\((.*?)\)')
apps['Dept_abbr'] = apps['Кафедра'].str.extract(r'\((.*?)\)')
fac_full = apps.dropna(subset=['Fac_abbr']).drop_duplicates('Fac_abbr').set_index('Fac_abbr')['Факультет'].to_dict()
dept_full = apps.dropna(subset=['Dept_abbr']).drop_duplicates('Dept_abbr').set_index('Dept_abbr')['Кафедра'].to_dict()

apps1['Fac_abbr']  = apps1['Факультет'].str.extract(r'\((.*?)\)')
apps1['Dept_abbr'] = apps1['Кафедра'].str.extract(r'\((.*?)\)')
fac_full = apps1.dropna(subset=['Fac_abbr']).drop_duplicates('Fac_abbr').set_index('Fac_abbr')['Факультет'].to_dict()
dept_full = apps1.dropna(subset=['Dept_abbr']).drop_duplicates('Dept_abbr').set_index('Dept_abbr')['Кафедра'].to_dict()

# итоги по формам обучения
form_counts1 = apps1['Форма обучения'].value_counts().reset_index()
form_counts1.columns = ['Форма обучения', 'Count']
total_form1 = form_counts1['Count'].sum()
# итоги по бюджету/договору
fin_sums1 = pd.Series({
    'Бюджет': apps1['Бюджет'].sum(),
    'Договор': apps1['Договор'].sum()
}).reset_index()
fin_sums1.columns = ['Основа финансирования', 'Count']
total_fin1 = fin_sums1['Count'].sum()

# --- 1) три графика «заявлений» ---
# 1.1
# Считаем ВСЕ заявления по факультетам и кафедрам (включая дубли)
bar_df = apps.groupby(['Fac_abbr', 'Dept_abbr']).size().reset_index(name='Count')

# bar_count теперь просто сумма заявлений по кафедрам
bar_count = bar_df.copy()  # здесь 'Count' — уже полное количество заявлений по кафедре
# итоги по факультетам
totals = bar_count.groupby('Fac_abbr')['Count'].sum().reset_index(name='Directions')
total_dir = totals['Directions'].sum()
fig_apps_dir = px.bar(
    bar_count,
    x='Fac_abbr',
    y='Count',
    color='Dept_abbr',
    barmode='stack',
    text='Count',
    color_discrete_sequence=[THEME['text']] #THEME['text']
)
# подписи внутри сегментов и ховеры с кафедрами
fig_apps_dir.update_traces(
    texttemplate='%{text}',
    textposition='inside',
    hovertemplate=(
        'Факультет: %{x}<br>' +
        'Кафедра: %{customdata[0]}<br>' +
        'Направлений: %{y}<extra></extra>'
    ),
    customdata=bar_count[['Dept_abbr']].values
)
# над столбцами — итоги по факультетам
for _, row in totals.iterrows():
    fig_apps_dir.add_annotation(
        x=row['Fac_abbr'],
        y=row['Directions'],
        text=str(row['Directions']),
        showarrow=False,
        yshift=8,
        font=dict(color=THEME['primary'], size=12)
    )
# аннотация сверху
fig_apps_dir.add_annotation(
    x=0.5, y=1.12,
    xref='paper', yref='paper',
    text=f"Всего направлений: {total_dir}",
    showarrow=False,
    font=dict(color=THEME['text'], size=14)
)
# оформление графика
fig_apps_dir.update_layout(
    title='Набор на направления<br>(по факультетам и кафедрам)',
    xaxis_title='Факультеты',
    yaxis_title='Количество направлений',
    # вот это принудительно убирает любой поворот:
    xaxis=dict(tickangle=0),
    paper_bgcolor=THEME['frame_bg'],
    plot_bgcolor=THEME['frame_bg'],
    font=dict(color=THEME['primary']),
    title_font=dict(color=THEME['primary']),
    showlegend=False,
    margin=dict(l=20, r=20, t=150, b=20),
    height=600
)


# 1.2 По формам обучения
form_counts = apps['Форма обучения'].value_counts().reset_index()
form_counts.columns = ['Форма обучения', 'Count']
total_form = form_counts['Count'].sum()
fig_apps_form = px.bar(
    form_counts,
    x='Форма обучения', y='Count',
    title="По формам обучения",
    text='Count',
    color_discrete_sequence=[THEME['primary'],THEME['text']]
)
fig_apps_form.add_annotation(
    x=0.5, y=1.05, xref='paper', yref='paper',
    text=f"Всего возможных направлений: {total_form}",
    showarrow=False,
    font=dict(color=THEME['text'], size=14)
)
fig_apps_form.update_traces(textposition='inside')
fig_apps_form.update_layout(
    xaxis_title=None, yaxis_title="Направлений",
    font=dict(color=THEME['primary']),
    title_font=dict(color=THEME['primary']),
    paper_bgcolor=THEME['frame_bg'], plot_bgcolor=THEME['frame_bg'],
    margin=dict(l=20,r=20,t=60,b=20), height=350
)

# 1.3 По бюджету/договору (суммируем колонки)
fin_sums = pd.Series({
    'Бюджет': apps['Бюджет'].sum(),
    'Договор': apps['Договор'].sum()
}).reset_index()
fin_sums.columns = ['Основа финансирования', 'Count']
total_fin  = fin_sums['Count'].sum()
fig_apps_fin = px.bar(
    fin_sums,
    x='Основа финансирования', y='Count',
    title="По бюджет/договор",
    text='Count',
    color_discrete_sequence=[THEME['text'], THEME['primary']]
)
fig_apps_fin.add_annotation(
    x=0.5, y=1.05, xref='paper', yref='paper',
    text=f"Всего мест: {total_fin}",
    showarrow=False,
    font=dict(color=THEME['text'], size=14)
)
fig_apps_fin.update_traces(textposition='inside')
fig_apps_fin.update_layout(
    xaxis_title=None, yaxis_title="Направлений",
    font=dict(color=THEME['primary']),
    title_font=dict(color=THEME['primary']),
    paper_bgcolor=THEME['frame_bg'], plot_bgcolor=THEME['frame_bg'],
    margin=dict(l=20,r=20,t=60,b=20), height=350
)

# === 1) построение tree_fig ===
'''faculties = sorted(df['Fac_abbr'].dropna().unique())
depts_by_fac = {fac: sorted(df[df['Fac_abbr']==fac]['Dept_abbr'].dropna().unique()) for fac in faculties}
coords = {'КнАГУ': (0.5, 1.0)}
n = len(faculties)
for i, fac in enumerate(faculties):
    coords[fac] = ((i+0.5)/n, 0.7)
    m = len(depts_by_fac[fac])
    for j, dept in enumerate(depts_by_fac[fac]):
        x0, x1 = i/n, (i+1)/n
        jitter = (j - (m-1)/2) * 0.005
        coords[dept] = (x0 + (j+0.5)*(x1-x0)/m + jitter, 0.3)
# образовние веток и подписей
edge_traces = []
for source, target in [('КнАГУ', fac) for fac in faculties] + [(fac, dept) for fac in faculties for dept in depts_by_fac[fac]]:
    x0, y0 = coords[source]; x1, y1 = coords[target]
    edge_traces.append(go.Scatter(
        x=[x0, x1], y=[y0, y1],
        mode='lines',
        line=dict(color=THEME['border'], width=2),
        hoverinfo='none',
        showlegend=False
    ))

# для удаления скобок и содержимого внутри:
def strip_parens(s):
    return re.sub(r'\s*\(.*?\)', '', s)

nodes_rf = ['КнАГУ'] + faculties
x_rf = [coords[n][0] for n in nodes_rf]
y_rf = [coords[n][1] for n in nodes_rf]
# hover: для КнАГУ просто «КнАГУ», для факультетов — full name без скобок
hover_rf = ['КнАГУ'] + [strip_parens(fac_full.get(f, f)) for f in faculties]
trace_rf = go.Scatter(
    x=x_rf, y=y_rf,
    mode='markers+text',
    marker=dict(size=20, color=THEME['primary']),
    text=nodes_rf,
    textposition='top center',
    textfont=dict(color='black'),
    hoverinfo='text',
    hovertext=hover_rf,
    showlegend=False
)
dept_nodes = [d for fac in faculties for d in depts_by_fac[fac]]
x_dn = [coords[d][0] for d in dept_nodes]
y_dn = [coords[d][1] for d in dept_nodes]
# hovertext для кафедр без скобок
hover_dn = [strip_parens(dept_full.get(d, d)) for d in dept_nodes]
trace_dn = go.Scatter(
    x=x_dn, y=y_dn,
    mode='markers',
    marker=dict(size=20, color=THEME['primary']),
    hoverinfo='text',
    hovertext=hover_dn,
    showlegend=False
)
# поворот подписей кафедр
annotations = []
for d in dept_nodes:
    x, y = coords[d]
    annotations.append(dict(
        x=x, y=y-0.05,
        text=d,
        textangle=90,
        showarrow=False,
        font=dict(color='black')
    ))
# построение
tree_fig = go.Figure(data=edge_traces + [trace_rf, trace_dn])
tree_fig.update_layout(
    title='Структура университета: КнАГУ → факультеты → кафедры',
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    font=dict(color=THEME['primary']),
    plot_bgcolor=THEME['frame_bg'], paper_bgcolor=THEME['frame_bg'],
    margin=dict(l=20, r=20, t=50, b=20), height=400,
    annotations=annotations
)'''

# === 2) упрощённая stacked bar ===
bar_df = apps1.groupby(['Fac_abbr','Dept_abbr']).size().reset_index(name='Applicants')
# считаем итоги по факультетам
totals = bar_df.groupby('Fac_abbr')['Applicants'].sum().reset_index()
bar_fig = px.bar(
    bar_df,
    x='Fac_abbr',
    y='Applicants',
    color='Dept_abbr',
    barmode='stack',
    text='Applicants',  # подписи внутри сегментов
    color_discrete_sequence=[THEME['border'], THEME['primary']] #THEME['text'],
)
# выводим подписи сегментов внутри
bar_fig.update_traces(
    texttemplate='%{text}',
    textposition='inside'
)
# настройка осей и фона
bar_fig.update_layout(
    title='Фактический набор на направления<br> (по факультетам и кафедрам)',
    xaxis_title='Факультеты',
    yaxis_title='Количество направлений',
    paper_bgcolor=THEME['frame_bg'],
    plot_bgcolor=THEME['frame_bg'],
    font=dict(color=THEME['text']),
    title_font=dict(color=THEME['primary']),
    showlegend=False,
    margin=dict(l=20, r=20, t=150, b=20),
    height=600
)
for _, row in totals.iterrows():
    bar_fig.add_annotation(
        x=row['Fac_abbr'],
        y=row['Applicants'],
        text=str(row['Applicants']),
        showarrow=False,
        yshift=8,
        font=dict(color=THEME['text'], size=12)
    )
bar_fig.add_annotation(
    x=0.5, y=1.12,
    xref='paper', yref='paper',
    text=f"Всего направлений: {total_students}",
    showarrow=False,
    font=dict(color=THEME['text'], size=14)
)

# === 3) Pie chart: проценты внутри + метки снаружи ===
labels = fin_sums1['Основа финансирования']
values = fin_sums1['Count']

pie_fig = go.Figure()

# сегменты-метки (внешний «кольцевой» слой)
pie_fig.add_trace(go.Pie(
    labels=labels,
    values=values,
    hole=0.4,                    # внутренний вырез, чтобы оставить место для процентов
    textinfo='label+value',      # метки и числа снаружи
    textposition='outside',
    textfont=dict(color=THEME['text'], size=14),
    marker=dict(colors=[THEME['primary'], THEME['text']]),
    pull=[0.05, 0.05],
    hovertemplate='%{label}<br>%{value} чел.<extra></extra>',
    sort=False,
    direction='clockwise',
    showlegend=False,
    domain={'x':[0,1],'y':[0,1]}
))
# слой процентов (внутренний круг)
pie_fig.add_trace(go.Pie(
    labels=labels,
    values=values,
    hole=0.5,                    # полукруг
    textinfo='percent',          # только проценты внутри
    textposition='inside',
    insidetextfont=dict(color='white', size=14),
    marker=dict(colors=['rgba(0,0,0,0)']*len(values)),  # прозрачные, чтобы не скрыть внешний слой
    hoverinfo='skip',            # отключаем hover для этого слоя
    sort=False,
    direction='clockwise',
    showlegend=False,
    domain={'x':[0,1],'y':[0,1]}
))
pie_fig.update_layout(
    title=dict(
        text='Абитуриенты, поступившие на бюджет/по договору',
        font=dict(color=THEME['primary'], size=16),
        pad=dict(t=20, b=10)
    ),
    paper_bgcolor=THEME['frame_bg'],
    plot_bgcolor=THEME['frame_bg'],
    margin=dict(l=20, r=20, t=100, b=20),
    height=400
)

# === Сам Dash ===
app = Dash(__name__)
app.index_string = f'''
<!DOCTYPE html>
<html>
  <head>
    {{%metas%}}
    <title>{{%title%}}</title>
    {{%favicon%}}
    {{%css%}}
    <style>
      body {{ background: {THEME['background']}; margin:0; }}
      .pdf-link {{ display: block; font-size: 18px; color: {THEME['link']}; margin-bottom: 8px; text-decoration: none; }}
      .pdf-link:hover {{ text-decoration: underline; }}
      .graph-frame {{ border: 2px solid {THEME['border']}; border-radius: 4px; background: {THEME['frame_bg']}; padding: 10px; }}
    </style>
  </head>
  <body>
    {{%app_entry%}}
    <footer>{{%config%}}{{%scripts%}}{{%renderer%}}</footer>
  </body>
</html>
'''
app.layout = html.Div(
    style={'padding': '20px', 'backgroundColor': THEME['background']},
    children=[
        html.H1('Работа приемной комиссии', style={'textAlign': 'center', 'color': THEME['primary'], 'fontSize': '48px', 'marginBottom': '5px'}),
        html.P('Результаты работы приемной комиссии за 2024 год', style={'textAlign': 'center', 'color': THEME['text'], 'fontStyle': 'italic', 'fontSize': '20px', 'marginBottom': '20px'}),
        html.Div([html.A(name, href=url, target='_blank', className='pdf-link') for name, url in PDF_LINKS], style={'textAlign': 'center', 'marginBottom': '40px'}),
        html.P("Количество заявлений (набор по направлениям):", style={'textAlign': 'center', 'color': THEME['primary'], 'fontSize': '25px', 'marginBottom': '5px'}),
        html.Div(
            style={
                'display':'grid',
                'gridTemplateColumns':'1fr 1fr',
                'gap':'20px',
                'maxWidth':'1200px',
                'margin':'auto'
            },
            children=[
                #html.Div(dcc.Graph(figure=fig_apps_dir), className='graph-frame'),
                html.Div(dcc.Graph(figure=fig_apps_form),className='graph-frame'),
                html.Div(dcc.Graph(figure=fig_apps_fin), className='graph-frame'),
            ]
        ),
                html.Div(
            style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '30px', 'maxWidth': '1200px', 'margin': 'auto', 'marginTop': '30px'},
            children=[
                # вместо tree_fig теперь ваш первый график
                html.Div(dcc.Graph(figure=fig_apps_dir), className='graph-frame'),
                html.Div(dcc.Graph(figure=bar_fig),      className='graph-frame'),
            ]
        ),
        html.Div(
            style={'display': 'flex', 'justifyContent': 'center', 'marginTop': '30px'},
            children=html.Div(dcc.Graph(figure=pie_fig), className='graph-frame', style={'width': '60%'})
        ),
        html.P(f'Всего абитуриентов в 2024 году: {total_fin1}', style={'textAlign': 'center', 'color': THEME['text'], 'fontWeight': 'bold', 'marginTop': '40px'})
    ]
)

if __name__ == '__main__':
    app.run(debug=True)
