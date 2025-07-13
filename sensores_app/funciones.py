rom django.shortcuts import render
import os
import pandas as pd
import json

RUTA_DATOS = r'D:\personal\tech\IA.Exploradores _sabaneta\Machine Learning\proyecto_sensores\sensores2.csv'

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
