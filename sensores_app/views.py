from django.shortcuts import render
from django.conf import settings
import os
import pandas as pd
import json

# Ruta al archivo CSV
RUTA_DATOS = os.path.join(settings.BASE_DIR, 'sensores_app', 'sensores2.csv')


# ====================
# Función para cargar y procesar los datos
# ====================
def cargar_datos():
    if not os.path.exists(RUTA_DATOS):
        raise FileNotFoundError(f"No se encontró el archivo: {RUTA_DATOS}")

    df = pd.read_csv(RUTA_DATOS, sep=',', encoding='utf-8')
    df.columns = df.columns.str.strip()
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    df.dropna(subset=['fecha'], inplace=True)

    if df['anomaly'].dtype != bool:
        df['anomaly'] = df['anomaly'].astype(bool)

    df['mes'] = df['fecha'].dt.to_period('M').astype(str)

    promedios_no_anomalias = (
        df[df['anomaly'] == False]
        .groupby('mes')['promediohora']
        .mean()
        .reset_index()
        .rename(columns={'promediohora': 'promedio_no_anomalias'})
    )

    promedios_anomalias = (
        df[df['anomaly'] == True]
        .groupby('mes')['promediohora']
        .mean()
        .reset_index()
        .rename(columns={'promediohora': 'promedio_anomalias'})
    )

    df_comparacion = pd.merge(promedios_no_anomalias, promedios_anomalias, on='mes', how='outer').fillna(0)

    return df_comparacion.to_dict(orient='records'), df.shape[0], df['anomaly'].sum()


# ====================
# Vista principal (home)
# ====================
def home(request):
    error_msgs = []
    try:
        datos_grafica, total_lecturas, total_anomalias = cargar_datos()
        datos_por_sensor, meses = obtener_promedios_por_sensor()

        # Formato para Chart.js
        datasets = []
        for sensor, valores_dict in datos_por_sensor.items():
            data = [valores_dict.get(m, 0) for m in meses]
            datasets.append({
                'label': sensor,
                'data': data,
                'fill': False,
                'borderWidth': 2,
                'tension': 0.3
            })

    except Exception as e:
        error_msgs.append(f"Error inesperado: {str(e)}")
        datos_grafica = []
        total_lecturas = total_anomalias = 0
        meses = []
        datasets = []

    context = {
        'datos_grafica': json.dumps(datos_grafica),
        'total_lecturas': total_lecturas,
        'total_anomalias': total_anomalias,
        'meses_json': json.dumps(meses),
        'sensor_datasets_json': json.dumps(datasets),
        'error_msgs': error_msgs,
    }
    return render(request, 'sensores_app/home.html', context)


# ====================
# Vista de anomalías
# ====================
def ver_anomalias(request):
    error_msgs = []
    tabla_html = ""

    try:
        if not os.path.exists(RUTA_DATOS):
            raise FileNotFoundError(f"No se encontró el archivo: {RUTA_DATOS}")

        df = pd.read_csv(RUTA_DATOS, sep=',', encoding='utf-8')
        df.columns = df.columns.str.strip()
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        df.dropna(subset=['fecha'], inplace=True)

        if df['anomaly'].dtype != bool:
            df['anomaly'] = df['anomaly'].astype(bool)

        df_anomalias = df[df['anomaly'] == True].copy()
        df_anomalias['mes'] = df_anomalias['fecha'].dt.to_period('M').astype(str)

        zonas = [col for col in df.columns if col not in ['fecha', 'hora', 'promediohora', 'promedio_zonas', 'anomaly', 'mes']]

        resumen = []
        for zona in zonas:
            df_temp = df_anomalias.groupby('mes')[zona].apply(lambda x: (x > 0).sum()).reset_index()
            df_temp.columns = ['mes', 'total_anomalias']
            df_temp['zona'] = zona
            resumen.append(df_temp)

        df_resumen = pd.concat(resumen)

        # Datos para gráfica de anomalías
        df_grafica = df_resumen.groupby('mes')['total_anomalias'].sum().reset_index()
        meses = df_grafica['mes'].tolist()
        valores = df_grafica['total_anomalias'].tolist()

        # Renombrar columnas para tabla
        df_resumen.rename(columns={
            'mes': 'Mes',
            'zona': 'Zona',
            'total_anomalias': 'Total de Anomalías'
        }, inplace=True)

        tabla_html = df_resumen.to_html(
            classes='display table table-striped table-bordered',
            index=False,
            table_id='tablaAnomalias'
        )

        # Agregar gráfica de promedios por sensor
        datos_por_sensor, meses_promedios = obtener_promedios_por_sensor()

        datasets = []
        for sensor, valores_dict in datos_por_sensor.items():
            data = [valores_dict.get(m, 0) for m in meses_promedios]
            datasets.append({
                'label': sensor,
                'data': data,
                'fill': False,
                'borderWidth': 2,
                'tension': 0.3
            })

    except Exception as e:
        error_msgs.append(f"Error inesperado: {str(e)}")
        meses = []
        valores = []
        meses_promedios = []
        datasets = []

    return render(request, 'sensores_app/anomalias.html', {
        'tabla_anomalias': tabla_html,
        'error_msgs': error_msgs,
        'meses_json': json.dumps(meses),
        'valores_json': json.dumps(valores),
        'meses_promedios_json': json.dumps(meses_promedios),
        'sensor_datasets_json': json.dumps(datasets),
    })


# ====================
# Función de ayuda
# ====================
def obtener_promedios_por_sensor():
    if not os.path.exists(RUTA_DATOS):
        raise FileNotFoundError(f"No se encontró el archivo: {RUTA_DATOS}")

    df = pd.read_csv(RUTA_DATOS, sep=',', encoding='utf-8')
    df.columns = df.columns.str.strip()
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    df.dropna(subset=['fecha'], inplace=True)
    df['mes'] = df['fecha'].dt.to_period('M').astype(str)

    sensores = [col for col in df.columns if col not in ['fecha', 'hora', 'promediohora', 'promedio_zonas', 'anomaly', 'mes']]

    datos = {}
    for sensor in sensores:
        df_sensor = df.groupby('mes')[sensor].mean().reset_index()
        datos[sensor] = df_sensor.set_index('mes')[sensor].round(2).to_dict()

    meses = sorted(set(df['mes']))

    return datos, meses
