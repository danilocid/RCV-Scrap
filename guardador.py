"""
Módulo de exportación de datos
"""
import json
import pandas as pd


def guardar_datos_json(datos, nombre_archivo="datos_rcv.json"):
    """
    Guarda los datos en un archivo JSON
    """
    try:
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        print(f"✓ Datos guardados en: {nombre_archivo}")
    except Exception as e:
        print(f"❌ Error al guardar JSON: {str(e)}")


def guardar_datos_excel(dataframes, nombre_archivo="datos_rcv.xlsx"):
    """
    Guarda los datos en un archivo Excel con múltiples hojas
    """
    try:
        with pd.ExcelWriter(nombre_archivo, engine='openpyxl') as writer:
            for idx, df in enumerate(dataframes):
                if df is not None and not df.empty:
                    df.to_excel(writer, sheet_name=f'Tabla_{idx+1}', index=False)
        print(f"✓ Datos guardados en Excel: {nombre_archivo}")
    except Exception as e:
        print(f"❌ Error al guardar Excel: {str(e)}")
