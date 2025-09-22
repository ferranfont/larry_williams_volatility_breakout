import pandas as pd
import numpy as np
import os
from create_2022_subset import create_subset
from plot_contrarian import plot_contrarian_results

# =============================================================================
# CONFIGURACIÓN DE FECHAS Y PARÁMETROS
# =============================================================================
start_date = '2017-09-02'
end_date = '2020-04-28'

# Parámetros del sistema
STOP_LOSS = 50      # puntos (ajustado para ES)
TARGET = 100        # puntos (ajustado para ES)
TRAILING_STOP = 50  # puntos para break-even

def contrarian_volatility_trading(df):
    """
    Sistema de trading contrarian basado en volatilidad baja del día anterior

    Lógica:
    - Opera solo cuando day_type del día anterior es 'mean' (< 50 puntos)
    - SELL en high del día anterior, BUY en low del día anterior
    - Si apertura > high anterior: SELL a la apertura
    - Si apertura < low anterior: BUY a la apertura
    - Si apertura entre high y low: esperar a que toque uno de los niveles
    - Stop fijo: 500 puntos
    - Target: 1000 puntos
    - Trailing stop: 15 puntos a break-even

    Parameters:
    df (DataFrame): Datos con columnas necesarias

    Returns:
    DataFrame: Resultados de trading
    """

    print(f"Columnas disponibles: {list(df.columns)}")
    print(f"Primeras filas:")
    print(df.head(3))

    # Usar parámetros globales

    # Verificar si tenemos day_type, si no, calcular range simple
    if 'day_type' not in df.columns:
        print("Columna 'day_type' no encontrada. Calculando range simple...")
        # Calcular range diario simple
        df['range_calc'] = df['high'] - df['low']
        # Usar range directamente para filtro >100
        day_type_col = 'range_calc'
    else:
        # Si tenemos day_type, necesitamos también el range numérico
        if 'range' in df.columns:
            day_type_col = 'range'
        else:
            df['range_calc'] = df['high'] - df['low']
            day_type_col = 'range_calc'

    # DataFrame para resultados
    trades = []

    # Preparar datos: agrupar por fecha y obtener datos diarios
    df['date_only'] = pd.to_datetime(df['date']).dt.date

    # Obtener días únicos para iterar
    unique_dates = sorted(df['date_only'].unique())

    print(f"Procesando {len(unique_dates)} días únicos...")

    # Iterar desde el segundo día (necesitamos día anterior)
    for i in range(1, len(unique_dates)):
        current_date = unique_dates[i]
        prev_date = unique_dates[i-1]

        # Obtener datos del día anterior (agregados)
        prev_day_data = df[df['date_only'] == prev_date]
        prev_day_high = prev_day_data['high'].max()
        prev_day_low = prev_day_data['low'].min()
        prev_day_summary = {
            'high': prev_day_high,
            'low': prev_day_low,
            'open': prev_day_data['open'].iloc[0],
            'close': prev_day_data['close'].iloc[-1],
            'range_daily': prev_day_high - prev_day_low,  # Range diario real
            day_type_col: prev_day_data[day_type_col].iloc[0] if day_type_col in prev_day_data.columns else 'unknown'
        }

        # Solo operar si el día anterior tuvo volatilidad ALTA (range > 100 puntos)
        # Usar siempre el range diario calculado
        prev_range_numeric = prev_day_summary['range_daily']

        # Debug: imprimir información del range
        if len(trades) < 5:  # Solo para los primeros días
            print(f"Día {current_date}: range_diario={prev_range_numeric:.1f} puntos")

        if prev_range_numeric <= 100:
            continue

        # Obtener datos del día actual (minuto a minuto)
        current_day_data = df[df['date_only'] == current_date].sort_values('date')

        if len(current_day_data) == 0:
            continue

        # Obtener niveles del día anterior
        prev_high = prev_day_summary['high']
        prev_low = prev_day_summary['low']
        current_open = current_day_data['open'].iloc[0]

        entry_price = None
        entry_type = None
        exit_price = None
        exit_reason = None
        entry_time = None
        exit_time = None

        # Caso 1: Apertura por encima del high anterior -> SELL a la apertura
        if current_open > prev_high:
            entry_price = current_open
            entry_type = 'SELL'
            entry_time = current_day_data['date'].iloc[0]

        # Caso 2: Apertura por debajo del low anterior -> BUY a la apertura
        elif current_open < prev_low:
            entry_price = current_open
            entry_type = 'BUY'
            entry_time = current_day_data['date'].iloc[0]

        # Caso 3: Apertura entre high y low -> esperar a que toque un nivel
        elif prev_low <= current_open <= prev_high:
            # Buscar en datos minuto a minuto si toca algún nivel
            for idx, row in current_day_data.iterrows():
                # Si toca el high -> SELL
                if row['high'] >= prev_high and entry_price is None:
                    entry_price = prev_high
                    entry_type = 'SELL'
                    entry_time = row['date']
                    break
                # Si toca el low -> BUY
                elif row['low'] <= prev_low and entry_price is None:
                    entry_price = prev_low
                    entry_type = 'BUY'
                    entry_time = row['date']
                    break

        # Si hay entrada, simular la gestión de stop/target
        if entry_price is not None and entry_type is not None:
            stop_price = entry_price + STOP_LOSS if entry_type == 'SELL' else entry_price - STOP_LOSS
            target_price = entry_price - TARGET if entry_type == 'SELL' else entry_price + TARGET

            # Filtrar datos después de la entrada
            entry_data = current_day_data[current_day_data['date'] >= entry_time]

            # Buscar exit en datos minuto a minuto
            for idx, row in entry_data.iterrows():
                if entry_type == 'SELL':
                    # Para SELL: stop si sube demasiado, target si baja lo suficiente
                    if row['high'] >= stop_price:
                        exit_price = stop_price
                        exit_reason = 'STOP_LOSS'
                        exit_time = row['date']
                        break
                    elif row['low'] <= target_price:
                        exit_price = target_price
                        exit_reason = 'TARGET'
                        exit_time = row['date']
                        break
                else:  # BUY
                    # Para BUY: stop si baja demasiado, target si sube lo suficiente
                    if row['low'] <= stop_price:
                        exit_price = stop_price
                        exit_reason = 'STOP_LOSS'
                        exit_time = row['date']
                        break
                    elif row['high'] >= target_price:
                        exit_price = target_price
                        exit_reason = 'TARGET'
                        exit_time = row['date']
                        break

            # Si no se tocó stop ni target, salir al cierre
            if exit_price is None:
                exit_price = current_day_data['close'].iloc[-1]
                exit_reason = 'EOD'
                exit_time = current_day_data['date'].iloc[-1]

            # Calcular PnL
            pnl = (exit_price - entry_price) if entry_type == 'BUY' else (entry_price - exit_price)

            trade = {
                'date': current_date,
                'entry_time': entry_time,
                'exit_time': exit_time,
                'entry_type': entry_type,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'exit_reason': exit_reason,
                'pnl': pnl,
                'prev_day_range': prev_day_summary[day_type_col],
                'prev_high': prev_high,
                'prev_low': prev_low,
                'current_open': current_open,
                'current_high': current_day_data['high'].max(),
                'current_low': current_day_data['low'].min(),
                'current_close': current_day_data['close'].iloc[-1]
            }
            trades.append(trade)

    return pd.DataFrame(trades)

def calculate_performance_metrics(trades_df):
    """
    Calcula métricas de rendimiento del sistema

    Parameters:
    trades_df (DataFrame): DataFrame con trades

    Returns:
    dict: Métricas de rendimiento
    """
    if len(trades_df) == 0:
        return {'total_trades': 0}

    total_trades = len(trades_df)
    winning_trades = len(trades_df[trades_df['pnl'] > 0])
    losing_trades = len(trades_df[trades_df['pnl'] < 0])

    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

    total_pnl = trades_df['pnl'].sum()
    avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
    avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0

    profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if losing_trades > 0 and avg_loss != 0 else float('inf')

    # Calcular drawdown máximo
    cumulative_pnl = trades_df['pnl'].cumsum()
    running_max = cumulative_pnl.expanding().max()
    drawdown = cumulative_pnl - running_max
    max_drawdown = drawdown.min()

    metrics = {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_factor': profit_factor,
        'max_drawdown': max_drawdown
    }

    return metrics

def save_contrarian_results(trades_df, start_date, end_date):
    """
    Guarda los resultados del trading contrarian en formato CSV

    Parameters:
    trades_df (DataFrame): DataFrame con trades
    start_date (str): Fecha inicial
    end_date (str): Fecha final

    Returns:
    str: Nombre del archivo guardado
    """
    if len(trades_df) == 0:
        print("No hay trades para guardar")
        return None

    # Crear nombre de archivo con etiqueta _contra_
    start_clean = start_date.replace('-', '')
    end_clean = end_date.replace('-', '')
    filename = f'tracking_record_contra_{start_clean}_{end_clean}.csv'

    # Preparar DataFrame para guardar
    save_df = trades_df.copy()
    save_df['strategy'] = 'contrarian_volatility'
    save_df['system_type'] = 'contrarian'

    # Reordenar columnas
    columns_order = [
        'date', 'entry_time', 'exit_time', 'strategy', 'system_type', 'entry_type', 'entry_price',
        'exit_price', 'exit_reason', 'pnl', 'prev_day_range',
        'prev_high', 'prev_low', 'current_open', 'current_high',
        'current_low', 'current_close'
    ]

    # Asegurar que todas las columnas existen
    for col in columns_order:
        if col not in save_df.columns:
            save_df[col] = None

    save_df = save_df[columns_order]

    # Crear directorio outputs si no existe
    outputs_dir = 'outputs'
    os.makedirs(outputs_dir, exist_ok=True)

    # Ruta completa con directorio outputs
    filepath = os.path.join(outputs_dir, filename)

    # Guardar archivo
    save_df.to_csv(filepath, index=False)
    print(f"Resultados guardados en: {filepath}")

    return filepath

def main():
    """
    Función principal para ejecutar el sistema de trading contrarian
    """

    print("=== SISTEMA DE TRADING CONTRARIAN VOLATILITY ===")
    print(f"Período: {start_date} a {end_date}")
    print("Lógica: Contrarian en días de ALTA volatilidad (range > 100 puntos)")
    print(f"Stop: {STOP_LOSS} puntos | Target: {TARGET} puntos | Trailing: {TRAILING_STOP} puntos")

    # Cargar datos
    print("\n=== CARGANDO DATOS ===")
    df_subset = create_subset(start_date, end_date)
    print(f"Datos cargados: {df_subset.shape}")

    # Ejecutar sistema de trading
    print("\n=== EJECUTANDO SISTEMA DE TRADING ===")
    trades_df = contrarian_volatility_trading(df_subset)

    if len(trades_df) == 0:
        print("No se generaron trades con los criterios especificados")
        return [], {}

    print(f"Total trades generados: {len(trades_df)}")

    # Calcular métricas
    print("\n=== CALCULANDO MÉTRICAS ===")
    metrics = calculate_performance_metrics(trades_df)

    # Mostrar resultados
    print(f"\n=== RESULTADOS DEL SISTEMA ===")
    print(f"Total trades: {metrics['total_trades']}")
    print(f"Trades ganadores: {metrics['winning_trades']}")
    print(f"Trades perdedores: {metrics['losing_trades']}")
    print(f"Win rate: {metrics['win_rate']:.2f}%")
    print(f"PnL total: {metrics['total_pnl']:.2f} puntos")
    print(f"Ganancia promedio: {metrics['avg_win']:.2f} puntos")
    print(f"Pérdida promedio: {metrics['avg_loss']:.2f} puntos")
    print(f"Profit factor: {metrics['profit_factor']:.2f}")
    print(f"Drawdown máximo: {metrics['max_drawdown']:.2f} puntos")

    # Mostrar distribución por tipo de salida
    print(f"\n=== DISTRIBUCIÓN POR TIPO DE SALIDA ===")
    exit_reasons = trades_df['exit_reason'].value_counts()
    for reason, count in exit_reasons.items():
        pct = (count / len(trades_df)) * 100
        print(f"{reason}: {count} trades ({pct:.1f}%)")

    # Mostrar distribución por tipo de entrada
    print(f"\n=== DISTRIBUCIÓN POR TIPO DE ENTRADA ===")
    entry_types = trades_df['entry_type'].value_counts()
    for entry_type, count in entry_types.items():
        pct = (count / len(trades_df)) * 100
        avg_pnl = trades_df[trades_df['entry_type'] == entry_type]['pnl'].mean()
        print(f"{entry_type}: {count} trades ({pct:.1f}%) - PnL promedio: {avg_pnl:.2f}")

    # Guardar resultados con etiqueta _contra_
    print(f"\n=== GUARDANDO RESULTADOS ===")
    tracking_filename = save_contrarian_results(trades_df, start_date, end_date)

    # Generar gráfico
    print(f"\n=== GENERANDO GRÁFICO ===")
    plot_contrarian_results(trades_df, df_subset, metrics)

    return trades_df, metrics

if __name__ == "__main__":
    trades, metrics = main()