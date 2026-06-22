"""
Módulo de procesamiento y limpieza de datos
"""
import logging
import pandas as pd

logger = logging.getLogger("procesador")


def limpiar_registro(registro):
    """
    Limpia un registro eliminando claves con valores vacíos, NaN o None
    """
    registro_limpio = {}
    for key, value in registro.items():
        # Verificar si el valor no es NaN, None, vacío o "NaN" como string
        if pd.notna(value) and value != "" and value != "NaN":
            registro_limpio[key] = value
    return registro_limpio


def eliminar_duplicados(datos):
    """
    Elimina registros duplicados basándose en Folio únicamente
    """
    try:
        if not datos:
            logger.debug("No hay datos para procesar duplicados")
            return []
        
        registros_iniciales = len(datos)
        logger.info("Procesando %d registros para eliminar duplicados...", registros_iniciales)
        
        # Usar un diccionario para rastrear folios únicos
        folios_vistos = {}
        registros_unicos = []
        
        for registro in datos:
            folio = registro.get('Folio')
            if folio and folio not in folios_vistos:
                # Limpiar el registro antes de agregarlo
                registro_limpio = limpiar_registro(registro)
                if registro_limpio:  # Solo agregar si tiene datos después de limpiar
                    registros_unicos.append(registro_limpio)
                    folios_vistos[folio] = True
        
        registros_finales = len(registros_unicos)
        duplicados_eliminados = registros_iniciales - registros_finales
        
        if duplicados_eliminados > 0:
            logger.warning("%d registros duplicados eliminados", duplicados_eliminados)
        
        logger.info("%d registros únicos obtenidos", registros_finales)
        
        return registros_unicos
    except Exception as e:
        logger.error("Error al eliminar duplicados: %s", str(e))
        return datos


def mostrar_datos_ordenados(datos_tabla, numero_tabla):
    """
    Muestra los datos en formato tabular ordenado usando pandas
    """
    try:
        if not datos_tabla:
            logger.warning("Tabla %d: Sin datos para mostrar", numero_tabla)
            return None
        
        # Convertir a DataFrame de pandas
        df = pd.DataFrame(datos_tabla)
        
        # Configurar pandas para mostrar todas las columnas
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 50)
        
        logger.info("="*80)
        logger.info("TABLA %d - Total de registros: %d", numero_tabla, len(df))
        logger.info("="*80)
        logger.info("Columnas: %s", ', '.join(df.columns.tolist()))
        logger.debug("\n%s", df.to_string(index=True))
        logger.info("="*80)
        
        return df
    except Exception as e:
        logger.error("Error al mostrar datos de tabla %d: %s", numero_tabla, str(e))
        return None
