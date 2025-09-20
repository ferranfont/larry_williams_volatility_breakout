import pandas as pd
import os
import sys

# Agregar el directorio padre al path para importar utils
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from utils.date_utils import add_day_of_week

def create_subset(start_date, end_date, output_filename=None):
    """
    Crea un subconjunto del archivo es_1min_data para un período específico

    Parameters:
    start_date (str): Fecha inicial en formato 'YYYY-MM-DD'
    end_date (str): Fecha final en formato 'YYYY-MM-DD'
    output_filename (str): Nombre del archivo de salida (opcional)

    Returns:
    DataFrame: Datos filtrados
    """

    # Cargar datos originales desde directorio data
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    data_dir = os.path.join(parent_dir, 'data')
    data_path = os.path.join(data_dir, 'es_1min_data.csv')
    print(f"Cargando datos desde: {data_path}")

    df = pd.read_csv(data_path, index_col=0, parse_dates=True)
    print(f"Datos originales: {df.shape}")
    print(f"Rango de fechas original: {df.index.min()} a {df.index.max()}")

    # Filtrar período específico
    df_filtered = df.loc[start_date:end_date].copy()

    print(f"\nDatos filtrados para {start_date} - {end_date}: {df_filtered.shape}")
    print(f"Rango de fechas filtrado: {df_filtered.index.min()} a {df_filtered.index.max()}")

    # Reset index para tener date como columna
    df_filtered = df_filtered.reset_index()

    # Añadir columna dow (day of week)
    df_filtered = add_day_of_week(df_filtered, 'date')

    print(f"Columna 'dow' añadida. Nuevas columnas: {list(df_filtered.columns)}")
    print(f"Registros antes de filtrar domingos: {len(df_filtered):,}")

    # Contar domingos antes de eliminar
    sunday_count = len(df_filtered[df_filtered['dow'] == 'sunday'])

    # Eliminar filas donde dow == "sunday"
    df_filtered = df_filtered[df_filtered['dow'] != 'sunday']

    print(f"Registros después de eliminar domingos: {len(df_filtered):,}")
    print(f"Registros de domingo eliminados: {sunday_count:,}")

    # Cargar datos diarios para merge
    daily_data_path = os.path.join(data_dir, 'es_1D_data_range.csv')
    print(f"\nCargando datos diarios desde: {daily_data_path}")

    df_daily = pd.read_csv(daily_data_path)

    # Limpiar nombres de columnas (eliminar espacios)
    df_daily.columns = df_daily.columns.str.strip()

    print(f"Columnas en archivo diario: {list(df_daily.columns)}")

    df_daily['date'] = pd.to_datetime(df_daily['date'])

    # Extraer solo la fecha (sin tiempo) para el merge
    df_filtered['date_only'] = df_filtered['date'].dt.date
    df_daily['date_only'] = df_daily['date'].dt.date

    print(f"Datos diarios cargados: {len(df_daily)} registros")
    print(f"Columnas diarias disponibles: {list(df_daily.columns)}")

    # Hacer merge usando solo la fecha
    columns_to_merge = ['date_only', 'long_level', 'short_level', 'long_stop', 'short_stop']
    df_merge = df_daily[columns_to_merge].copy()

    # Merge con los datos de 1 minuto
    df_filtered = df_filtered.merge(df_merge, on='date_only', how='left')

    # Convertir niveles a float para evitar errores de tipo
    for col in ['long_level', 'short_level', 'long_stop', 'short_stop']:
        df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce')

    # Eliminar la columna auxiliar date_only
    df_filtered = df_filtered.drop('date_only', axis=1)

    print(f"Merge completado. Nuevas columnas añadidas: long_level, short_level, long_stop, short_stop")
    print(f"Datos finales: {df_filtered.shape}")

    # Generar nombre de archivo si no se proporciona
    if output_filename is None:
        year_start = start_date[:4]
        year_end = end_date[:4]
        if year_start == year_end:
            output_filename = f'es_1min_data_{year_start}.csv'
        else:
            output_filename = f'es_1min_data_{year_start}_{year_end}.csv'

    # Guardar en directorio data
    output_path = os.path.join(data_dir, output_filename)
    df_filtered.to_csv(output_path, index=False)

    print(f"\nArchivo guardado como: {output_path}")
    print(f"Número de registros: {len(df_filtered):,}")
    print(f"Columnas guardadas: {list(df_filtered.columns)}")

    return df_filtered

def create_2022_subset():
    """
    Crea un subconjunto del archivo es_1min_data solo para el año 2022
    """
    return create_subset('2022-01-01', '2022-12-31')

if __name__ == "__main__":
    df_2022 = create_2022_subset()
    print("\n=== Primeras 5 filas ===")
    print(df_2022.head())
    print("\n=== Últimas 5 filas ===")
    print(df_2022.tail())