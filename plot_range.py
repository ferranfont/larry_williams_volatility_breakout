import plotly.graph_objects as go
import plotly.offline as pyo
import pandas as pd

def plot_range_chart(symbol, timeframe, df):
    """
    Crea un gráfico interactivo con Plotly mostrando el range en rojo

    Parameters:
    symbol (str): Símbolo del instrumento
    timeframe (str): Timeframe de los datos
    df (DataFrame): DataFrame con columnas 'date' y 'range'
    """

    # Crear figura
    fig = go.Figure()

    # Añadir línea del range en rojo
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['range'],
        mode='lines',
        name='Range',
        line=dict(color='red', width=2),
        hovertemplate='<b>Date:</b> %{x}<br>' +
                      '<b>Range:</b> %{y:.2f}<br>' +
                      '<extra></extra>'
    ))

    # Configurar layout
    fig.update_layout(
        title=f'{symbol} - Range Chart ({timeframe})',
        title_x=0.5,
        xaxis_title='Date',
        yaxis_title='Range',
        template='plotly_white',
        width=1200,
        height=600,
        showlegend=True,
        hovermode='x unified'
    )

    # Configurar ejes
    fig.update_xaxes(
        rangeslider_visible=True,
        type='date'
    )

    fig.update_yaxes(
        title_standoff=25
    )

    # Mostrar gráfico en navegador
    pyo.plot(fig, filename=f'charts/{symbol}_range_{timeframe}.html', auto_open=True)

    print(f"Gráfico de range guardado en: charts/{symbol}_range_{timeframe}.html")

if __name__ == "__main__":
    print("Range plot module loaded successfully")
    print("Available functions:")
    print("- plot_range_chart(symbol, timeframe, df)")