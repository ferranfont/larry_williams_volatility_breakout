# main.py
import pandas as pd
import os
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

# Remover filas donde dow == "sunday"
df_daily = df_daily[df_daily['dow'] != 'sunday']

# Reordenar columnas
column_order = ['date', 'dow', 'open', 'high', 'low', 'close', 'volume', 'range', 'range_avg', 'range_enter', 'range_stop', 'long_level', 'short_level', 'long_stop', 'short_stop']
df_daily = df_daily[column_order]

# Guardar datos diarios en carpeta data
output_daily = os.path.join('data', 'es_1D_data_range.csv')
df_daily.to_csv(output_daily, index=False)

print(f"Datos diarios guardados en: {output_daily}")
print("\n=== DataFrame con indicadores de range (sin domingos) ===")
print(df_daily.head(30))

# Ejecutar gráfico
plot_close_and_volume(symbol, timeframe, df_daily)

# Ejecutar gráfico de range
plot_range_chart(symbol, timeframe, df_daily)
