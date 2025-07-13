from django.shortcuts import render
from django.conf import settings
import os
import pandas as pd
import json


# Ruta al archivo CSV
RUTA_DATOS = os.path.join(settings.BASE_DIR, 'sensores_app', 'sensores2.csv')

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

    promedios_no_anomalias = df[df['anomaly'] == False].groupby('mes')['promediohora'].mean().reset_index()
    promedios_no_anomalias.rename(columns={'promediohora': 'promedio_no_anomalias'}, inplace=True)

    promedios_anomalias = df[df['anomaly'] == True].groupby('mes')['promediohora'].mean().reset_index()
    promedios_anomalias.rename(columns={'promediohora': 'promedio_anomalias'}, inplace=True)

    df_comparacion = pd.merge(promedios_no_anomalias, promedios_anomalias, on='mes', how='outer').fillna(0)

    return df_comparacion.to_dict(orient='records'), df.shape[0], df['anomaly'].sum()

def home(request):
    error_msgs = []
    try:
        datos_grafica, total_lecturas, total_anomalias = cargar_datos()
    except Exception as e:
        error_msgs.append(f"Error inesperado: {str(e)}")
        datos_grafica = []
        total_lecturas = 0
        total_anomalias = 0

    context = {
        'datos_grafica': json.dumps(datos_grafica),
        'total_lecturas': total_lecturas,
        'total_anomalias': total_anomalias,
        'error_msgs': error_msgs,
    }
    return render(request, 'sensores_app/home.html', context)


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

# Renombrar columnas para que salgan en español
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

    except Exception as e:
        error_msgs.append(f"Error inesperado: {str(e)}")

    return render(request, 'sensores_app/anomalias.html', {
        'tabla_anomalias': tabla_html,
        'error_msgs': error_msgs
    })