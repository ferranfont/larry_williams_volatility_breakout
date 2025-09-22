import os
import webbrowser
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots

def plot_close_and_volume(symbol, timeframe, df):
    html_path = f'charts/close_vol_chart_{symbol}_{timeframe}.html'
    os.makedirs(os.path.dirname(html_path), exist_ok=True)

    df = df.rename(columns=str.lower)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.80, 0.20],
        vertical_spacing=0.03,
    )

    # Traza de precio (línea de cierre)
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['close'],
        mode='lines',
        line=dict(color='blue', width=1.5),
        name='Close'
    ), row=1, col=1)

    # Añadir puntos naranjas solo para días de volatilidad media-baja (upto_60)
    if 'day_type' in df.columns:
        max_vol_days = df[df['day_type'] == 'upto_60']
        if len(max_vol_days) > 0:
            fig.add_trace(go.Scatter(
                x=max_vol_days['date'],
                y=max_vol_days['close'],
                mode='markers',
                marker=dict(
                    color='orange',
                    size=6,
                    opacity=0.8,
                    symbol='circle'
                ),
                name='Maximum Volatility Days (100+ pts)',
                hovertemplate='<b>Max Vol Day</b><br>' +
                              'Date: %{x}<br>' +
                              'Close: %{y}<br>' +
                              'Range: 100+ points<br>' +
                              '<extra></extra>'
            ), row=1, col=1)

    # Barras de volumen
    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['volume'],
        marker_color='royalblue',
        marker_line_color='blue',
        marker_line_width=0.4,
        opacity=0.95,
        name='Volumen'
    ), row=2, col=1)

    fig.update_layout(
        dragmode='pan',
        title=f'{symbol}_{timeframe}',
        width=1500,
        height=700,
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(size=12, color="black"),
        plot_bgcolor='rgba(255,255,255,0.05)',
        paper_bgcolor='rgba(240,240,240,0.1)',
        showlegend=True,
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(0,0,0,0.2)',
            borderwidth=1
        ),
        template='plotly_white',
        xaxis=dict(
            type='date',
            tickformat="%b %d<br>%Y",
            tickangle=0,
            showgrid=False,
            linecolor='gray',
            linewidth=1,
            range=[df['date'].min(), df['date'].max()]
        ),
        yaxis=dict(showgrid=True, linecolor='gray', linewidth=1),
        xaxis2=dict(
            type='date',
            tickformat="%b %d<br>%Y",
            tickangle=45,
            showgrid=False,
            linecolor='gray',
            linewidth=1,
            range=[df['date'].min(), df['date'].max()]
        ),
        yaxis2=dict(showgrid=True, linecolor='grey', linewidth=1),
        # shapes=shapes
    )

    fig.write_html(html_path, config={"scrollZoom": True})
    print(f"✅ Gráfico Plotly guardado como HTML: '{html_path}'")

    webbrowser.open('file://' + os.path.realpath(html_path))
