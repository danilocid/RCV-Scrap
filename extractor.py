"""
Módulo de extracción y orquestación del scraping
"""
import time
import logging
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

logger = logging.getLogger("extractor")


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
    logger.info("Ejecutando en modo: %s", AMBIENTE)
    
    # Si no se proporcionan mes y año, usar los actuales
    from datetime import datetime
    if mes is None:
        mes = datetime.now().month
        logger.info("Mes no especificado, usando mes actual: %d", mes)
    if anio is None:
        anio = datetime.now().year
        logger.info("Año no especificado, usando año actual: %d", anio)
    
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
    logger.info("Período a consultar: %s", periodo)
    
    with sync_playwright() as p:
        # Configurar navegador
        headless = AMBIENTE != "DEV"
        logger.info("Iniciando navegador Chromium (headless=%s)...", headless)
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.set_default_timeout(DEFAULT_TIMEOUT)
        logger.debug("Página creada con timeout de %d ms", DEFAULT_TIMEOUT)
        
        # Login en el SII
        logger.info("Iniciando proceso de login en SII...")
        login_exitoso = login_sii(page, RUT, CLAVE)
        if not login_exitoso:
            logger.error("Login fallido: credenciales incorrectas")
            raise Exception("Credenciales incorrectas. Verifica tu RUT y contraseña.")
        
        # Navegar al RCV y seleccionar período
        logger.info("Navegando al módulo RCV...")
        navegar_a_rcv(page, mes, anio)
        
        # Obtener tipos de documentos disponibles de la tabla de resumen
        logger.info("Obteniendo tipos de documentos disponibles...")
        tipos_disponibles = obtener_tipos_documento_disponibles(page)
        
        if not tipos_disponibles:
            logger.warning("No se encontraron tipos de documentos disponibles para el período %s", periodo)
            browser.close()
            return None
        
        # Si el usuario especificó tipos, filtrar solo los que están disponibles
        if tipos_documento is not None:
            tipos_a_procesar = [td for td in tipos_documento if td in tipos_disponibles]
            tipos_no_disponibles = [td for td in tipos_documento if td not in tipos_disponibles]
            
            if tipos_no_disponibles:
                logger.warning("Los siguientes tipos NO están disponibles para el período: %s", ', '.join(tipos_no_disponibles))
            
            if not tipos_a_procesar:
                logger.warning("Ninguno de los tipos especificados está disponible para el período %s", periodo)
                browser.close()
                return None
            
            logger.info("Procesando tipos especificados que están disponibles: %s", ', '.join(tipos_a_procesar))
        else:
            # Si no se especificaron tipos, usar todos los disponibles
            tipos_a_procesar = tipos_disponibles
            logger.info("Procesando TODOS los tipos disponibles: %s", ', '.join(tipos_a_procesar))
        
        # Extraer datos para cada tipo de documento disponible
        todos_los_datos = []
        total_tipos = len(tipos_a_procesar)
        
        for idx, tipo_doc in enumerate(tipos_a_procesar, 1):
            logger.info("="*60)
            logger.info("Procesando tipo %d/%d: %s - %s", idx, total_tipos, tipo_doc, TIPOS_DOCUMENTO.get(tipo_doc, 'Desconocido'))
            logger.info("="*60)
            
            # Navegar al detalle del tipo de documento
            logger.info("Navegando al detalle del tipo %s...", tipo_doc)
            navegar_a_detalle_tipo(page, tipo_doc)
            
            # Extraer datos
            logger.info("Extrayendo datos del tipo %s...", tipo_doc)
            datos_extraidos = extraer_datos_tablas(page)
            
            # Agregar tipo de documento a cada registro
            for registro in datos_extraidos:
                registro['Tipo Documento'] = tipo_doc
                registro['Nombre Tipo Documento'] = TIPOS_DOCUMENTO.get(tipo_doc, 'Desconocido')
            
            todos_los_datos.extend(datos_extraidos)
            logger.info("Extraídos %d registros del tipo %s", len(datos_extraidos), tipo_doc)
            
            # Volver a la pantalla de resumen antes de continuar con el siguiente tipo
            # (excepto en el último tipo)
            if idx < total_tipos:
                logger.info("Volviendo a resumen antes de procesar siguiente tipo...")
                volver_a_resumen(page)
        
        datos_extraidos = todos_los_datos
        
        # Procesar y guardar datos
        if datos_extraidos:
            logger.info("Procesando datos finales...")
            logger.info("Total de registros antes de eliminar duplicados: %d", len(datos_extraidos))
            
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
            logger.info("Guardando datos en JSON: %s", ARCHIVO_JSON)
            guardar_datos_json(datos_completos, ARCHIVO_JSON)
            
            # Guardar en Excel
            if datos_completos["datos"]:
                df_final = pd.DataFrame(datos_completos["datos"])
                logger.info("Guardando datos en Excel: %s", ARCHIVO_EXCEL)
                guardar_datos_excel([df_final], ARCHIVO_EXCEL)
            
            logger.info("Total de registros únicos guardados: %d", len(datos_completos['datos']))
            logger.info("Extracción completada exitosamente")
            return datos_completos
        else:
            logger.warning("No se extrajeron datos de ninguna tabla")
            return None
        
        browser.close()
