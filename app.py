import pandas as pd
import plotly.express as px
from urllib.parse import quote
from dash import Dash, dcc, html, dash_table

# Расширенная цветовая тема
THEME = {
    'background': '#f2f2f2',    # фон всего дашборда
    'primary': '#1f77b4',       # синий для заголовков
    'text': '#2ca02c',          # зелёный для основного текста
    'border': '#1f77b4',        # синий для рамок
    'frame_bg': '#FFFFFF',      # фон панелей
    'link': '#4a4a4a'           # тёмно‑серый для ссылок
}

BASE_RAW = "https://raw.githubusercontent.com/annkaewstic/AdmisStudents/release/"
CSV_NAME = "Список студентов для расчета контингента на 06.2025.csv"
CSV_URL = BASE_RAW + quote(CSV_NAME)

PDF_FILES = [
    "Количество зачисленных на обучение в 2024 году. Очная.pdf",
    "Количество зачисленных на обучение в 2024 году. Очно-заочная.pdf",
    "Количество зачисленных на обучение в 2024 году. заочная.pdf"
]
PDF_LINKS = [(name, BASE_RAW + quote(name)) for name in PDF_FILES]

# Загрузка и подготовка данных
df = pd.read_csv(CSV_URL, sep=';', encoding='cp1251')
df.columns = [c.strip() for c in df.columns]
total_students = len(df)

# 1) Treemap
treemap_fig = px.treemap(
    df,
    path=['Факультет','Кафедра'],
    color='Факультет',
    color_discrete_sequence=[THEME['primary'], THEME['border'], THEME['text']],
    title="Структура контингента: факультеты и кафедры"
)
treemap_fig.update_layout(
    paper_bgcolor=THEME['frame_bg'],
    plot_bgcolor=THEME['frame_bg'],
    font=dict(color=THEME['text']),
    title_font=dict(color=THEME['primary'])
)

# 2) Stacked bar
bar_fig = px.bar(
    df.groupby(['Факультет','Кафедра']).size().reset_index(name='Students'),
    x='Факультет', y='Students', color='Кафедра', barmode='stack',
    color_discrete_sequence=[THEME['text'], THEME['border'], THEME['primary']]
)
bar_fig.update_layout(
    title="Количество студентов по факультетам и кафедрам",
    paper_bgcolor=THEME['frame_bg'],
    plot_bgcolor=THEME['frame_bg'],
    font=dict(color=THEME['text']),
    title_font=dict(color=THEME['primary'])
)

# 3) Pie chart
status_df = df['Статус'].value_counts().rename_axis('Status').reset_index(name='Count')
pie_fig = px.pie(
    status_df, names='Status', values='Count',
    color_discrete_sequence=[THEME['primary'], THEME['text']],
    title="Процент студентов: обучающихся и в академическом отпуске"
)
pie_fig.update_layout(
    paper_bgcolor=THEME['frame_bg'],
    plot_bgcolor=THEME['frame_bg'],
    font=dict(color=THEME['text']),
    title_font=dict(color=THEME['primary'])
)

# --- Dash-приложение ---
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
      .pdf-link {{
        display: block;
        font-size: 18px;
        color: {THEME['link']};
        margin-bottom: 8px;
        text-decoration: none;
      }}
      .pdf-link:hover {{ text-decoration: underline; }}
      .graph-frame {{
        border: 2px solid {THEME['border']};
        border-radius: 4px;
        background: {THEME['frame_bg']};
        padding: 10px;
      }}
    </style>
  </head>
  <body>
    {{%app_entry%}}
    <footer>
      {{%config%}}
      {{%scripts%}}
      {{%renderer%}}
    </footer>
  </body>
</html>
'''

app.layout = html.Div(
    style={'padding': '20px', 'backgroundColor': THEME['background']},
    children=[

        # Заголовок
        html.H1(
            "Admission Dashboard",
            style={
                'textAlign': 'center',
                'color': THEME['primary'],
                'fontSize': '48px',
                'marginBottom': '5px'
            }
        ),
        html.P(
            "Контингент студентов за июнь 2025",
            style={
                'textAlign': 'center',
                'color': THEME['text'],
                'fontStyle': 'italic',
                'fontSize': '20px',
                'marginBottom': '20px'
            }
        ),

        # Ссылки
        html.Div([
            html.A(name, href=url, target="_blank", className='pdf-link')
            for name, url in PDF_LINKS
        ], style={'textAlign': 'center', 'marginBottom': '40px'}),

        # Первая строка — 2 графика
        html.Div(
            style={
                'display': 'grid',
                'gridTemplateColumns': '1fr 1fr',
                'gap': '20px',
                'maxWidth': '1200px',
                'margin': 'auto'
            },
            children=[
                html.Div(dcc.Graph(figure=treemap_fig), className='graph-frame'),
                html.Div(dcc.Graph(figure=bar_fig),     className='graph-frame'),
            ]
        ),

        # Вторая строка — одна диаграмма по центру
        html.Div(
            style={'display': 'flex', 'justifyContent': 'center', 'marginTop': '30px'},
            children=html.Div(dcc.Graph(figure=pie_fig), className='graph-frame', style={'width': '60%'})
        ),

        # Итоговый текст
        html.P(
            f"Всего студентов в 2025 году: {total_students}",
            style={
                'textAlign': 'center',
                'color': THEME['text'],
                'fontWeight': 'bold',
                'marginTop': '40px'
            }
        )
    ]
)

if __name__ == '__main__':
    app.run(debug=True)
