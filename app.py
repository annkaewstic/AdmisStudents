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

PDF_FILES = [
    "Количество зачисленных на обучение в 2024 году. Очная.pdf",
    "Количество зачисленных на обучение в 2024 году. Очно-заочная.pdf",
    "Количество зачисленных на обучение в 2024 году. заочная.pdf"
]
PDF_LINKS = [(name, BASE_RAW + quote(name)) for name in PDF_FILES]

# загрузка и подготовка данных
df = pd.read_csv(CSV_URL, sep=';', encoding='cp1251')
apps = pd.read_csv(APPL_URL, sep=',', encoding='utf-8')
df.columns = [c.strip() for c in df.columns]
total_students = len(df)
# аббревиатуры и полные названия
df['Fac_abbr']  = df['Факультет'].str.extract(r'\((.*?)\)')
df['Dept_abbr'] = df['Кафедра'].str.extract(r'\((.*?)\)')
fac_full = df.dropna(subset=['Fac_abbr']).drop_duplicates('Fac_abbr').set_index('Fac_abbr')['Факультет'].to_dict()
dept_full = df.dropna(subset=['Dept_abbr']).drop_duplicates('Dept_abbr').set_index('Dept_abbr')['Кафедра'].to_dict()

# --- 1) три графика «заявлений» ---
# функция обрезки
def truncate(name, length=40):
    return name if len(name) <= length else name[:length-3] + '...'

# 1.1 По направлениям — собираем списки с обрезкой
dir_series = apps['Направление'].value_counts()
dir_df = dir_series.reset_index()
dir_df.columns = ['Направление', 'Count']
# создаём колонку с усечёнными названиями
dir_df['Short'] = dir_df['Направление'].apply(truncate)
# считаем общий итог
total_dir = dir_df['Count'].sum()
# группируем по Count и склеиваем короткие названия через <br>
grouped = (
    dir_df
    .groupby('Count')['Short']
    .agg(lambda names: '<br>'.join(names))
    .reset_index(name='HoverList')
)
fig_apps_dir = px.bar(
    grouped,
    x='Count',
    y='Count',
    text='Count',
    color_discrete_sequence=[THEME['text']],
    title="По направлениям"
)
fig_apps_dir.add_annotation(
    x=0.5, y=1.05,
    xref='paper', yref='paper',
    text=f"Всего заявлений: {total_dir}",
    showarrow=False,
    font=dict(color=THEME['text'], size=14)
)
fig_apps_dir.update_traces(
    textposition='inside',
    hovertemplate=(
        'Заявлений: %{x}<br>' +
        'Направления:<br>%{customdata[0]}<extra></extra>'
    ),
    customdata=grouped[['HoverList']].values
)
fig_apps_dir.update_layout(
    xaxis_title="Количество заявлений",
    yaxis_title="Количество заявлений",
    paper_bgcolor=THEME['frame_bg'],
    plot_bgcolor=THEME['frame_bg'],
    margin=dict(l=20, r=20, t=60, b=20),
    height=350,
    showlegend=False
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
    text=f"Всего заявлений: {total_form}",
    showarrow=False,
    font=dict(color=THEME['text'], size=14)
)
fig_apps_form.update_traces(textposition='inside')
fig_apps_form.update_layout(
    xaxis_title=None, yaxis_title="Заявлений",
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
    xaxis_title=None, yaxis_title="Заявлений",
    paper_bgcolor=THEME['frame_bg'], plot_bgcolor=THEME['frame_bg'],
    margin=dict(l=20,r=20,t=60,b=20), height=350
)

# === 1) построение tree_fig ===
faculties = sorted(df['Fac_abbr'].dropna().unique())
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
hover_rf = ['КнАГУ'] + [strip_parens(fac_full[f]) for f in faculties]
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
hover_dn = [strip_parens(dept_full[d]) for d in dept_nodes]
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
    title='Структура контингента: КнАГУ → факультеты → кафедры',
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    font=dict(color=THEME['primary']),
    plot_bgcolor=THEME['frame_bg'], paper_bgcolor=THEME['frame_bg'],
    margin=dict(l=20, r=20, t=50, b=20), height=400,
    annotations=annotations
)

# === 2) упрощённая stacked bar ===
bar_df = df.groupby(['Fac_abbr','Dept_abbr']).size().reset_index(name='Students')
# считаем итоги по факультетам
totals = bar_df.groupby('Fac_abbr')['Students'].sum().reset_index()
bar_fig = px.bar(
    bar_df,
    x='Fac_abbr',
    y='Students',
    color='Dept_abbr',
    barmode='stack',
    text='Students',  # подписи внутри сегментов
    color_discrete_sequence=[THEME['border'], THEME['primary']] #THEME['text'],
)
# выводим подписи сегментов внутри
bar_fig.update_traces(
    texttemplate='%{text}',
    textposition='inside'
)
# настройка осей и фона
bar_fig.update_layout(
    title='Количество студентов по факультетам и кафедрам',
    xaxis_title='Факультеты',
    yaxis_title='Количество студентов',
    paper_bgcolor=THEME['frame_bg'],
    plot_bgcolor=THEME['frame_bg'],
    font=dict(color=THEME['text']),
    title_font=dict(color=THEME['primary']),
    showlegend=False,
    margin=dict(l=20, r=20, t=80, b=20),
    height=400
)
for _, row in totals.iterrows():
    bar_fig.add_annotation(
        x=row['Fac_abbr'],
        y=row['Students'],
        text=str(row['Students']),
        showarrow=False,
        yshift=8,
        font=dict(color=THEME['text'], size=12)
    )
bar_fig.add_annotation(
    x=0.5, y=1.12,
    xref='paper', yref='paper',
    text=f"Всего студентов: {total_students}",
    showarrow=False,
    font=dict(color=THEME['text'], size=14)
)

# === 3) pie chart ===
status_df = df['Статус'].value_counts().rename_axis('Status').reset_index(name='Count')
custom_labels = status_df.apply(lambda row: f"{row['Status']}<br>{row['Count']} студентов", axis=1)
status_df = df['Статус'].value_counts().rename_axis('Status').reset_index(name='Count')
pie_fig = px.pie(
    status_df,
    names='Status',
    values='Count',
    color_discrete_sequence=[THEME['primary'], THEME['text']],
    title='Процент студентов: обучающихся и в академическом отпуске'
)
# проценты
pie_fig.update_traces(
    text=custom_labels,
    textinfo='percent',
    textposition='inside',
    insidetextfont=dict(color='white', size=14),
    hovertemplate='%{label}<br>Доля: %{percent}<extra></extra>'
)
# показываем и название, и количество
pie_fig.update_traces(
    textinfo='label+value',
    textposition='outside',
    textfont=dict(color=THEME['text'], size=14),
    pull=[0.05, 0.05]
)
pie_fig.update_layout(
    # поднимаем заголовок и даём ему дополнительный внутренний отступ
    title=dict(
        text='Процент студентов: обучающихся и в академическом отпуске',
        font=dict(color=THEME['primary'], size=16),
        pad=dict(t=20, b=10)
    ),
    paper_bgcolor=THEME['frame_bg'],
    plot_bgcolor=THEME['frame_bg'],
    font=dict(color=THEME['text']),
    margin=dict(l=20, r=20, t=100, b=20),  # t=100 даёт место над кругом
    height=400,
    showlegend=False
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
        html.H1('Admission Dashboard', style={'textAlign': 'center', 'color': THEME['primary'], 'fontSize': '48px', 'marginBottom': '5px'}),
        html.P('Результаты работы приемной комиссии за 2024 год', style={'textAlign': 'center', 'color': THEME['text'], 'fontStyle': 'italic', 'fontSize': '20px', 'marginBottom': '20px'}), #Контингент студентов за июнь 2025
        html.Div([html.A(name, href=url, target='_blank', className='pdf-link') for name, url in PDF_LINKS], style={'textAlign': 'center', 'marginBottom': '40px'}),
        html.P("Количество заявлений:", style={'textAlign': 'center', 'color': THEME['primary'], 'fontSize': '25px', 'marginBottom': '5px'}),
        html.Div(
            style={
                'display':'grid',
                'gridTemplateColumns':'1fr 1fr 1fr',
                'gap':'20px',
                'maxWidth':'1200px',
                'margin':'auto'
            },
            children=[
                html.Div(dcc.Graph(figure=fig_apps_dir), className='graph-frame'),
                html.Div(dcc.Graph(figure=fig_apps_form),className='graph-frame'),
                html.Div(dcc.Graph(figure=fig_apps_fin), className='graph-frame'),
            ]
        ),
        html.Div(
            style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px', 'maxWidth': '1200px', 'margin': 'auto', 'marginTop': '30px'},
            children=[
                html.Div(dcc.Graph(figure=tree_fig), className='graph-frame'),
                html.Div(dcc.Graph(figure=bar_fig), className='graph-frame'),
            ]
        ),
        html.Div(
            style={'display': 'flex', 'justifyContent': 'center', 'marginTop': '30px'},
            children=html.Div(dcc.Graph(figure=pie_fig), className='graph-frame', style={'width': '60%'})
        ),
        html.P(f'Всего студентов в 2025 году: {total_students}', style={'textAlign': 'center', 'color': THEME['text'], 'fontWeight': 'bold', 'marginTop': '40px'})
    ]
)

if __name__ == '__main__':
    app.run(debug=True)
