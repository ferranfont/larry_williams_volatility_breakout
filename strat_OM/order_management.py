import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def order_management(df, dow_filter=0, use_fixed_stop=False, fixed_stop_usd=800, trail=12, tp_days=0):
    """
    Sistema de gestión de órdenes basado en señales de crossover con trailing stop y target profit

    Parameters:
    df (DataFrame): DataFrame con datos de precios y niveles
    dow_filter (int): Filtro de día de la semana (0=sin filtro, 1=lunes, 2=martes, 3=miércoles, 4=jueves, 5=viernes)
    use_fixed_stop (bool): Si usar stop fijo en USD en lugar de stop basado en range
    fixed_stop_usd (float): Cantidad en USD para stop fijo (default 800)
    trail (float): Puntos de ganancia para activar trailing stop a break-even (default 12)
    tp_days (int): Días para mantener la posición (0=cierre mismo día, 1=siguiente día, etc.)

    Returns:
    tuple: (trades_df, df_with_trades) - Registro de operaciones y DataFrame enriquecido
    """

    # Preparar datos
    df = df.copy()
    df = df.sort_values('date').reset_index(drop=True)

    # Detectar señales de crossover (misma lógica que en el gráfico)
    df['date_only'] = df['date'].dt.date

    # Agrupar por día para obtener niveles únicos
    daily_levels = df.groupby('date_only').agg({
        'long_level': 'first',
        'short_level': 'first',
        'long_stop': 'first',
        'short_stop': 'first'
    }).reset_index()

    # Convertir a float
    for col in ['long_level', 'short_level', 'long_stop', 'short_stop']:
        daily_levels[col] = pd.to_numeric(daily_levels[col], errors='coerce')

    trades = []
    active_trade = None  # Mantener trade activo a través de múltiples días

    # Procesar cada día
    for _, day_levels in daily_levels.iterrows():
        day_data = df[df['date_only'] == day_levels['date_only']].copy()

        if len(day_data) < 2:
            continue

        # Aplicar filtro de día de la semana si está activo (solo para nuevas entradas)
        if dow_filter > 0 and active_trade is None:
            # Obtener el día de la semana del primer registro del día
            first_record = day_data.iloc[0]
            day_dow = first_record['dow'].lower()

            # Mapeo de números a días de la semana
            dow_mapping = {
                1: 'monday',
                2: 'tuesday',
                3: 'wednesday',
                4: 'thursday',
                5: 'friday'
            }

            # Si el día no coincide con el filtro, saltar este día
            if day_dow != dow_mapping.get(dow_filter):
                continue

        day_data = day_data.sort_values('date').reset_index(drop=True)

        long_level = day_levels['long_level']
        short_level = day_levels['short_level']
        long_stop = day_levels['long_stop']
        short_stop = day_levels['short_stop']

        # Skip si algún nivel es NaN
        if pd.isna(long_level) or pd.isna(short_level) or pd.isna(long_stop) or pd.isna(short_stop):
            continue

        # Variables para controlar señales del día (solo si no hay trade activo)
        if active_trade is None:
            long_signal_triggered = False
            short_signal_triggered = False
        else:
            # Si hay trade activo, no buscar nuevas señales
            long_signal_triggered = True
            short_signal_triggered = True

        # Analizar minuto a minuto
        for i in range(1, len(day_data)):
            current_time = day_data.iloc[i]['date']
            current_price = day_data.iloc[i]['close']
            prev_price = day_data.iloc[i-1]['close']

            # Detectar señal LONG (primer crossover verde del día)
            if not long_signal_triggered and prev_price <= long_level < current_price:
                if active_trade is None:  # No hay trade activo
                    # Calcular stop level basado en configuración
                    if use_fixed_stop:
                        # Stop fijo: entry_price - (stop_usd / 50)
                        # $50 por punto, entonces stop_usd / 50 = puntos de stop
                        stop_points = fixed_stop_usd / 50
                        calculated_stop = current_price - stop_points
                    else:
                        # Stop basado en range (comportamiento original)
                        calculated_stop = long_stop

                    # Calcular fecha objetivo de salida
                    entry_date = day_levels['date_only']
                    target_exit_date = entry_date + timedelta(days=tp_days)

                    active_trade = {
                        'entry_time': current_time,
                        'entry_price': current_price,
                        'trade_type': 'BUY',
                        'stop_level': calculated_stop,
                        'date_only': day_levels['date_only'],
                        'target_exit_date': target_exit_date
                    }
                    long_signal_triggered = True

            # Detectar señal SHORT (primer crossunder rojo del día)
            elif not short_signal_triggered and prev_price >= short_level > current_price:
                if active_trade is None:  # No hay trade activo
                    # Calcular stop level basado en configuración
                    if use_fixed_stop:
                        # Stop fijo: entry_price + (stop_usd / 50)
                        stop_points = fixed_stop_usd / 50
                        calculated_stop = current_price + stop_points
                    else:
                        # Stop basado en range (comportamiento original)
                        calculated_stop = short_stop

                    # Calcular fecha objetivo de salida
                    entry_date = day_levels['date_only']
                    target_exit_date = entry_date + timedelta(days=tp_days)

                    active_trade = {
                        'entry_time': current_time,
                        'entry_price': current_price,
                        'trade_type': 'SELL',
                        'stop_level': calculated_stop,
                        'date_only': day_levels['date_only'],
                        'target_exit_date': target_exit_date
                    }
                    short_signal_triggered = True

            # Verificar salidas si hay trade activo
            if active_trade is not None:
                exit_triggered = False
                exit_reason = None

                # Aplicar trailing stop (mover stop a break-even cuando hay ganancia >= trail puntos)
                if active_trade['trade_type'] == 'BUY':
                    # Para BUY: si precio actual está 'trail' puntos arriba del entry, mover stop a break-even
                    profit_points = current_price - active_trade['entry_price']
                    if profit_points >= trail and active_trade['stop_level'] < active_trade['entry_price']:
                        active_trade['stop_level'] = active_trade['entry_price']  # Break-even
                elif active_trade['trade_type'] == 'SELL':
                    # Para SELL: si precio actual está 'trail' puntos abajo del entry, mover stop a break-even
                    profit_points = active_trade['entry_price'] - current_price
                    if profit_points >= trail and active_trade['stop_level'] > active_trade['entry_price']:
                        active_trade['stop_level'] = active_trade['entry_price']  # Break-even

                # Verificar stop loss
                if active_trade['trade_type'] == 'BUY' and current_price <= active_trade['stop_level']:
                    exit_triggered = True
                    exit_reason = 'STOP_LOSS'
                elif active_trade['trade_type'] == 'SELL' and current_price >= active_trade['stop_level']:
                    exit_triggered = True
                    exit_reason = 'STOP_LOSS'

                # Verificar si se alcanzó la fecha objetivo de salida
                current_date = current_time.date()
                if current_date >= active_trade['target_exit_date']:
                    # Si estamos en la fecha objetivo o después, cerrar al final del día
                    if i == len(day_data) - 1:
                        exit_triggered = True
                        if tp_days == 0:
                            exit_reason = 'END_OF_DAY'
                        else:
                            exit_reason = f'TARGET_PROFIT_{tp_days}D'

                # Ejecutar salida
                if exit_triggered:
                    exit_time = current_time
                    exit_price = current_price

                    # Calcular métricas
                    if active_trade['trade_type'] == 'BUY':
                        profit_points = exit_price - active_trade['entry_price']
                        profit_label = 'PROFIT' if profit_points > 0 else 'LOSS'
                    else:  # SELL
                        profit_points = active_trade['entry_price'] - exit_price
                        profit_label = 'PROFIT' if profit_points > 0 else 'LOSS'

                    profit_usd = profit_points * 50  # $50 por punto
                    time_in_market = (exit_time - active_trade['entry_time']).total_seconds() / 60  # minutos

                    # Registrar trade
                    trade_record = {
                        'date': active_trade['date_only'],
                        'dow': day_data.iloc[0]['dow'],  # Día de la semana
                        'trade_type': active_trade['trade_type'],
                        'entry_time': active_trade['entry_time'],
                        'entry_price': active_trade['entry_price'],
                        'exit_time': exit_time,
                        'exit_price': exit_price,
                        'exit_reason': exit_reason,
                        'profit_points': round(profit_points, 2),
                        'profit_usd': round(profit_usd, 2),
                        'profit_label': profit_label,
                        'time_in_market_minutes': round(time_in_market, 1),
                        'stop_level': active_trade['stop_level']
                    }

                    trades.append(trade_record)

                    # Reset trade
                    active_trade = None

    # Si queda un trade activo al final del período, cerrarlo
    if active_trade is not None:
        # Buscar el último precio disponible
        last_day_data = df[df['date_only'] == df['date_only'].max()]
        if len(last_day_data) > 0:
            last_price = last_day_data.iloc[-1]['close']
            last_time = last_day_data.iloc[-1]['date']

            # Calcular métricas
            if active_trade['trade_type'] == 'BUY':
                profit_points = last_price - active_trade['entry_price']
                profit_label = 'PROFIT' if profit_points > 0 else 'LOSS'
            else:  # SELL
                profit_points = active_trade['entry_price'] - last_price
                profit_label = 'PROFIT' if profit_points > 0 else 'LOSS'

            profit_usd = profit_points * 50  # $50 por punto
            time_in_market = (last_time - active_trade['entry_time']).total_seconds() / 60  # minutos

            # Registrar trade final
            trade_record = {
                'date': active_trade['date_only'],
                'dow': df[df['date_only'] == active_trade['date_only']].iloc[0]['dow'],
                'trade_type': active_trade['trade_type'],
                'entry_time': active_trade['entry_time'],
                'entry_price': active_trade['entry_price'],
                'exit_time': last_time,
                'exit_price': last_price,
                'exit_reason': 'END_OF_PERIOD',
                'profit_points': round(profit_points, 2),
                'profit_usd': round(profit_usd, 2),
                'profit_label': profit_label,
                'time_in_market_minutes': round(time_in_market, 1),
                'stop_level': active_trade['stop_level']
            }

            trades.append(trade_record)

    # Convertir a DataFrame
    trades_df = pd.DataFrame(trades)

    # Enriquecer DataFrame original con datos de trading
    df_with_trades = df.copy()

    # Inicializar columnas con el mismo tipo de datetime que 'date'
    df_with_trades['entry_time'] = pd.Series(dtype='datetime64[ns, UTC]')
    df_with_trades['entry_price'] = np.nan
    df_with_trades['exit_time'] = pd.Series(dtype='datetime64[ns, UTC]')
    df_with_trades['exit_price'] = np.nan
    df_with_trades['trade_type'] = ''

    # Añadir datos de trading al DataFrame original
    for _, trade in trades_df.iterrows():
        # Marcar entrada
        entry_mask = df_with_trades['date'] == trade['entry_time']
        df_with_trades.loc[entry_mask, 'entry_time'] = trade['entry_time']
        df_with_trades.loc[entry_mask, 'entry_price'] = trade['entry_price']
        df_with_trades.loc[entry_mask, 'trade_type'] = trade['trade_type']

        # Marcar salida
        exit_mask = df_with_trades['date'] == trade['exit_time']
        df_with_trades.loc[exit_mask, 'exit_time'] = trade['exit_time']
        df_with_trades.loc[exit_mask, 'exit_price'] = trade['exit_price']

    return trades_df, df_with_trades

def save_trading_results(trades_df, period_start, period_end, use_fixed_stop=False, fixed_stop_usd=800, trail=12, tp_days=0):
    """
    Guarda los resultados de trading en CSV

    Parameters:
    trades_df (DataFrame): DataFrame con los trades
    period_start (str): Fecha de inicio del período
    period_end (str): Fecha de fin del período
    use_fixed_stop (bool): Si se usó stop fijo
    fixed_stop_usd (float): Valor del stop fijo en USD
    trail (float): Puntos para activar trailing stop
    tp_days (int): Días para mantener la posición
    """
    if len(trades_df) == 0:
        print("No hay trades para guardar")
        return

    # Obtener ruta del directorio outputs
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    outputs_dir = os.path.join(parent_dir, 'outputs')

    # Crear directorio outputs si no existe
    os.makedirs(outputs_dir, exist_ok=True)

    # Generar nombre de archivo con información del stop
    start_str = period_start.replace('-', '')
    end_str = period_end.replace('-', '')

    if use_fixed_stop:
        stop_info = f'fix_stop_{int(fixed_stop_usd)}_trail_{int(trail)}_tp_{int(tp_days)}d'
    else:
        stop_info = f'range_stop_trail_{int(trail)}_tp_{int(tp_days)}d'

    filename = f'tracking_record_{start_str}_{end_str}_{stop_info}.csv'

    # Ruta completa en directorio outputs
    full_path = os.path.join(outputs_dir, filename)

    # Guardar CSV
    trades_df.to_csv(full_path, index=False)

    # Estadísticas resumen
    total_trades = len(trades_df)
    profitable_trades = len(trades_df[trades_df['profit_label'] == 'PROFIT'])
    total_profit_usd = trades_df['profit_usd'].sum()
    win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
    avg_time_in_market = trades_df['time_in_market_minutes'].mean()

    print(f"\n=== RESULTADOS DE TRADING ===")
    print(f"Archivo guardado: {full_path}")
    print(f"Total trades: {total_trades}")
    print(f"Trades rentables: {profitable_trades}")
    print(f"Win rate: {win_rate:.1f}%")
    print(f"Profit total: ${total_profit_usd:.2f}")
    print(f"Tiempo promedio en mercado: {avg_time_in_market:.1f} minutos")

    return full_path

if __name__ == "__main__":
    print("Order Management module loaded successfully")
    print("Available functions:")
    print("- order_management(df)")
    print("- save_trading_results(trades_df, period_start, period_end)")