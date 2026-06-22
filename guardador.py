"""
Módulo de exportación de datos
"""
import json
import logging
import pandas as pd

logger = logging.getLogger("guardador")


def guardar_datos_json(datos, nombre_archivo="datos_rcv.json"):
    """
    Guarda los datos en un archivo JSON
    """
    try:
        logger.info("Guardando datos en JSON: %s", nombre_archivo)
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        logger.info("Datos guardados exitosamente en: %s", nombre_archivo)
    except Exception as e:
        logger.error("Error al guardar JSON: %s", str(e))


def guardar_datos_excel(dataframes, nombre_archivo="datos_rcv.xlsx"):
    """
    Guarda los datos en un archivo Excel con múltiples hojas
    """
    try:
        logger.info("Guardando datos en Excel: %s", nombre_archivo)
        with pd.ExcelWriter(nombre_archivo, engine='openpyxl') as writer:
            for idx, df in enumerate(dataframes):
                if df is not None and not df.empty:
                    df.to_excel(writer, sheet_name=f'Tabla_{idx+1}', index=False)
        logger.info("Datos guardados exitosamente en Excel: %s", nombre_archivo)
    except Exception as e:
        logger.error("Error al guardar Excel: %s", str(e))
