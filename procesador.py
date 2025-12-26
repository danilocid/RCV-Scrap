"""
Módulo de procesamiento y limpieza de datos
"""
import pandas as pd


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
            return []
        
        registros_iniciales = len(datos)
        
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
            print(f"  ⚠ {duplicados_eliminados} registros duplicados eliminados")
        
        print(f"  ✓ {registros_finales} registros únicos")
        
        return registros_unicos
    except Exception as e:
        print(f"  ❌ Error al eliminar duplicados: {str(e)}")
        return datos


def mostrar_datos_ordenados(datos_tabla, numero_tabla):
    """
    Muestra los datos en formato tabular ordenado usando pandas
    """
    try:
        if not datos_tabla:
            print(f"  ⚠ Tabla {numero_tabla}: Sin datos")
            return None
        
        # Convertir a DataFrame de pandas
        df = pd.DataFrame(datos_tabla)
        
        # Configurar pandas para mostrar todas las columnas
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 50)
        
        print(f"\n{'='*80}")
        print(f"TABLA {numero_tabla} - Total de registros: {len(df)}")
        print(f"{'='*80}")
        print(f"\nColumnas: {', '.join(df.columns.tolist())}")
        print(f"\n{df.to_string(index=True)}")
        print(f"{'='*80}\n")
        
        return df
    except Exception as e:
        print(f"  ❌ Error al mostrar datos: {str(e)}")
        return None
