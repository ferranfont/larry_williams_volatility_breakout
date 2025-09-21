import pandas as pd
import os
from create_2022_subset import create_subset
from plot_chart_subset import plot_subset_chart
from order_management import order_management, save_trading_results

def main():
    """
    Script principal para crear subconjuntos de datos y ejecutar estrategias
    """
    # ======================================================================================================


    # Filtro de día de la semana 
    start_date = '2024-08-15'
    end_date =   '2025-04-13'

    # dow (day of week, dia de la semana) 
    dow_filter = 0 # (0=sin filtro, 1=lunes, 2=martes, 3=miércoles, 4=jueves, 5=viernes)
    
  
    # ======================================================================================================

    print("=== CREACIÓN DE SUBSET DE DATOS ===")
    print(f"Período: {start_date} a {end_date}")

    # Crear subset de datos
    df_subset = create_subset(start_date, end_date)

    print(f"\n=== DATOS CARGADOS ===")
    print(f"Shape: {df_subset.shape}")
    print(f"Columns: {list(df_subset.columns)}")

    print(f"\n=== PRIMERAS 10 FILAS ===")
    print(df_subset.head(10))

    print(f"\n=== ÚLTIMAS 10 FILAS ===")
    print(df_subset.tail(10))

    print(f"\n=== INFORMACIÓN DEL DATASET ===")
    print(df_subset.info())

    # Ejecutar sistema de trading
    print(f"\n=== EJECUTANDO SISTEMA DE TRADING ===")
    if dow_filter > 0:
        dow_names = {1: 'lunes', 2: 'martes', 3: 'miércoles', 4: 'jueves', 5: 'viernes'}
        print(f"Filtro activo: Solo operar en {dow_names.get(dow_filter, 'desconocido')}")
    else:
        print("Sin filtro de día de la semana: operar todos los días")

    trades_df, df_with_trades = order_management(df_subset, dow_filter=dow_filter)

    # Generar gráfico con datos de trading (lo último)
    print(f"\n=== GENERANDO GRÁFICO CON TRADES ===")
    plot_subset_chart('ES', '1min', df_with_trades, 'trades')

    # Guardar resultados de trading
    if len(trades_df) > 0:
        print(f"\n=== GUARDANDO RESULTADOS ===")
        tracking_filename = save_trading_results(trades_df, start_date, end_date)

        print(f"\n=== PRIMEROS 10 TRADES ===")
        print(trades_df.head(20))
    else:
        print("No se generaron trades en el período analizado")

    # Aquí puedes agregar más lógica de estrategia
    print(f"\n=== SUBSET CREADO EXITOSAMENTE ===")
    print(f"Datos disponibles para estrategias en período {start_date} - {end_date}")
    print(f"Gráfico interactivo generado con rangebreaks para eliminar fines de semana")
    print(f"Sistema de trading ejecutado y resultados guardados")

if __name__ == "__main__":
    main()