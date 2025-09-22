# main.py
import pandas as pd
import os
import plotly.graph_objects as go
import webbrowser
from chart_volume import plot_close_and_volume
from quant_stat.range_calculations import add_range_indicators
from utils.date_utils import add_day_of_week
from strat_OM.plot_range import plot_range_chart
from quant_stat.get_levels import get_levels

symbol = 'ES'
timeframe = '1D'

# Parámetros para cálculos de range
expansion_pct = 0.4  # 40% expansión para range_enter
stop_multiplier_pct = 2.5  # 50% para range_stop
range_lookback = 3  # Lookback de 20 días para cálculo de range    

# ====================================================
# 📥 CARGA DE DATOS
# ====================================================
directorio = 'data'
nombre_fichero = 'es_1min_data.csv'
ruta_completa = os.path.join(directorio, nombre_fichero)

print("\n======================== 🔍 df  ===========================")
df = pd.read_csv(ruta_completa, index_col=0, parse_dates=True)
print('Fichero:', ruta_completa, 'importado')
print(f"Características del Fichero Base: {df.shape}")

# Normalizar columnas a minúsculas y renombrar 'volumen' a 'volume'
df.columns = [col.strip().lower() for col in df.columns]
df = df.rename(columns={'volumen': 'volume'})




# ====================================================

# 🔁 Resample a velas diarias
df_daily = df.resample('1D').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum'
}).dropna()

# Reset index para usar 'date' como columna
df_daily = df_daily.reset_index()

print(df_daily.head())
print(f"Datos diarios - shape: {df_daily.shape}")
print(df_daily.info())

# Añadir indicadores de range
df_daily = add_range_indicators(df_daily, expansion_pct, stop_multiplier_pct, range_lookback)

# Añadir día de la semana
df_daily = add_day_of_week(df_daily, 'date')

# Añadir niveles de trading
df_daily = get_levels(df_daily)

# Añadir clasificación de day_type basada en range
def classify_day_type(range_value):
    """
    Clasifica el tipo de día basado en el valor del range

    Parameters:
    range_value (float): Valor del range diario

    Returns:
    str: Clasificación del día
    """
    if pd.isna(range_value):
        return 'unknown'
    elif range_value < 50:
        return 'mean'
    elif range_value < 60:
        return 'upto_60'
    elif range_value < 70:
        return 'upto_70'
    elif range_value < 80:
        return 'upto_80'
    elif range_value < 100:
        return 'upto_100'
    else:
        return 'more_100'

df_daily['day_type'] = df_daily['range'].apply(classify_day_type)

# Remover filas donde dow == "sunday"
df_daily = df_daily[df_daily['dow'] != 'sunday']

# Reordenar columnas
column_order = ['date', 'dow', 'open', 'high', 'low', 'close', 'volume', 'range', 'day_type', 'range_avg', 'range_enter', 'range_stop', 'long_level', 'short_level', 'long_stop', 'short_stop']
df_daily = df_daily[column_order]

# Guardar datos diarios en carpeta data
output_daily = os.path.join('data', 'es_1D_data_range.csv')
df_daily.to_csv(output_daily, index=False)

print(f"Datos diarios guardados en: {output_daily}")

# Mostrar distribución de day_type
print(f"\n=== DISTRIBUCIÓN DE TIPOS DE DÍA ===")
day_type_counts = df_daily['day_type'].value_counts().sort_index()
day_type_pct = df_daily['day_type'].value_counts(normalize=True).sort_index() * 100

print("Clasificación basada en range diario:")
print("- mean: < 50 puntos")
print("- upto_60: 50-60 puntos")
print("- upto_70: 60-70 puntos")
print("- upto_80: 70-80 puntos")
print("- upto_100: 80-100 puntos")
print("- more_100: > 100 puntos")
print()

for day_type in day_type_counts.index:
    count = day_type_counts[day_type]
    percentage = day_type_pct[day_type]
    print(f"{day_type:>10}: {count:4d} días ({percentage:5.1f}%) & {count} days")

print(f"\nTotal días analizados: {len(df_daily):,}")

print("\n=== DataFrame con indicadores de range (sin domingos) ===")
print(df_daily.head(30))

# Ejecutar gráfico
plot_close_and_volume(symbol, timeframe, df_daily)

# Ejecutar gráfico de range
plot_range_chart(symbol, timeframe, df_daily)

def create_range_histogram(df, symbol, timeframe):
    """
    Crea histograma de distribución de ranges diarios

    Parameters:
    df (DataFrame): Datos con columna 'range'
    symbol (str): Símbolo del instrumento
    timeframe (str): Marco temporal
    """
    # Filtrar valores válidos de range
    range_values = df['range'].dropna()

    if len(range_values) == 0:
        print("No hay datos de range válidos para el histograma")
        return

    # Crear histograma
    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=range_values,
        nbinsx=100,
        name='Range Distribution',
        marker_color='steelblue',
        opacity=0.8,
        hovertemplate='Range: %{x:.2f}<br>Count: %{y}<extra></extra>'
    ))

    # Estadísticas
    mean_range = range_values.mean()
    median_range = range_values.median()
    std_range = range_values.std()
    min_range = range_values.min()
    max_range = range_values.max()

    # Configurar layout
    fig.update_layout(
        title=f'{symbol} {timeframe} - Daily Range Distribution (High Resolution)',
        xaxis_title='Range (Points)',
        yaxis_title='Frequency',
        template='plotly_white',
        width=1400,
        height=700,
        showlegend=False
    )

    # Añadir líneas de referencia
    fig.add_vline(x=mean_range, line_dash="dash", line_color="red",
                  annotation_text=f"Mean: {mean_range:.2f}", annotation_position="top")
    fig.add_vline(x=median_range, line_dash="dot", line_color="green",
                  annotation_text=f"Median: {median_range:.2f}", annotation_position="bottom")

    # Añadir estadísticas como anotación
    fig.add_annotation(
        x=0.75, y=0.85,
        xref="paper", yref="paper",
        text=f"<b>Range Statistics</b><br>" +
             f"Mean: {mean_range:.2f}<br>" +
             f"Median: {median_range:.2f}<br>" +
             f"Std Dev: {std_range:.2f}<br>" +
             f"Min: {min_range:.2f}<br>" +
             f"Max: {max_range:.2f}<br>" +
             f"Count: {len(range_values):,}",
        showarrow=False,
        font=dict(size=12, color="black"),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="rgba(0,0,0,0.3)",
        borderwidth=1,
        align="left"
    )

    # Guardar y abrir en navegador
    charts_dir = 'charts'
    os.makedirs(charts_dir, exist_ok=True)
    html_path = f'{charts_dir}/range_histogram_{symbol}_{timeframe}.html'
    fig.write_html(html_path, config={"scrollZoom": True})

    print(f"\nRange histogram guardado: {html_path}")
    print(f"Estadísticas de Range:")
    print(f"  Media: {mean_range:.2f} puntos")
    print(f"  Mediana: {median_range:.2f} puntos")
    print(f"  Desviación estándar: {std_range:.2f} puntos")
    print(f"  Rango: {min_range:.2f} - {max_range:.2f} puntos")

    webbrowser.open('file://' + os.path.realpath(html_path))

# Crear histograma de ranges al final
print(f"\n=== CREANDO HISTOGRAMA DE RANGES ===")
create_range_histogram(df_daily, symbol, timeframe)
