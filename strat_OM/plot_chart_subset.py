import os
import webbrowser
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots

def plot_subset_chart(symbol, timeframe, df, suffix='subset'):
    """
    Plot chart for subset data

    Parameters:
    symbol (str): Symbol name
    timeframe (str): Timeframe
    df (DataFrame): Data to plot
    suffix (str): Suffix for filename
    """
    html_path = f'charts/close_vol_chart_{symbol}_{timeframe}_{suffix}.html'
    os.makedirs(os.path.dirname(html_path), exist_ok=True)

    df = df.rename(columns=str.lower)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.80, 0.20],
        vertical_spacing=0.03,
    )

    # Traza de precio (línea de cierre)
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['close'],
        mode='lines',
        line=dict(color='blue', width=1.5),
        name='Close'
    ), row=1, col=1)

    # Barras de volumen
    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['volume'],
        marker_color='royalblue',
        marker_line_color='blue',
        marker_line_width=0.4,
        opacity=0.95,
        name='Volumen'
    ), row=2, col=1)

    # Añadir líneas horizontales para niveles diarios
    if 'long_level' in df.columns and 'short_level' in df.columns:
        # Agrupar por fecha (día) para obtener niveles únicos por día
        df['date_only'] = df['date'].dt.date
        daily_levels = df.groupby('date_only').agg({
            'long_level': 'first',
            'short_level': 'first',
            'date': ['min', 'max']  # Min y max timestamp del día
        }).reset_index()

        # Aplanar columnas multi-nivel
        daily_levels.columns = ['date_only', 'long_level', 'short_level', 'date_start', 'date_end']

        # Convertir long_level y short_level a float si son string
        daily_levels['long_level'] = pd.to_numeric(daily_levels['long_level'], errors='coerce')
        daily_levels['short_level'] = pd.to_numeric(daily_levels['short_level'], errors='coerce')

        # Crear líneas horizontales para cada día
        for _, row in daily_levels.iterrows():
            if not pd.isna(row['long_level']):
                # Línea verde sólida con transparencia para long_level
                fig.add_trace(go.Scatter(
                    x=[row['date_start'], row['date_end']],
                    y=[row['long_level'], row['long_level']],
                    mode='lines',
                    line=dict(color='rgba(0, 255, 0, 0.5)', width=1),
                    name=f"Long Level {row['date_only']}",
                    showlegend=False,
                    hovertemplate=f'Long Level: {row["long_level"]:.2f}<extra></extra>'
                ), row=1, col=1)

            if not pd.isna(row['short_level']):
                # Línea roja sólida con transparencia para short_level
                fig.add_trace(go.Scatter(
                    x=[row['date_start'], row['date_end']],
                    y=[row['short_level'], row['short_level']],
                    mode='lines',
                    line=dict(color='rgba(255, 0, 0, 0.5)', width=1),
                    name=f"Short Level {row['date_only']}",
                    showlegend=False,
                    hovertemplate=f'Short Level: {row["short_level"]:.2f}<extra></extra>'
                ), row=1, col=1)

        # Detectar cruces de precios con niveles (SOLO PRIMER CRUCE POR DÍA)
        crossover_points = []
        crossunder_points = []

        for _, row in daily_levels.iterrows():
            # Filtrar datos del día específico
            day_data = df[df['date_only'] == row['date_only']].copy()

            if len(day_data) > 1 and not pd.isna(row['long_level']) and not pd.isna(row['short_level']):
                day_data = day_data.sort_values('date')

                # Convertir niveles a float
                long_level = float(row['long_level'])
                short_level = float(row['short_level'])

                # Flags para controlar primer cruce del día
                first_crossover_found = False
                first_crossunder_found = False

                # Detectar SOLO el primer crossover/crossunder del día
                for i in range(1, len(day_data)):
                    prev_close = day_data.iloc[i-1]['close']
                    curr_close = day_data.iloc[i]['close']

                    # Crossover verde: SOLO el primer cruce por encima de long_level
                    if not first_crossover_found and prev_close <= long_level < curr_close:
                        crossover_points.append({
                            'date': day_data.iloc[i]['date'],
                            'price': curr_close,
                            'level': long_level
                        })
                        first_crossover_found = True

                    # Crossunder rojo: SOLO el primer cruce por debajo de short_level
                    if not first_crossunder_found and prev_close >= short_level > curr_close:
                        crossunder_points.append({
                            'date': day_data.iloc[i]['date'],
                            'price': curr_close,
                            'level': short_level
                        })
                        first_crossunder_found = True

                    # Si ya encontramos ambos cruces, no necesitamos seguir buscando
                    if first_crossover_found and first_crossunder_found:
                        break

        # Añadir puntos verdes para crossovers (TAMAÑO 8)
        if crossover_points:
            crossover_df = pd.DataFrame(crossover_points)
            fig.add_trace(go.Scatter(
                x=crossover_df['date'],
                y=crossover_df['price'],
                mode='markers',
                marker=dict(color='green', size=8, symbol='circle'),
                name='First Long Crossover',
                showlegend=False,
                hovertemplate='First Long Crossover<br>Price: %{y:.2f}<extra></extra>'
            ), row=1, col=1)

        # Añadir puntos rojos para crossunders (TAMAÑO 8)
        if crossunder_points:
            crossunder_df = pd.DataFrame(crossunder_points)
            fig.add_trace(go.Scatter(
                x=crossunder_df['date'],
                y=crossunder_df['price'],
                mode='markers',
                marker=dict(color='red', size=8, symbol='circle'),
                name='First Short Crossunder',
                showlegend=False,
                hovertemplate='First Short Crossunder<br>Price: %{y:.2f}<extra></extra>'
            ), row=1, col=1)

    # Añadir puntos de salida y líneas de conexión si tenemos datos de trading
    if 'entry_time' in df.columns and 'exit_time' in df.columns:
        # Obtener datos de entrada y salida por separado
        entry_data = df[df['entry_time'].notna()][
            ['entry_time', 'entry_price', 'trade_type']
        ].drop_duplicates()

        exit_data = df[df['exit_time'].notna()][
            ['exit_time', 'exit_price']
        ].drop_duplicates()

        # Añadir puntos de entrada (verde para BUY, rojo para SELL)
        if len(entry_data) > 0:

            # Separar BUY y SELL orders
            buy_entries = entry_data[entry_data['trade_type'] == 'BUY']
            sell_entries = entry_data[entry_data['trade_type'] == 'SELL']

            # Puntos verdes para BUY orders
            if len(buy_entries) > 0:
                fig.add_trace(go.Scatter(
                    x=buy_entries['entry_time'],
                    y=buy_entries['entry_price'],
                    mode='markers',
                    marker=dict(color='green', size=10, symbol='circle'),
                    name='BUY Entry Points',
                    showlegend=False,
                    hovertemplate='BUY Entry<br>Price: %{y:.2f}<br>Time: %{x}<extra></extra>'
                ), row=1, col=1)

            # Puntos rojos para SELL orders
            if len(sell_entries) > 0:
                fig.add_trace(go.Scatter(
                    x=sell_entries['entry_time'],
                    y=sell_entries['entry_price'],
                    mode='markers',
                    marker=dict(color='red', size=10, symbol='circle'),
                    name='SELL Entry Points',
                    showlegend=False,
                    hovertemplate='SELL Entry<br>Price: %{y:.2f}<br>Time: %{x}<extra></extra>'
                ), row=1, col=1)

        # Añadir puntos de salida (cuadrados negros)
        if len(exit_data) > 0:
            fig.add_trace(go.Scatter(
                x=exit_data['exit_time'],
                y=exit_data['exit_price'],
                mode='markers',
                marker=dict(color='black', size=8, symbol='square'),
                name='Exit Points',
                showlegend=False,
                hovertemplate='Exit Point<br>Price: %{y:.2f}<br>Time: %{x}<extra></extra>'
            ), row=1, col=1)

        # Para las líneas de conexión, necesitamos reconstruir los pares entry/exit
        if len(entry_data) > 0 and len(exit_data) > 0:
            # Crear un DataFrame temporal para matchear entradas y salidas por tiempo
            temp_df = df[['date', 'entry_time', 'entry_price', 'exit_time', 'exit_price', 'trade_type']].copy()

            # Buscar pares de entrada/salida válidos
            entry_times = temp_df[temp_df['entry_time'].notna()]['entry_time'].unique()
            exit_times = temp_df[temp_df['exit_time'].notna()]['exit_time'].unique()

            # Para cada entrada, buscar su salida correspondiente
            for entry_time in entry_times:
                entry_row = temp_df[temp_df['entry_time'] == entry_time].iloc[0]
                entry_price = entry_row['entry_price']

                # Buscar la salida más cercana después de la entrada
                future_exits = temp_df[(temp_df['exit_time'].notna()) &
                                     (temp_df['exit_time'] > entry_time)]

                if len(future_exits) > 0:
                    exit_row = future_exits.iloc[0]  # Tomar la primera salida después de la entrada
                    exit_time = exit_row['exit_time']
                    exit_price = exit_row['exit_price']

                    # Añadir línea de conexión con puntos pequeños
                    fig.add_trace(go.Scatter(
                        x=[entry_time, exit_time],
                        y=[entry_price, exit_price],
                        mode='lines',
                        line=dict(color='grey', width=1, dash='dot'),
                        name=f"Trade Line",
                        showlegend=False,
                        hoverinfo='skip'
                    ), row=1, col=1)

    fig.update_layout(
        dragmode='pan',
        title=f'{symbol}_{timeframe}_{suffix}',
        width=1500,
        height=700,
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(size=12, color="black"),
        plot_bgcolor='rgba(255,255,255,0.05)',
        paper_bgcolor='rgba(240,240,240,0.1)',
        showlegend=False,
        template='plotly_white',
        xaxis=dict(
            type='date',
            tickformat="%b %d<br>%Y",
            tickangle=0,
            showgrid=False,
            linecolor='gray',
            linewidth=1,
            range=[df['date'].min(), df['date'].max()],
            # Ocultar fines de semana para evitar líneas de conexión
            rangebreaks=[
                dict(bounds=["sat", "mon"]),  # Ocultar desde sábado hasta lunes
            ]
        ),
        yaxis=dict(showgrid=True, linecolor='gray', linewidth=1),
        xaxis2=dict(
            type='date',
            tickformat="%b %d<br>%Y",
            tickangle=45,
            showgrid=False,
            linecolor='gray',
            linewidth=1,
            range=[df['date'].min(), df['date'].max()],
            # Ocultar fines de semana para evitar líneas de conexión
            rangebreaks=[
                dict(bounds=["sat", "mon"]),  # Ocultar desde sábado hasta lunes
            ]
        ),
        yaxis2=dict(showgrid=True, linecolor='grey', linewidth=1),
    )

    fig.write_html(html_path, config={"scrollZoom": True})
    print(f"Grafico Subset Plotly guardado como HTML: '{html_path}'")

    webbrowser.open('file://' + os.path.realpath(html_path))

def plot_2022_data():
    """
    Función específica para plotear datos de 2022
    """
    # Cargar datos de 2022 - usar ruta absoluta
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    data_path = os.path.join(parent_dir, 'data', 'es_1min_data_2022.csv')

    print(f"Cargando datos desde: {data_path}")
    df = pd.read_csv(data_path)

    # Convertir columna date a datetime si no lo está
    df['date'] = pd.to_datetime(df['date'])

    print(f"Datos cargados: {df.shape}")
    print(f"Período: {df['date'].min()} a {df['date'].max()}")

    # Plotear
    plot_subset_chart('ES', '1min', df, '2022')

if __name__ == "__main__":
    plot_2022_data()