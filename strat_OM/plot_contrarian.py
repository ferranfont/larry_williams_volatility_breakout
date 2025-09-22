import os
import webbrowser
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import numpy as np

def plot_contrarian_results(trades_df, market_data, metrics):
    """
    Genera gráfico interactivo con resultados del sistema contrarian

    Parameters:
    trades_df (DataFrame): DataFrame con trades ejecutados
    market_data (DataFrame): DataFrame con datos del mercado
    metrics (dict): Métricas de rendimiento del sistema
    """

    # Crear directorio de charts si no existe
    charts_dir = 'charts'
    os.makedirs(charts_dir, exist_ok=True)

    # Preparar datos
    market_data = market_data.copy()
    market_data['date'] = pd.to_datetime(market_data['date'])
    market_data = market_data.sort_values('date')

    trades_df = trades_df.copy()
    trades_df['date'] = pd.to_datetime(trades_df['date'])

    # Crear subplot con 3 filas
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.50, 0.25, 0.25],
        vertical_spacing=0.05,
        subplot_titles=[
            'Precio y Señales de Trading Contrarian',
            'Curva de Equity (PnL Acumulado)',
            'Distribución de PnL por Trade'
        ]
    )

    # 1. GRÁFICO PRINCIPAL: Precio con señales de trading
    fig.add_trace(go.Scatter(
        x=market_data['date'],
        y=market_data['close'],
        mode='lines',
        line=dict(color='blue', width=1.5),
        name='Close Price',
        hovertemplate='Fecha: %{x}<br>Precio: %{y:.2f}<extra></extra>'
    ), row=1, col=1)

    # Añadir puntos de entrada BUY (verde)
    buy_trades = trades_df[trades_df['entry_type'] == 'BUY']
    if len(buy_trades) > 0:
        fig.add_trace(go.Scatter(
            x=buy_trades['date'],
            y=buy_trades['entry_price'],
            mode='markers',
            marker=dict(
                color='green',
                size=10,
                symbol='triangle-up',
                line=dict(color='darkgreen', width=2)
            ),
            name='BUY Entry',
            hovertemplate='BUY<br>Fecha: %{x}<br>Precio: %{y:.2f}<extra></extra>'
        ), row=1, col=1)

    # Añadir puntos de entrada SELL (rojo)
    sell_trades = trades_df[trades_df['entry_type'] == 'SELL']
    if len(sell_trades) > 0:
        fig.add_trace(go.Scatter(
            x=sell_trades['date'],
            y=sell_trades['entry_price'],
            mode='markers',
            marker=dict(
                color='red',
                size=10,
                symbol='triangle-down',
                line=dict(color='darkred', width=2)
            ),
            name='SELL Entry',
            hovertemplate='SELL<br>Fecha: %{x}<br>Precio: %{y:.2f}<extra></extra>'
        ), row=1, col=1)

    # Añadir puntos naranjas pequeños en entry_price
    if 'entry_time' in trades_df.columns:
        entry_x = trades_df['entry_time']
    else:
        entry_x = trades_df['date']

    fig.add_trace(go.Scatter(
        x=entry_x,
        y=trades_df['entry_price'],
        mode='markers',
        marker=dict(
            color='orange',
            size=4,
            symbol='circle',
            line=dict(color='darkorange', width=1)
        ),
        name='Entry Price',
        hovertemplate='Entry Price<br>Fecha: %{x}<br>Precio: %{y:.2f}<extra></extra>'
    ), row=1, col=1)

    # Añadir puntos de salida (cuadrados negros)
    if 'exit_time' in trades_df.columns:
        exit_x = trades_df['exit_time']
    else:
        exit_x = trades_df['date']

    fig.add_trace(go.Scatter(
        x=exit_x,
        y=trades_df['exit_price'],
        mode='markers',
        marker=dict(
            color='black',
            size=8,
            symbol='square',
            line=dict(color='black', width=2)
        ),
        name='Exit Points',
        hovertemplate='Exit<br>Fecha: %{x}<br>Precio: %{y:.2f}<br>Razón: %{customdata}<extra></extra>',
        customdata=trades_df['exit_reason']
    ), row=1, col=1)

    # Añadir líneas grises punteadas conectando entrada y salida
    for idx, trade in trades_df.iterrows():
        entry_x = trade.get('entry_time', trade['date'])
        exit_x_val = trade.get('exit_time', trade['date'])

        fig.add_trace(go.Scatter(
            x=[entry_x, exit_x_val],
            y=[trade['entry_price'], trade['exit_price']],
            mode='lines',
            line=dict(
                color='grey',
                width=1,
                dash='dash'
            ),
            opacity=0.5,
            showlegend=False,
            hoverinfo='skip'
        ), row=1, col=1)

    # 2. CURVA DE EQUITY
    if len(trades_df) > 0:
        cumulative_pnl = trades_df['pnl'].cumsum()

        # Crear serie temporal para curva de equity
        equity_dates = trades_df['date'].tolist()
        equity_values = cumulative_pnl.tolist()

        # Añadir punto inicial en 0
        if len(equity_dates) > 0:
            start_date = equity_dates[0] - pd.Timedelta(days=1)
            equity_dates.insert(0, start_date)
            equity_values.insert(0, 0)

        fig.add_trace(go.Scatter(
            x=equity_dates,
            y=equity_values,
            mode='lines',
            line=dict(color='green', width=2),
            fill='tonexty',
            fillcolor='rgba(0,255,0,0.1)',
            name='Equity Curve',
            hovertemplate='Fecha: %{x}<br>PnL Acumulado: %{y:.2f}<extra></extra>'
        ), row=2, col=1)

        # Línea horizontal en 0
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, row=2, col=1)

    # 3. DISTRIBUCIÓN DE PnL
    if len(trades_df) > 0:
        fig.add_trace(go.Histogram(
            x=trades_df['pnl'],
            nbinsx=30,
            marker_color='lightblue',
            marker_line_color='blue',
            marker_line_width=1,
            name='PnL Distribution',
            hovertemplate='PnL Range: %{x}<br>Frequency: %{y}<extra></extra>'
        ), row=3, col=1)

        # Línea vertical en 0
        fig.add_vline(x=0, line_dash="dash", line_color="red", opacity=0.7, row=3, col=1)

    # Configurar layout
    fig.update_layout(
        title=dict(
            text=f'<b>Sistema Contrarian Volatility - Resultados</b><br>' +
                 f'<span style="font-size:14px">Trades: {metrics.get("total_trades", 0)} | ' +
                 f'Win Rate: {metrics.get("win_rate", 0):.1f}% | ' +
                 f'PnL Total: {metrics.get("total_pnl", 0):.2f} pts | ' +
                 f'Profit Factor: {metrics.get("profit_factor", 0):.2f}</span>',
            x=0.5
        ),
        width=1400,
        height=1000,
        template='plotly_white',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    # Configurar ejes
    fig.update_xaxes(title_text="Fecha", row=3, col=1)
    fig.update_yaxes(title_text="Precio", row=1, col=1)
    fig.update_yaxes(title_text="PnL Acumulado", row=2, col=1)
    fig.update_yaxes(title_text="Frecuencia", row=3, col=1)

    # Añadir tabla de métricas como anotación
    metrics_text = f"""
<b>Métricas del Sistema:</b><br>
• Total Trades: {metrics.get('total_trades', 0)}<br>
• Trades Ganadores: {metrics.get('winning_trades', 0)}<br>
• Trades Perdedores: {metrics.get('losing_trades', 0)}<br>
• Win Rate: {metrics.get('win_rate', 0):.2f}%<br>
• PnL Total: {metrics.get('total_pnl', 0):.2f} pts<br>
• Ganancia Promedio: {metrics.get('avg_win', 0):.2f} pts<br>
• Pérdida Promedio: {metrics.get('avg_loss', 0):.2f} pts<br>
• Profit Factor: {metrics.get('profit_factor', 0):.2f}<br>
• Max Drawdown: {metrics.get('max_drawdown', 0):.2f} pts
"""

    fig.add_annotation(
        x=0.02, y=0.98,
        xref="paper", yref="paper",
        text=metrics_text,
        showarrow=False,
        font=dict(size=11, color="black"),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="rgba(0,0,0,0.3)",
        borderwidth=1,
        align="left",
        valign="top"
    )

    # Guardar y abrir gráfico
    html_path = f'{charts_dir}/contrarian_volatility_results.html'
    fig.write_html(html_path, config={"scrollZoom": True})

    print(f"Gráfico guardado en: {html_path}")

    # Abrir en navegador
    full_path = os.path.abspath(html_path)
    webbrowser.open(f'file://{full_path}')

    return fig

def create_performance_summary_chart(trades_df, metrics):
    """
    Crea gráfico adicional con resumen de rendimiento mensual

    Parameters:
    trades_df (DataFrame): DataFrame con trades
    metrics (dict): Métricas de rendimiento
    """
    if len(trades_df) == 0:
        print("No hay trades para generar resumen mensual")
        return

    # Agregar por mes
    trades_df = trades_df.copy()
    trades_df['date'] = pd.to_datetime(trades_df['date'])
    trades_df['year_month'] = trades_df['date'].dt.to_period('M')

    monthly_pnl = trades_df.groupby('year_month')['pnl'].agg(['sum', 'count']).reset_index()
    monthly_pnl['year_month_str'] = monthly_pnl['year_month'].astype(str)

    # Crear gráfico de barras mensual
    fig = go.Figure()

    colors = ['green' if pnl >= 0 else 'red' for pnl in monthly_pnl['sum']]

    fig.add_trace(go.Bar(
        x=monthly_pnl['year_month_str'],
        y=monthly_pnl['sum'],
        marker_color=colors,
        name='PnL Mensual',
        hovertemplate='Mes: %{x}<br>PnL: %{y:.2f}<br>Trades: %{customdata}<extra></extra>',
        customdata=monthly_pnl['count']
    ))

    fig.update_layout(
        title='Rendimiento Mensual - Sistema Contrarian Volatility',
        xaxis_title='Mes',
        yaxis_title='PnL (puntos)',
        template='plotly_white',
        width=1200,
        height=500
    )

    # Línea horizontal en 0
    fig.add_hline(y=0, line_dash="dash", line_color="gray")

    # Guardar
    charts_dir = 'charts'
    html_path = f'{charts_dir}/contrarian_monthly_performance.html'
    fig.write_html(html_path)
    print(f"Gráfico mensual guardado en: {html_path}")

    return fig