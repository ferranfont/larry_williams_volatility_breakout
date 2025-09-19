import pandas as pd

def add_day_of_week(df, date_column='date'):
    """
    Añade columna dow con el nombre del día de la semana

    Parameters:
    df (DataFrame): DataFrame con una columna de fecha
    date_column (str): Nombre de la columna que contiene las fechas

    Returns:
    DataFrame: DataFrame con columna dow
    """
    df_copy = df.copy()

    # Asegurar que la columna de fecha es datetime
    if date_column in df_copy.columns:
        df_copy[date_column] = pd.to_datetime(df_copy[date_column])
        date_series = df_copy[date_column]
    elif df_copy.index.name == date_column or isinstance(df_copy.index, pd.DatetimeIndex):
        date_series = df_copy.index
    else:
        raise ValueError(f"No se encontró la columna de fecha: {date_column}")

    # Agregar día de la semana como string
    df_copy['dow'] = date_series.dt.day_name().str.lower()

    return df_copy

if __name__ == "__main__":
    print("Date utilities module loaded successfully")
    print("Available functions:")
    print("- add_day_of_week(df, date_column='date')")