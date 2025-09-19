import pandas as pd
import numpy as np

def calculate_range(df):
    """
    Calcula el range como la diferencia entre high y low

    Parameters:
    df (DataFrame): DataFrame con columnas 'high' y 'low'

    Returns:
    Series: Range calculado para cada fila
    """
    return df['high'] - df['low']

def calculate_range_enter(df, expansion_pct=0.1, use_avg=False, lookback=20):
    """
    Calcula range_enter usando range_avg * expansion_pct

    Parameters:
    df (DataFrame): DataFrame con columnas 'high' y 'low'
    expansion_pct (float): Porcentaje de expansión del range (default 10%)
    use_avg (bool): Si usar range_avg en lugar de range
    lookback (int): Lookback para range_avg

    Returns:
    Series: Range para entrada
    """
    if use_avg:
        range_val = calculate_range_avg(df, lookback)
    else:
        range_val = calculate_range(df)
    return range_val * expansion_pct

def calculate_range_stop(df, stop_multiplier=2.0, use_avg=False, lookback=20):
    """
    Calcula range_stop usando range_avg * stop_multiplier

    Parameters:
    df (DataFrame): DataFrame con columnas 'high' y 'low'
    stop_multiplier (float): Multiplicador para el stop (default 2.0)
    use_avg (bool): Si usar range_avg en lugar de range
    lookback (int): Lookback para range_avg

    Returns:
    Series: Range para stop loss
    """
    if use_avg:
        range_val = calculate_range_avg(df, lookback)
    else:
        range_val = calculate_range(df)
    return range_val * stop_multiplier

def calculate_range_avg(df, lookback=20):
    """
    Calcula el promedio del range para un período de lookback

    Parameters:
    df (DataFrame): DataFrame con columnas 'high' y 'low'
    lookback (int): Número de períodos para el promedio móvil

    Returns:
    Series: Promedio móvil del range
    """
    range_val = calculate_range(df)
    return range_val.rolling(window=lookback, min_periods=1).mean()

def add_range_indicators(df, expansion_pct=0.1, stop_multiplier=2.0, lookback=20):
    """
    Añade todos los indicadores de range al DataFrame

    Parameters:
    df (DataFrame): DataFrame con columnas 'high' y 'low'
    expansion_pct (float): Porcentaje de expansión para range_enter
    stop_multiplier (float): Multiplicador para range_stop
    lookback (int): Número de períodos para range_avg

    Returns:
    DataFrame: DataFrame original con columnas adicionales de range
    """
    df_copy = df.copy()

    # Calcular todos los ranges
    df_copy['range'] = calculate_range(df_copy).round(2)
    df_copy['range_avg'] = calculate_range_avg(df_copy, lookback).round(2)
    df_copy['range_enter'] = calculate_range_enter(df_copy, expansion_pct, use_avg=True, lookback=lookback).round(2)
    df_copy['range_stop'] = calculate_range_stop(df_copy, stop_multiplier, use_avg=True, lookback=lookback).round(2)

    return df_copy