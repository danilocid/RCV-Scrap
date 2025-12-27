"""
Módulo de extracción y orquestación del scraping
"""
import time
import pandas as pd
from playwright.sync_api import sync_playwright

from config import (
    RUT, CLAVE, AMBIENTE,
    ARCHIVO_JSON, ARCHIVO_EXCEL, DEFAULT_TIMEOUT,
    validar_configuracion
)
from scraper import (
    login_sii, navegar_a_rcv, obtener_tipos_documento_disponibles, 
    navegar_a_detalle_tipo, extraer_datos_tablas, volver_a_resumen
)
from procesador import eliminar_duplicados
from guardador import guardar_datos_json, guardar_datos_excel


def ejecutar_scraping(mes=None, anio=None, tipos_documento=None):
    """
    Ejecuta el proceso de scraping completo
    
    Args:
        mes: Mes para filtrar (1-12). Si es None, usa el mes actual
        anio: Año para filtrar (ej: 2025). Si es None, usa el año actual
        tipos_documento: Lista de códigos de tipos de documento (ej: ["33", "39"]), None para TODOS los tipos
    
    Returns:
        dict: Datos extraídos y procesados
    """
    print(f"Ejecutando en modo: {AMBIENTE}")
    
    # Si no se proporcionan mes y año, usar los actuales
    from datetime import datetime
    if mes is None:
        mes = datetime.now().month
        print(f"ℹ️  Mes no especificado, usando mes actual: {mes}")
    if anio is None:
        anio = datetime.now().year
        print(f"ℹ️  Año no especificado, usando año actual: {anio}")
    
    # Validar mes y año
    if not (1 <= mes <= 12):
        raise ValueError("El mes debe estar entre 1 y 12")
    
    if not (2000 <= anio <= 2100):
        raise ValueError("El año debe estar entre 2000 y 2100")
    
    # Validar configuración
    validar_configuracion()
    
    # Importar TIPOS_DOCUMENTO para mostrar nombres
    from config import TIPOS_DOCUMENTO
    
    # Mostrar información de la consulta
    periodo = f"{mes:02d}/{anio}"
    print(f"📅 Período: {periodo}")
    
    with sync_playwright() as p:
        # Configurar navegador
        headless = AMBIENTE != "DEV"
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.set_default_timeout(DEFAULT_TIMEOUT)
        
        # Login en el SII
        login_exitoso = login_sii(page, RUT, CLAVE)
        if not login_exitoso:
            raise Exception("Credenciales incorrectas. Verifica tu RUT y contraseña.")
        
        # Navegar al RCV y seleccionar período
        navegar_a_rcv(page, mes, anio)
        
        # Obtener tipos de documentos disponibles de la tabla de resumen
        tipos_disponibles = obtener_tipos_documento_disponibles(page)
        
        if not tipos_disponibles:
            print("\n⚠ No se encontraron tipos de documentos disponibles para el período especificado")
            browser.close()
            return None
        
        # Si el usuario especificó tipos, filtrar solo los que están disponibles
        if tipos_documento is not None:
            tipos_a_procesar = [td for td in tipos_documento if td in tipos_disponibles]
            tipos_no_disponibles = [td for td in tipos_documento if td not in tipos_disponibles]
            
            if tipos_no_disponibles:
                print(f"\n⚠ Los siguientes tipos NO están disponibles para el período: {', '.join(tipos_no_disponibles)}")
            
            if not tipos_a_procesar:
                print("\n⚠ Ninguno de los tipos especificados está disponible para el período")
                browser.close()
                return None
            
            print(f"\n📄 Procesando tipos especificados que están disponibles: {', '.join(tipos_a_procesar)}")
        else:
            # Si no se especificaron tipos, usar todos los disponibles
            tipos_a_procesar = tipos_disponibles
            print(f"\n📄 Procesando TODOS los tipos disponibles: {', '.join(tipos_a_procesar)}")
        
        # Extraer datos para cada tipo de documento disponible
        todos_los_datos = []
        total_tipos = len(tipos_a_procesar)
        
        for idx, tipo_doc in enumerate(tipos_a_procesar, 1):
            print(f"\n{'='*60}")
            print(f"Procesando tipo {idx}/{total_tipos}: {tipo_doc} - {TIPOS_DOCUMENTO.get(tipo_doc, 'Desconocido')}")
            print(f"{'='*60}")
            
            # Navegar al detalle del tipo de documento
            navegar_a_detalle_tipo(page, tipo_doc)
            
            # Extraer datos
            datos_extraidos = extraer_datos_tablas(page)
            
            # Agregar tipo de documento a cada registro
            for registro in datos_extraidos:
                registro['Tipo Documento'] = tipo_doc
                registro['Nombre Tipo Documento'] = TIPOS_DOCUMENTO.get(tipo_doc, 'Desconocido')
            
            todos_los_datos.extend(datos_extraidos)
            print(f"✓ Extraídos {len(datos_extraidos)} registros del tipo {tipo_doc}")
            
            # Volver a la pantalla de resumen antes de continuar con el siguiente tipo
            # (excepto en el último tipo)
            if idx < total_tipos:
                volver_a_resumen(page)
        
        datos_extraidos = todos_los_datos
        
        # Procesar y guardar datos
        if datos_extraidos:
            print(f"\n📊 Procesando datos finales...")
            print(f"  Total de registros antes de eliminar duplicados: {len(datos_extraidos)}")
            
            # Crear estructura de datos
            datos_completos = {
                "fecha_extraccion": time.strftime("%Y-%m-%d %H:%M:%S"),
                "periodo": {
                    "mes": mes,
                    "anio": anio
                },
                "tipos_documento_procesados": tipos_a_procesar,
                "datos": eliminar_duplicados(datos_extraidos)
            }
            
            # Guardar en JSON
            guardar_datos_json(datos_completos, ARCHIVO_JSON)
            
            # Guardar en Excel
            if datos_completos["datos"]:
                df_final = pd.DataFrame(datos_completos["datos"])
                guardar_datos_excel([df_final], ARCHIVO_EXCEL)
            
            print(f"\n✓ Total de registros únicos guardados: {len(datos_completos['datos'])}")
            return datos_completos
        else:
            print("\n⚠ No se extrajeron datos de ninguna tabla")
            return None
        
        browser.close()
