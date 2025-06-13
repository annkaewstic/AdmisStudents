import pandas as pd
import plotly.express as px
from urllib.parse import quote
from dash import Dash, dcc, html
from dash import dash_table

# Цветовая тема
THEME = {
    'background': '#fff7e6',
    'primary': '#e67e22',
    'secondary': '#f39c12',
    'accent1': '#f1c40f',
    'accent2': '#f8c471',
    'text': '#5d4037'
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

# Загрузка данных
df = pd.read_csv(CSV_URL, sep=';', encoding='cp1251')
df.columns = [c.strip() for c in df.columns]
total_students = len(df)

# Treemap: квадратный, крупный шрифт с переносом
treemap_fig = px.treemap(
    df,
    path=['Факультет', 'Кафедра'],
    color='Факультет',
    color_discrete_sequence=[
        THEME['primary'], THEME['secondary'],
        THEME['accent1'], THEME['accent2']
    ],
    title="Структура контингента: факультеты и кафедры"
)
treemap_fig.update_traces(
    branchvalues="total",
    textinfo="label+value",
    textfont=dict(size=18),
    tiling=dict(pad=5)
)
treemap_fig.update_layout(
    width=900, height=900,
    margin=dict(t=50, l=30, r=30, b=30),
    paper_bgcolor=THEME['background'],
    plot_bgcolor=THEME['background']
)

# Stacked bar
bar_fig = px.bar(
    df.groupby(['Факультет','Кафедра']).size().reset_index(name='Students'),
    x='Факультет', y='Students', color='Кафедра', barmode='stack',
    color_discrete_sequence=[
        THEME['accent1'], THEME['accent2'],
        THEME['primary'], THEME['secondary']
    ],
    title="Количество студентов по факультетам и кафедрам"
)
bar_fig.update_layout(
    paper_bgcolor=THEME['background'],
    plot_bgcolor=THEME['background']
)

# Pie chart
status_df = (
    df['Статус']
      .value_counts()
      .rename_axis('Status')
      .reset_index(name='Count')
)

pie_fig = px.pie(
    status_df,
    names='Status',
    values='Count',
    color='Status',  # без этого sequence не сработает
    color_discrete_sequence=[THEME['primary'], THEME['accent1']],
    title="Процент студентов: обучающихся и в академическом отпуске",
    template=None      # чтобы не подмешивалась тема plotly по умолчанию
)
pie_fig.update_layout(
    paper_bgcolor=THEME['background'],
    plot_bgcolor=THEME['background']
)

app = Dash(__name__)

# Встраиваем CSS в шаблон
app.index_string = f'''
<!DOCTYPE html>
<html>
  <head>
    {{%metas%}}
    <title>{{%title%}}</title>
    {{%favicon%}}
    {{%css%}}
    <style>
      body {{ background: {THEME['background']}; }}
      .pdf-link {{
        display: block;
        font-size: 24px;
        color: {THEME['secondary']};
        margin-bottom: 16px;
        text-decoration: none;
      }}
      .pdf-link:hover {{
        text-decoration: underline;
      }}
      .dash-graph {{
        margin: 40px auto !important;
      }}
      .data-table-cell {{
        white-space: normal !important;
        height: auto !important;
        font-size: 16px;
        padding: 8px;
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

        html.H1(
            "Admission Dashboard",
            style={
                'textAlign': 'center',
                'color': THEME['primary'],
                'fontSize': '48px',
                'marginBottom': '10px'
            }
        ),

        html.P(
            "Контингент студентов за июнь 2025",
            style={
                'textAlign': 'center',
                'color': THEME['text'],
                'fontStyle': 'italic',
                'fontSize': '24px',
                'marginBottom': '40px'
            }
        ),

        html.Div(style={'height': '80px'}),

        html.Div([
            html.A(name, href=url, target="_blank", className='pdf-link')
            for name, url in PDF_LINKS
        ], style={'maxWidth': '800px', 'margin': 'auto', 'marginBottom': '60px'}),

        html.Div(dcc.Graph(figure=treemap_fig), style={'display': 'flex', 'justifyContent': 'center'}),

        html.Div(dcc.Graph(figure=bar_fig), className='dash-graph'),

        html.Div(dcc.Graph(figure=pie_fig), className='dash-graph'),

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
