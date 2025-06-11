import pandas as pd
import plotly.express as px

from dash import Dash, dcc, html
from dash.dependencies import Input, Output

# Цветовая тема: оттенки оранжевого и жёлтого
THEME = {
    'background': '#fff7e6',
    'primary': '#e67e22',  # насыщенный оранжевый
    'secondary': '#f39c12',  # тёмно-жёлтый
    'accent1': '#f1c40f',  # ярко-жёлтый
    'accent2': '#f8c471',  # светло-оранжевый
    'text': '#5d4037'  # тёмно-коричневый для текста
}

# Ссылка на raw-CSV из ветки release
CSV_URL = (
    "https://raw.githubusercontent.com/"
    "annkaewstic/AdmisStudents/release/"
    "Список%20студентов%20для%20расчета%20контингента%20на%2006.2025.csv"
)

app = Dash(__name__, suppress_callback_exceptions=True)

app.layout = html.Div(
    style={'backgroundColor': THEME['background'], 'minHeight': '100vh', 'padding': '20px'},
    children=[
        html.H1("Admission Dashboard", style={'textAlign': 'center', 'color': THEME['primary']}),
        html.P("Нажать для показа анализа контингента студентов 2025 года",
               style={'textAlign': 'center', 'color': THEME['text'], 'fontStyle': 'italic'}),
        html.Div(html.Button("Показать анализ", id="show-analysis", n_clicks=0,
                             style={'backgroundColor': THEME['secondary'], 'color': 'white',
                                    'padding': '10px 20px', 'border': 'none', 'borderRadius': '5px',
                                    'fontSize': '18px', 'cursor': 'pointer'}), style={'textAlign': 'center'}),
        html.Div(id="dashboard-content", style={'marginTop': '40px'})
    ]
)

@app.callback(
    Output("dashboard-content", "children"),
    Input("show-analysis", "n_clicks")
)
def render_dashboard(n):
    if not n:
        return html.P("Ожидание запуска...", style={'textAlign': 'center', 'color': THEME['text']})

    # Загрузка данных
    df = pd.read_csv(CSV_URL)
    # Переименовать столбцы в английские, если нужно
    df.columns = [c.strip() for c in df.columns]

    # Первый график: иерархия факультетов и кафедр
    sunburst = px.sunburst(
        df, path=['Faculty', 'Department'], values=None,
        color='Faculty', color_discrete_sequence=[
            THEME['primary'], THEME['secondary'], THEME['accent1'], THEME['accent2']
        ],
        title="Структура контингента: факультеты и кафедры"
    )
    sunburst.update_traces(branchvalues="total")

    # Второй график: столбчатая диаграмма с факультетами и кафедрами
    counts = df.groupby(['Faculty', 'Department']).size().reset_index(name='Students')
    bar = px.bar(
        counts, x='Faculty', y='Students', color='Department', barmode='stack',
        color_discrete_sequence=[
            THEME['accent1'], THEME['accent2'], THEME['primary'], THEME['secondary']
        ],
        title="Количество студентов по факультетам и кафедрам"
    )

    # Третий график: процент обучающихся и в академическом отпуске
    status_counts = df['Status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    pie = px.pie(
        status_counts, names='Status', values='Count',
        color='Status',
        color_discrete_map={
            'Active': THEME['primary'],
            'On Leave': THEME['secondary']
        },
        title="Процент студентов: обучающихся и в академическом отпуске"
    )

    return html.Div([
        dcc.Graph(figure=sunburst),
        dcc.Graph(figure=bar),
        dcc.Graph(figure=pie)
    ], style={'maxWidth': '1200px', 'margin': 'auto'})


if __name__ == "__main__":
    app.run(debug=True)
