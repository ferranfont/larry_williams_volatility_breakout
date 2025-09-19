import pandas as pd

def calculate_entry_level_long(df):
    """
    Calcula el nivel de entrada long como open de hoy + range_enter de ayer

    Parameters:
    df (DataFrame): DataFrame con columnas 'open' y 'range_enter'

    Returns:
    Series: Nivel de entrada long calculado
    """
    # Open de hoy + range_enter de ayer (shift hacia adelante)
    return df['open'] + df['range_enter'].shift(1)

def calculate_stop_level_long(df):
    """
    Calcula el nivel de stop long como open de hoy - range_stop de ayer

    Parameters:
    df (DataFrame): DataFrame con columnas 'open' y 'range_stop'

    Returns:
    Series: Nivel de stop long calculado
    """
    # Open de hoy - range_stop de ayer (shift hacia adelante)
    return df['open'] - df['range_stop'].shift(1)

def calculate_entry_level_short(df):
    """
    Calcula el nivel de entrada short como open de hoy - range_enter de ayer

    Parameters:
    df (DataFrame): DataFrame con columnas 'open' y 'range_enter'

    Returns:
    Series: Nivel de entrada short calculado
    """
    # Open de hoy - range_enter de ayer (shift hacia adelante)
    return df['open'] - df['range_enter'].shift(1)

def calculate_stop_level_short(df):
    """
    Calcula el nivel de stop short como open de hoy + range_stop de ayer

    Parameters:
    df (DataFrame): DataFrame con columnas 'open' y 'range_stop'

    Returns:
    Series: Nivel de stop short calculado
    """
    # Open de hoy + range_stop de ayer (shift hacia adelante)
    return df['open'] + df['range_stop'].shift(1)

def get_levels(df):
    """
    Calcula y añade los 4 niveles de trading al DataFrame

    Parameters:
    df (DataFrame): DataFrame con columnas 'open', 'range_enter', 'range_stop'

    Returns:
    DataFrame: DataFrame con columnas de niveles: long_level, short_level, long_stop, short_stop
    """
    df_copy = df.copy()

    # Calcular niveles de entrada y stop
    df_copy['long_level'] = calculate_entry_level_long(df_copy).round(2)
    df_copy['long_stop'] = calculate_stop_level_long(df_copy).round(2)
    df_copy['short_level'] = calculate_entry_level_short(df_copy).round(2)
    df_copy['short_stop'] = calculate_stop_level_short(df_copy).round(2)

    return df_copy

def add_entry_levels(df):
    """
    Añade columnas de niveles de entrada y stop para long y short al DataFrame

    Parameters:
    df (DataFrame): DataFrame con columnas 'open', 'range_enter', 'range_stop'

    Returns:
    DataFrame: DataFrame con columnas adicionales de niveles
    """
    df_copy = df.copy()

    # Calcular niveles long
    df_copy['entry_level_long'] = calculate_entry_level_long(df_copy).round(2)
    df_copy['stop_level_long'] = calculate_stop_level_long(df_copy).round(2)

    # Calcular niveles short
    df_copy['entry_level_short'] = calculate_entry_level_short(df_copy).round(2)
    df_copy['stop_level_short'] = calculate_stop_level_short(df_copy).round(2)

    return df_copy

if __name__ == "__main__":
    print("Get levels module loaded successfully")
    print("Available functions:")
    print("- calculate_entry_level(df)")
    print("- calculate_stop_level(df)")
    print("- add_entry_levels(df)")