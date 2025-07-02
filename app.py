import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from urllib.parse import quote
from dash import Dash, dcc, html
import re

# цветовая тема
THEME = {
    'background': '#f2f2f2',    # фон всего дашборда
    'primary': '#1f77b4',       # синий для заголовков
    'text': '#2ca02c',          # зелёный для основного текста
    'border': '#1f77b4',        # синий для рамок
    'frame_bg': '#FFFFFF',      # фон панелей
    'link': '#4a4a4a'           # тёмно‑серый для ссылок
}

BASE_RAW = "https://raw.githubusercontent.com/annkaewstic/AdmisStudents/release/"
APPL_URL  = BASE_RAW + quote("Итоги приемной комиссии за 2024 год.csv")

PDF_FILES = [
    "Количество мест на обучение в 2024 году. Очная.pdf",
    "Количество мест на обучение в 2024 году. Очно-заочная.pdf",
    "Количество мест на обучение в 2024 году. заочная.pdf"
]
PDF_LINKS = [(name, BASE_RAW + quote(name)) for name in PDF_FILES]

# --- загрузка и подготовка данных ---
apps = pd.read_csv(APPL_URL, sep=',', encoding='utf-8')

# извлекаем аббревиатуры
apps['Fac_abbr']  = apps['Факультет'].str.extract(r'\((.*?)\)')
apps['Dept_abbr'] = apps['Кафедра'].str.extract(r'\((.*?)\)') 

# === 1.1 По формам обучения ===
form_counts = apps['Форма обучения'].value_counts().reset_index()
form_counts.columns = ['Форма обучения', 'Count']
total_form = form_counts['Count'].sum()
fig_apps_form = px.bar(
    form_counts, x='Форма обучения', y='Count',
    title="По формам обучения", text='Count',
    color_discrete_sequence=[THEME['primary'], THEME['text']],
    height=350
)
fig_apps_form.add_annotation(
    x=0.5, y=1.05, xref='paper', yref='paper',
    text=f"Всего возможных направлений: {total_form}",
    showarrow=False,
    font=dict(color=THEME['text'], size=14)
)
fig_apps_form.update_traces(textposition='inside')
fig_apps_form.update_layout(
    xaxis_title=None, yaxis_title="Направления",
    font=dict(color=THEME['primary']), title_font=dict(color=THEME['primary']),
    paper_bgcolor=THEME['frame_bg'], plot_bgcolor=THEME['frame_bg'],
    margin=dict(l=20, r=20, t=60, b=20)
)

# === 1.2 По бюджету/договору ===
fin_sums = pd.Series({
    'Бюджет': apps['Бюджет'].sum(),
    'Договор': apps['Договор'].sum()
}).reset_index()
fin_sums.columns = ['Основа финансирования', 'Count']
total_fin = fin_sums['Count'].sum()
fig_apps_fin = px.bar(
    fin_sums, x='Основа финансирования', y='Count',
    title="По бюджет/договор", text='Count',
    color_discrete_sequence=[THEME['text'], THEME['primary']],
    height=350
)
fig_apps_fin.add_annotation(
    x=0.5, y=1.05, xref='paper', yref='paper',
    text=f"Всего мест: {total_fin}",
    showarrow=False,
    font=dict(color=THEME['text'], size=14)
)
fig_apps_fin.update_traces(textposition='inside')
fig_apps_fin.update_layout(
    xaxis_title=None, yaxis_title="Количество",
    font=dict(color=THEME['primary']), title_font=dict(color=THEME['primary']),
    paper_bgcolor=THEME['frame_bg'], plot_bgcolor=THEME['frame_bg'],
    margin=dict(l=20, r=20, t=60, b=20)
)

# === 2.1 Stacked bar по направлениям ===
temp = apps.groupby(['Fac_abbr','Dept_abbr'])['Направление'] \
           .agg(list) \
           .reset_index(name='DirectionsList')

bar_df = apps.groupby(['Fac_abbr','Dept_abbr']) \
             .size() \
             .reset_index(name='Count')

bar_df = bar_df.merge(temp, on=['Fac_abbr','Dept_abbr'], how='left')
# превращаем списки в HTML-строки с нумерацией
def make_hover_list(lst):
    return '<br>'.join(f"{i+1}. {n}" for i,n in enumerate(lst))

bar_df['HoverList'] = bar_df['DirectionsList'].apply(make_hover_list)

# Считаем итоги
totals = bar_df.groupby('Fac_abbr')['Count']\
               .sum().reset_index(name='Directions')
total_dir = totals['Directions'].sum()
# серия go.Bar
fig_apps_dir = go.Figure()
faculties = bar_df['Fac_abbr'].unique()
for dept in bar_df['Dept_abbr'].unique():
    sub = bar_df[bar_df['Dept_abbr'] == dept]
    # для выравнивания по всем факультетам:
    y = [ sub[sub['Fac_abbr']==f]['Count'].iloc[0] if f in sub['Fac_abbr'].values else 0
          for f in faculties ]
    hover = [ sub[sub['Fac_abbr']==f]['HoverList'].iloc[0] if f in sub['Fac_abbr'].values else ''
              for f in faculties ]

    fig_apps_dir.add_trace(go.Bar(
        x=faculties,
        y=y,
        name=dept,
        marker_color=THEME['text'],
        text=y,
        textposition='inside',
        customdata=hover,
        hovertemplate=(
            'Факультет: %{x}<br>' +
            'Кафедра: ' + dept + '<br>' +
            'Направления:<br>%{customdata}<extra></extra>'
        )
    ))
# stacking и лэйаут
fig_apps_dir.update_layout(
    barmode='stack',
    title='Набор на направления<br>(по факультетам и кафедрам)',
    xaxis_title='Факультеты',
    yaxis_title='Количество направлений',
    xaxis=dict(tickangle=0),
    paper_bgcolor=THEME['frame_bg'],
    plot_bgcolor=THEME['frame_bg'],
    font=dict(color=THEME['primary']),
    title_font=dict(color=THEME['primary']),
    showlegend=False,
    margin=dict(l=20, r=20, t=100, b=20),
    height=550
)
# аннотации итогов по факультетам
for _, row in totals.iterrows():
    fig_apps_dir.add_annotation(
        x=row['Fac_abbr'],
        y=row['Directions'],
        text=str(row['Directions']),
        showarrow=False,
        yshift=8,
        font=dict(color=THEME['primary'], size=12)
    )
# аннотация
fig_apps_dir.add_annotation(
    x=0.5, y=1.12,
    xref='paper', yref='paper',
    text=f"Всего направлений: {total_dir}",
    showarrow=False,
    font=dict(color=THEME['text'], size=14)
)
fig_apps_dir.update_layout(
    title='Набор на направления<br>(по факультетам и кафедрам)',
    xaxis_title='Факультеты', yaxis_title='Количество направлений',
    xaxis=dict(tickangle=0),
    paper_bgcolor=THEME['frame_bg'], plot_bgcolor=THEME['frame_bg'],
    font=dict(color=THEME['primary']), title_font=dict(color=THEME['primary']),
    showlegend=False, margin=dict(l=20, r=20, t=100, b=20)
)

# === 3.2 Простая прокручиваемая таблица ===
# собираем базовый DF
detail_df = apps[['Направление','Форма обучения','Кафедра','Факультет','Бюджет','Договор']].copy()
# агрегируем бюджеты и договора по тем же группам, чтобы не дублировать строки
seats = (
    detail_df
    .groupby(['Направление','Форма обучения','Кафедра','Факультет'])[['Бюджет','Договор']]
    .sum()
    .reset_index()
)
# убираем лишние колонки из detail_df 
base = detail_df[['Направление','Форма обучения','Кафедра','Факультет']].drop_duplicates()

table_df = base.merge(seats, on=['Направление','Форма обучения','Кафедра','Факультет'], how='left')
# заголовок таблицы 
table_header = html.Thead(
    html.Tr([
        html.Th(col, style={
            'backgroundColor': THEME['border'],
            'color': 'white',
            'fontWeight': 'bold',
            'padding': '8px',
            'border': f'1px solid {THEME["border"]}'
        })
        for col in ['Направление','Форма обучения','Кафедра','Факультет','Места на бюджет','Места по договору']
    ])
)
# тело таблицы
table_rows = []
for _, r in table_df.iterrows():
    table_rows.append(html.Tr([
        html.Td(r['Направление'], style={'padding':'6px','border':f'1px solid {THEME["border"]}'}),
        html.Td(r['Форма обучения'], style={'padding':'6px','border':f'1px solid {THEME["border"]}'}),
        html.Td(r['Кафедра'],       style={'padding':'6px','border':f'1px solid {THEME["border"]}'}),
        html.Td(r['Факультет'],     style={'padding':'6px','border':f'1px solid {THEME["border"]}'}),
        html.Td(r['Бюджет'],        style={'padding':'6px','border':f'1px solid {THEME["border"]}'}),
        html.Td(r['Договор'],       style={'padding':'6px','border':f'1px solid {THEME["border"]}'})
    ]))

table_body = html.Tbody(table_rows)
detail_table = html.Div(
    style={'maxHeight':'450px','overflowY':'auto','marginTop':'10px'},
    children=html.Table(
        [table_header, table_body],
        style={'width':'100%','borderCollapse':'collapse'},
        className='detail-table'
    )
)

# === 4) Pie chart ===
labels = fin_sums['Основа финансирования']
values = fin_sums['Count']
pie_fig = go.Figure()
pie_fig.add_trace(go.Pie(
    labels=labels, values=values, hole=0.4,
    textinfo='label+value', textposition='outside',
    textfont=dict(color=THEME['text'], size=14),
    marker=dict(colors=[THEME['primary'], THEME['text']]),
    pull=[0.05,0.05], hovertemplate='%{label}<br>%{value}<extra></extra>',
    sort=False, direction='clockwise', showlegend=False,
    domain={'x':[0,1],'y':[0,1]}
))
pie_fig.add_trace(go.Pie(
    labels=labels, values=values, hole=0.5,
    textinfo='percent', textposition='inside',
    insidetextfont=dict(color='white', size=14),
    marker=dict(colors=['rgba(0,0,0,0)']*len(values)),
    hoverinfo='skip', sort=False, direction='clockwise',
    showlegend=False, domain={'x':[0,1],'y':[0,1]}
))
pie_fig.update_layout(
    title=dict(text='Абитуриенты, поступившие на бюджет/по договору',
               font=dict(color=THEME['primary'],size=16), pad=dict(t=20,b=10)),
    paper_bgcolor=THEME['frame_bg'], plot_bgcolor=THEME['frame_bg'],
    margin=dict(l=20,r=20,t=100,b=20), height=400
)

# === Dash-приложение ===
app = Dash(__name__)
app.index_string = f'''
<!DOCTYPE html>
<html>
  <head>{{%metas%}}<title>{{%title%}}</title>{{%favicon%}}{{%css%}}
    <style>
      body {{background:{THEME['background']};margin:0;}}
      .pdf-link {{display:block;font-size:18px;color:{THEME['link']};margin-bottom:8px;text-decoration:none;}}
      .pdf-link:hover {{text-decoration:underline;}}
      .graph-frame {{border:2px solid {THEME['border']};border-radius:4px;background:{THEME['frame_bg']};padding:10px;}}
      .detail-table {{
        width: 100%;
        border-collapse: collapse;
        background-color: white;            /* белый фон */
      }}
      .detail-table th,
      .detail-table td {{
        border: 1px solid {THEME['border']};  /* границы как у графиков */
        padding: 6px;
      }}
      .detail-table th {{
        background-color: {THEME['border']};  /* синяя шапка */
        color: white;
        font-weight: bold;
      }}
    </style>
  </head>
  <body>{{%app_entry%}}<footer>{{%config%}}{{%scripts%}}{{%renderer%}}</footer></body>
</html>
'''
app.layout = html.Div(style={'padding':'20px','backgroundColor':THEME['background']}, children=[

    html.H1('Работа приемной комиссии',
            style={'textAlign':'center','color':THEME['primary'],'fontSize':'48px','marginBottom':'5px'}),
    html.P('Результаты работы приемной комиссии за 2024 год',
           style={'textAlign':'center','color':THEME['text'],'fontStyle':'italic','fontSize':'20px','marginBottom':'20px'}),
    html.Div([html.A(name,href=url,target='_blank',className='pdf-link') for name,url in PDF_LINKS],
             style={'textAlign':'center','marginBottom':'40px'}),

    html.P("Количество заявлений (набор по направлениям):",
           style={'textAlign':'center','color':THEME['primary'],'fontSize':'25px','marginBottom':'5px'}),

    html.Div(style={'display':'grid','gridTemplateColumns':'1fr 1fr','gap':'20px','maxWidth':'1200px','margin':'auto'},
             children=[
                 html.Div(dcc.Graph(figure=fig_apps_form),className='graph-frame'),
                 html.Div(dcc.Graph(figure=fig_apps_fin), className='graph-frame'),
             ]),

    html.Div(style={'display':'grid','gridTemplateColumns':'1fr','gap':'20px','maxWidth':'1200px','margin':'auto','marginTop':'20px'},
             children=[
                 html.Div(dcc.Graph(figure=fig_apps_dir), className='graph-frame'),
                 detail_table
             ]),

    html.Div(style={'display':'flex','justifyContent':'center','marginTop':'30px'},
             children=html.Div(dcc.Graph(figure=pie_fig),className='graph-frame',style={'width':'60%'})),

    html.P(f'Всего абитуриентов в 2024 году: {total_fin}',
           style={'textAlign':'center','color':THEME['text'],'fontWeight':'bold','marginTop':'40px'})

])

if __name__ == '__main__':
    app.run(debug=True)
