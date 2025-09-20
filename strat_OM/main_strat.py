import pandas as pd
import os
from create_2022_subset import create_subset
from plot_chart_subset import plot_subset_chart
from order_management import order_management, save_trading_results

def main():
    """
    Script principal para crear subconjuntos de datos y ejecutar estrategias
    """

    # Parámetros de fechas
    start_date = '2022-01-01'
    end_date = '2022-03-31'

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
    trades_df, df_with_trades = order_management(df_subset)

    # Generar gráfico con datos de trading (lo último)
    print(f"\n=== GENERANDO GRÁFICO CON TRADES ===")
    plot_subset_chart('ES', '1min', df_with_trades, 'trades')

    # Guardar resultados de trading
    if len(trades_df) > 0:
        print(f"\n=== GUARDANDO RESULTADOS ===")
        tracking_filename = save_trading_results(trades_df, start_date, end_date)

        print(f"\n=== PRIMEROS 10 TRADES ===")
        print(trades_df.head(10))
    else:
        print("No se generaron trades en el período analizado")

    # Aquí puedes agregar más lógica de estrategia
    print(f"\n=== SUBSET CREADO EXITOSAMENTE ===")
    print(f"Datos disponibles para estrategias en período {start_date} - {end_date}")
    print(f"Gráfico interactivo generado con rangebreaks para eliminar fines de semana")
    print(f"Sistema de trading ejecutado y resultados guardados")

if __name__ == "__main__":
    main()