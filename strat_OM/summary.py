import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
import webbrowser
from datetime import datetime

# ============================================================
# CONFIGURACIÓN: Especificar archivo a analizar (o None para el más reciente)
# ============================================================


target_filename = 'tracking_record_20240815_20250413.csv'  # Cambiar por nombre específico: 'tracking_record_20200815_20230313.csv'


def load_tracking_data(filename=None):
    """
    Carga los datos del tracking record

    Parameters:
    filename (str): Nombre del archivo de tracking (opcional)

    Returns:
    DataFrame: Datos de trading cargados
    """
    if filename is None:
        # Buscar el archivo más reciente de tracking
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        data_dir = os.path.join(parent_dir, 'data')

        tracking_files = [f for f in os.listdir(data_dir) if f.startswith('tracking_record_')]
        if not tracking_files:
            raise FileNotFoundError("No se encontraron archivos de tracking record")

        # Usar el más reciente
        filename = sorted(tracking_files)[-1]

    # Cargar datos
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    data_dir = os.path.join(parent_dir, 'data')
    file_path = os.path.join(data_dir, filename)

    print(f"Cargando datos desde: {file_path}")

    df = pd.read_csv(file_path)
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df['exit_time'] = pd.to_datetime(df['exit_time'])
    df['date'] = pd.to_datetime(df['date'])

    return df, filename

def calculate_basic_stats(df):
    """
    Calcula estadísticas básicas de la estrategia

    Parameters:
    df (DataFrame): Datos de trading

    Returns:
    dict: Diccionario con estadísticas básicas
    """
    total_trades = len(df)
    winning_trades = len(df[df['profit_label'] == 'PROFIT'])
    losing_trades = len(df[df['profit_label'] == 'LOSS'])

    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

    total_profit_usd = df['profit_usd'].sum()
    avg_trade_profit = df['profit_usd'].mean()

    # Separar ganancias y pérdidas
    profits = df[df['profit_label'] == 'PROFIT']['profit_usd']
    losses = df[df['profit_label'] == 'LOSS']['profit_usd']

    avg_winning_trade = profits.mean() if len(profits) > 0 else 0
    avg_losing_trade = losses.mean() if len(losses) > 0 else 0

    # Profit Factor = Gross Profit / Gross Loss
    gross_profit = profits.sum() if len(profits) > 0 else 0
    gross_loss = abs(losses.sum()) if len(losses) > 0 else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

    # Tiempo en mercado
    avg_time_in_market = df['time_in_market_minutes'].mean()

    # Máxima ganancia y pérdida
    max_profit = df['profit_usd'].max()
    max_loss = df['profit_usd'].min()

    # Racha ganadora y perdedora
    df_sorted = df.sort_values('entry_time')
    profit_labels = df_sorted['profit_label'].values

    max_winning_streak, max_losing_streak = calculate_streaks(profit_labels)

    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': win_rate,
        'total_profit_usd': total_profit_usd,
        'avg_trade_profit': avg_trade_profit,
        'avg_winning_trade': avg_winning_trade,
        'avg_losing_trade': avg_losing_trade,
        'profit_factor': profit_factor,
        'gross_profit': gross_profit,
        'gross_loss': gross_loss,
        'avg_time_in_market': avg_time_in_market,
        'max_profit': max_profit,
        'max_loss': max_loss,
        'max_winning_streak': max_winning_streak,
        'max_losing_streak': max_losing_streak
    }

def calculate_streaks(profit_labels):
    """
    Calcula las rachas máximas de ganancias y pérdidas
    """
    if len(profit_labels) == 0:
        return 0, 0

    max_winning_streak = 0
    max_losing_streak = 0
    current_winning_streak = 0
    current_losing_streak = 0

    for label in profit_labels:
        if label == 'PROFIT':
            current_winning_streak += 1
            current_losing_streak = 0
            max_winning_streak = max(max_winning_streak, current_winning_streak)
        else:
            current_losing_streak += 1
            current_winning_streak = 0
            max_losing_streak = max(max_losing_streak, current_losing_streak)

    return max_winning_streak, max_losing_streak

def calculate_drawdown_stats(equity_curve):
    """
    Calcula estadísticas de drawdown

    Parameters:
    equity_curve (Series): Curva de equity acumulada

    Returns:
    dict: Estadísticas de drawdown
    """
    # Calcular peak (máximo acumulado)
    peak = equity_curve.cummax()

    # Calcular drawdown
    drawdown = equity_curve - peak
    drawdown_pct = (drawdown / peak) * 100

    # Máximo drawdown
    max_drawdown = drawdown.min()
    max_drawdown_pct = drawdown_pct.min()

    # Duración del drawdown
    in_drawdown = drawdown < 0
    drawdown_periods = []

    if in_drawdown.any():
        start_dd = None
        for i, is_dd in enumerate(in_drawdown):
            if is_dd and start_dd is None:
                start_dd = i
            elif not is_dd and start_dd is not None:
                drawdown_periods.append(i - start_dd)
                start_dd = None

        # Si termina en drawdown
        if start_dd is not None:
            drawdown_periods.append(len(in_drawdown) - start_dd)

    max_drawdown_duration = max(drawdown_periods) if drawdown_periods else 0

    return {
        'max_drawdown': max_drawdown,
        'max_drawdown_pct': max_drawdown_pct,
        'max_drawdown_duration': max_drawdown_duration,
        'drawdown_series': drawdown
    }

def calculate_risk_ratios(df):
    """
    Calcula ratios de riesgo (Sharpe, Sortino, etc.)

    Parameters:
    df (DataFrame): Datos de trading

    Returns:
    dict: Ratios de riesgo calculados
    """
    # Retornos por trade
    returns = df['profit_usd'].values

    if len(returns) == 0:
        return {
            'sharpe_ratio': 0,
            'sortino_ratio': 0,
            'calmar_ratio': 0,
            'volatility': 0
        }

    # Retorno promedio
    avg_return = np.mean(returns)

    # Volatilidad (desviación estándar)
    volatility = np.std(returns, ddof=1) if len(returns) > 1 else 0

    # Sharpe Ratio (asumiendo risk-free rate = 0)
    sharpe_ratio = avg_return / volatility if volatility > 0 else 0

    # Sortino Ratio (solo considera volatilidad negativa)
    negative_returns = returns[returns < 0]
    downside_volatility = np.std(negative_returns, ddof=1) if len(negative_returns) > 1 else 0
    sortino_ratio = avg_return / downside_volatility if downside_volatility > 0 else 0

    # Para Calmar ratio necesitamos la curva de equity
    equity_curve = df['profit_usd'].cumsum()
    drawdown_stats = calculate_drawdown_stats(equity_curve)

    # Calmar Ratio = Annual Return / Max Drawdown
    # Aproximamos annual return basado en el período total
    period_days = (df['exit_time'].max() - df['entry_time'].min()).days
    annual_factor = 365 / period_days if period_days > 0 else 1
    annual_return = avg_return * len(returns) * annual_factor

    calmar_ratio = annual_return / abs(drawdown_stats['max_drawdown']) if drawdown_stats['max_drawdown'] < 0 else 0

    return {
        'sharpe_ratio': sharpe_ratio,
        'sortino_ratio': sortino_ratio,
        'calmar_ratio': calmar_ratio,
        'volatility': volatility,
        'annual_return': annual_return
    }

def create_equity_curve_chart(df, filename_prefix):
    """
    Crea gráfico de curva de equity

    Parameters:
    df (DataFrame): Datos de trading
    filename_prefix (str): Prefijo para el nombre del archivo
    """
    # Ordenar por tiempo de salida para la secuencia correcta
    df_sorted = df.sort_values('exit_time').copy()

    # Calcular equity acumulada
    df_sorted['cumulative_profit'] = df_sorted['profit_usd'].cumsum()

    # Crear gráfico
    fig = go.Figure()

    # Área de equity curve en verde
    fig.add_trace(go.Scatter(
        x=df_sorted['exit_time'],
        y=df_sorted['cumulative_profit'],
        mode='lines',
        fill='tonexty',
        fillcolor='rgba(0, 255, 0, 0.3)',
        line=dict(color='green', width=2),
        name='Equity Curve',
        hovertemplate='Date: %{x}<br>Cumulative P&L: $%{y:,.2f}<extra></extra>'
    ))

    # Línea de cero
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.7)

    # Configurar layout
    fig.update_layout(
        title='Equity Curve - Cumulative P&L',
        xaxis_title='Date',
        yaxis_title='Cumulative Profit/Loss ($)',
        template='plotly_white',
        width=1200,
        height=600,
        showlegend=False,
        hovermode='x unified'
    )

    # Guardar gráfico
    charts_dir = 'charts'
    os.makedirs(charts_dir, exist_ok=True)
    html_path = f'{charts_dir}/equity_curve_{filename_prefix}.html'
    fig.write_html(html_path, config={"scrollZoom": True})

    print(f"Gráfico de equity curve guardado: {html_path}")
    webbrowser.open('file://' + os.path.realpath(html_path))

    return df_sorted['cumulative_profit']

def create_ratios_table(stats, risk_ratios, drawdown_stats, filename_prefix):
    """
    Crea una tabla HTML con todos los ratios y estadísticas

    Parameters:
    stats (dict): Estadísticas básicas
    risk_ratios (dict): Ratios de riesgo
    drawdown_stats (dict): Estadísticas de drawdown
    filename_prefix (str): Prefijo para el nombre del archivo
    """
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Strategy Performance Ratios - {filename_prefix}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            .header {{
                text-align: center;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .header h1 {{
                margin: 0;
                font-size: 2.5em;
            }}
            .header p {{
                margin: 10px 0 0 0;
                font-size: 1.2em;
                opacity: 0.9;
            }}
            .container {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
                max-width: 1400px;
                margin: 0 auto;
            }}
            .section {{
                background: white;
                border-radius: 10px;
                padding: 25px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .section h2 {{
                margin-top: 0;
                color: #333;
                font-size: 1.8em;
                border-bottom: 3px solid #667eea;
                padding-bottom: 10px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }}
            th, td {{
                padding: 12px 15px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #f8f9fa;
                font-weight: 600;
                color: #333;
            }}
            tr:hover {{
                background-color: #f8f9fa;
            }}
            .metric-name {{
                font-weight: 500;
                color: #555;
            }}
            .metric-value {{
                font-weight: 600;
                color: #333;
            }}
            .positive {{
                color: #28a745;
            }}
            .negative {{
                color: #dc3545;
            }}
            .neutral {{
                color: #6c757d;
            }}
            .highlight {{
                background-color: #e3f2fd !important;
                font-weight: bold;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                padding: 20px;
                background: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Strategy Performance Report</h1>
            <p>Larry Williams Volatility Breakout - {filename_prefix}</p>
        </div>

        <div class="container">
            <div class="section">
                <h2>📈 Basic Statistics</h2>
                <table>
                    <thead>
                        <tr><th>Metric</th><th>Value</th></tr>
                    </thead>
                    <tbody>
                        <tr><td class="metric-name">Total Trades</td><td class="metric-value">{stats['total_trades']:,}</td></tr>
                        <tr><td class="metric-name">Winning Trades</td><td class="metric-value positive">{stats['winning_trades']:,}</td></tr>
                        <tr><td class="metric-name">Losing Trades</td><td class="metric-value negative">{stats['losing_trades']:,}</td></tr>
                        <tr class="highlight"><td class="metric-name">Win Rate</td><td class="metric-value {'positive' if stats['win_rate'] > 50 else 'negative'}">{stats['win_rate']:.1f}%</td></tr>
                        <tr><td class="metric-name">Average Time in Market</td><td class="metric-value">{stats['avg_time_in_market']:.1f} min ({stats['avg_time_in_market']/60:.1f}h)</td></tr>
                        <tr><td class="metric-name">Max Winning Streak</td><td class="metric-value positive">{stats['max_winning_streak']} trades</td></tr>
                        <tr><td class="metric-name">Max Losing Streak</td><td class="metric-value negative">{stats['max_losing_streak']} trades</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="section">
                <h2>💰 Profitability Metrics</h2>
                <table>
                    <thead>
                        <tr><th>Metric</th><th>Value</th></tr>
                    </thead>
                    <tbody>
                        <tr class="highlight"><td class="metric-name">Total P&L</td><td class="metric-value {'positive' if stats['total_profit_usd'] > 0 else 'negative'}">${stats['total_profit_usd']:,.2f}</td></tr>
                        <tr><td class="metric-name">Average Trade P&L</td><td class="metric-value {'positive' if stats['avg_trade_profit'] > 0 else 'negative'}">${stats['avg_trade_profit']:,.2f}</td></tr>
                        <tr><td class="metric-name">Average Winning Trade</td><td class="metric-value positive">${stats['avg_winning_trade']:,.2f}</td></tr>
                        <tr><td class="metric-name">Average Losing Trade</td><td class="metric-value negative">${stats['avg_losing_trade']:,.2f}</td></tr>
                        <tr class="highlight"><td class="metric-name">Profit Factor</td><td class="metric-value {'positive' if stats['profit_factor'] > 1 else 'negative'}">{stats['profit_factor']:.2f}</td></tr>
                        <tr><td class="metric-name">Gross Profit</td><td class="metric-value positive">${stats['gross_profit']:,.2f}</td></tr>
                        <tr><td class="metric-name">Gross Loss</td><td class="metric-value negative">${stats['gross_loss']:,.2f}</td></tr>
                        <tr><td class="metric-name">Best Trade</td><td class="metric-value positive">${stats['max_profit']:,.2f}</td></tr>
                        <tr><td class="metric-name">Worst Trade</td><td class="metric-value negative">${stats['max_loss']:,.2f}</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="section">
                <h2>⚡ Risk-Adjusted Ratios</h2>
                <table>
                    <thead>
                        <tr><th>Ratio</th><th>Value</th><th>Interpretation</th></tr>
                    </thead>
                    <tbody>
                        <tr class="highlight">
                            <td class="metric-name">Sharpe Ratio</td>
                            <td class="metric-value {'positive' if risk_ratios['sharpe_ratio'] > 0 else 'negative'}">{risk_ratios['sharpe_ratio']:.3f}</td>
                            <td class="metric-value">{'Excellent' if risk_ratios['sharpe_ratio'] > 1 else 'Good' if risk_ratios['sharpe_ratio'] > 0.5 else 'Poor'}</td>
                        </tr>
                        <tr class="highlight">
                            <td class="metric-name">Sortino Ratio</td>
                            <td class="metric-value {'positive' if risk_ratios['sortino_ratio'] > 0 else 'negative'}">{risk_ratios['sortino_ratio']:.3f}</td>
                            <td class="metric-value">{'Excellent' if risk_ratios['sortino_ratio'] > 1 else 'Good' if risk_ratios['sortino_ratio'] > 0.5 else 'Poor'}</td>
                        </tr>
                        <tr class="highlight">
                            <td class="metric-name">Calmar Ratio</td>
                            <td class="metric-value {'positive' if risk_ratios['calmar_ratio'] > 0 else 'negative'}">{risk_ratios['calmar_ratio']:.3f}</td>
                            <td class="metric-value">{'Good' if risk_ratios['calmar_ratio'] > 0.5 else 'Moderate' if risk_ratios['calmar_ratio'] > 0 else 'Poor'}</td>
                        </tr>
                        <tr>
                            <td class="metric-name">Volatility</td>
                            <td class="metric-value">${risk_ratios['volatility']:,.2f}</td>
                            <td class="metric-value">Per Trade</td>
                        </tr>
                        <tr>
                            <td class="metric-name">Annualized Return</td>
                            <td class="metric-value {'positive' if risk_ratios['annual_return'] > 0 else 'negative'}">${risk_ratios['annual_return']:,.2f}</td>
                            <td class="metric-value">Projected Annual</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="section">
                <h2>📉 Drawdown Analysis</h2>
                <table>
                    <thead>
                        <tr><th>Metric</th><th>Value</th></tr>
                    </thead>
                    <tbody>
                        <tr class="highlight"><td class="metric-name">Maximum Drawdown</td><td class="metric-value negative">${drawdown_stats['max_drawdown']:,.2f}</td></tr>
                        <tr class="highlight"><td class="metric-name">Max Drawdown %</td><td class="metric-value negative">{drawdown_stats['max_drawdown_pct']:.2f}%</td></tr>
                        <tr><td class="metric-name">Max Drawdown Duration</td><td class="metric-value">{drawdown_stats['max_drawdown_duration']} trades</td></tr>
                    </tbody>
                </table>

                <div style="margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 5px; border-left: 4px solid #667eea;">
                    <h4 style="margin: 0 0 10px 0; color: #333;">📊 Ratio Guidelines:</h4>
                    <p style="margin: 5px 0; font-size: 0.9em;"><strong>Sharpe Ratio:</strong> >1.0 Excellent, >0.5 Good, <0.5 Poor</p>
                    <p style="margin: 5px 0; font-size: 0.9em;"><strong>Sortino Ratio:</strong> >1.0 Excellent, >0.5 Good, <0.5 Poor</p>
                    <p style="margin: 5px 0; font-size: 0.9em;"><strong>Profit Factor:</strong> >2.0 Excellent, >1.5 Good, >1.0 Profitable</p>
                    <p style="margin: 5px 0; font-size: 0.9em;"><strong>Calmar Ratio:</strong> >0.5 Good, >0.0 Positive, <0.0 Poor</p>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>📈 <strong>Strategy Summary:</strong>
            {'🟢 Profitable Strategy' if stats['total_profit_usd'] > 0 else '🔴 Losing Strategy'} |
            {'🎯 High Win Rate' if stats['win_rate'] > 60 else '⚖️ Moderate Win Rate' if stats['win_rate'] > 40 else '❌ Low Win Rate'} |
            {'💪 Strong Profit Factor' if stats['profit_factor'] > 1.5 else '⚖️ Moderate Profit Factor' if stats['profit_factor'] > 1 else '⚠️ Weak Profit Factor'}
            </p>
            <p style="margin-top: 10px; font-size: 0.9em; color: #666;">
                Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Larry Williams Volatility Breakout Strategy
            </p>
        </div>
    </body>
    </html>
    """

    # Guardar archivo HTML
    charts_dir = 'charts'
    os.makedirs(charts_dir, exist_ok=True)
    html_path = f'{charts_dir}/strategy_ratios_{filename_prefix}.html'

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"Tabla de ratios guardada: {html_path}")
    webbrowser.open('file://' + os.path.realpath(html_path))

def create_performance_charts(df, stats, filename_prefix):
    """
    Crea gráficos adicionales de rendimiento
    """
    # Crear subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=['Monthly Returns', 'Profit/Loss Distribution',
                       'Trade Duration', 'Rolling Win Rate'],
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )

    # 1. Retornos mensuales
    df_monthly = df.copy()
    df_monthly['month'] = df_monthly['exit_time'].dt.to_period('M')
    monthly_returns = df_monthly.groupby('month')['profit_usd'].sum()

    fig.add_trace(go.Bar(
        x=[str(m) for m in monthly_returns.index],
        y=monthly_returns.values,
        name='Monthly P&L',
        marker_color=['green' if x > 0 else 'red' for x in monthly_returns.values]
    ), row=1, col=1)

    # 2. Distribución de P&L
    fig.add_trace(go.Histogram(
        x=df['profit_usd'],
        nbinsx=20,
        name='P&L Distribution',
        marker_color='lightblue',
        opacity=0.7
    ), row=1, col=2)

    # 3. Duración de trades
    fig.add_trace(go.Histogram(
        x=df['time_in_market_minutes'],
        nbinsx=15,
        name='Trade Duration',
        marker_color='orange',
        opacity=0.7
    ), row=2, col=1)

    # 4. Rolling win rate
    df_sorted = df.sort_values('exit_time')
    window = min(20, len(df_sorted) // 4)  # Ventana móvil
    if window > 0:
        rolling_wins = df_sorted['profit_label'].apply(lambda x: 1 if x == 'PROFIT' else 0)
        rolling_win_rate = rolling_wins.rolling(window=window).mean() * 100

        fig.add_trace(go.Scatter(
            x=df_sorted['exit_time'],
            y=rolling_win_rate,
            mode='lines',
            name=f'Rolling Win Rate ({window} trades)',
            line=dict(color='purple', width=2)
        ), row=2, col=2)

    # Actualizar layout
    fig.update_layout(
        height=800,
        showlegend=False,
        title_text="Performance Analysis Dashboard"
    )

    # Guardar
    charts_dir = 'charts'
    html_path = f'{charts_dir}/performance_dashboard_{filename_prefix}.html'
    fig.write_html(html_path, config={"scrollZoom": True})

    print(f"Dashboard de rendimiento guardado: {html_path}")

def print_summary_report(stats, risk_ratios, filename):
    """
    Imprime reporte completo de la estrategia
    """
    print("\n" + "="*80)
    print(f"RESUMEN DE ESTRATEGIA - {filename}")
    print("="*80)

    print("\n📊 ESTADÍSTICAS BÁSICAS:")
    print(f"  • Total de operaciones: {stats['total_trades']:,}")
    print(f"  • Operaciones ganadoras: {stats['winning_trades']:,}")
    print(f"  • Operaciones perdedoras: {stats['losing_trades']:,}")
    print(f"  • Tasa de acierto: {stats['win_rate']:.1f}%")

    print("\n💰 RENTABILIDAD:")
    print(f"  • P&L Total: ${stats['total_profit_usd']:,.2f}")
    print(f"  • P&L Promedio por trade: ${stats['avg_trade_profit']:,.2f}")
    print(f"  • Ganancia promedio: ${stats['avg_winning_trade']:,.2f}")
    print(f"  • Pérdida promedio: ${stats['avg_losing_trade']:,.2f}")
    print(f"  • Profit Factor: {stats['profit_factor']:.2f}")
    print(f"  • Ganancia bruta: ${stats['gross_profit']:,.2f}")
    print(f"  • Pérdida bruta: ${stats['gross_loss']:,.2f}")

    print("\n⏱️ TIEMPO EN MERCADO:")
    print(f"  • Tiempo promedio por trade: {stats['avg_time_in_market']:.1f} minutos")
    print(f"  • Tiempo promedio por trade: {stats['avg_time_in_market']/60:.1f} horas")

    print("\n📈 EXTREMOS:")
    print(f"  • Mejor trade: ${stats['max_profit']:,.2f}")
    print(f"  • Peor trade: ${stats['max_loss']:,.2f}")
    print(f"  • Racha ganadora máxima: {stats['max_winning_streak']} trades")
    print(f"  • Racha perdedora máxima: {stats['max_losing_streak']} trades")

    print("\n⚡ RATIOS DE RIESGO:")
    print(f"  • Ratio de Sharpe: {risk_ratios['sharpe_ratio']:.3f}")
    print(f"  • Ratio de Sortino: {risk_ratios['sortino_ratio']:.3f}")
    print(f"  • Ratio de Calmar: {risk_ratios['calmar_ratio']:.3f}")
    print(f"  • Volatilidad: ${risk_ratios['volatility']:,.2f}")
    print(f"  • Retorno anualizado: ${risk_ratios['annual_return']:,.2f}")

    print("\n" + "="*80)

def generate_strategy_summary(filename=None):
    """
    Función principal que genera el resumen completo de la estrategia

    Parameters:
    filename (str): Nombre del archivo de tracking (opcional)
    """
    print("Iniciando análisis de estrategia...")

    # Cargar datos
    df, tracking_filename = load_tracking_data(filename)

    # Extraer prefijo del nombre del archivo para los gráficos
    filename_prefix = tracking_filename.replace('tracking_record_', '').replace('.csv', '')

    print(f"Analizando {len(df)} operaciones del archivo: {tracking_filename}")

    # Calcular estadísticas
    stats = calculate_basic_stats(df)
    risk_ratios = calculate_risk_ratios(df)

    # Crear equity curve
    equity_curve = create_equity_curve_chart(df, filename_prefix)

    # Calcular drawdown
    drawdown_stats = calculate_drawdown_stats(equity_curve)

    # Añadir estadísticas de drawdown al reporte
    stats.update({
        'max_drawdown': drawdown_stats['max_drawdown'],
        'max_drawdown_pct': drawdown_stats['max_drawdown_pct'],
        'max_drawdown_duration': drawdown_stats['max_drawdown_duration']
    })

    # Crear tabla de ratios HTML
    create_ratios_table(stats, risk_ratios, drawdown_stats, filename_prefix)

    # Crear gráficos adicionales
    create_performance_charts(df, stats, filename_prefix)

    # Imprimir reporte
    print_summary_report(stats, risk_ratios, tracking_filename)

    print(f"\n✅ Análisis completado. Gráficos guardados en directorio 'charts/'")

    return stats, risk_ratios, df

if __name__ == "__main__":
    # Ejecutar análisis
    stats, risk_ratios, df = generate_strategy_summary(target_filename)