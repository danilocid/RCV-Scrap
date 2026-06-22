"""
Módulo de extracción de datos del portal SII
"""
import time
import re
import logging
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from config import *

logger = logging.getLogger("scraper")


def login_sii(page, rut, clave):
    """
    Realiza el login en el portal del SII
    """
    logger.info("Accediendo al portal del SII en %s", URL_LOGIN_SII)
    try:
        page.goto(URL_LOGIN_SII, timeout=60000)
    except PlaywrightTimeoutError:
        logger.error("Timeout al acceder al portal del SII en %s", URL_LOGIN_SII)
        raise
    logger.info("Página de login cargada correctamente")

    # Click en "Ingresar a Mi SII"
    logger.info("Haciendo clic en 'Ingresar a Mi SII'")
    try:
        page.click("text=Ingresar a Mi SII", timeout=30000)
    except PlaywrightTimeoutError:
        logger.error("Timeout al hacer clic en 'Ingresar a Mi SII'")
        raise
    time.sleep(SLEEP_MEDIUM)
    logger.debug("Formulario de credenciales visible")
    
    # Completar RUT y clave
    logger.info("Ingresando credenciales para RUT: %s", rut[:7] + "***")
    page.fill('input[name="rutcntr"]', rut)
    time.sleep(SLEEP_MEDIUM)
    page.fill('input[name="clave"]', clave)
    time.sleep(SLEEP_MEDIUM)
    logger.debug("Credenciales completadas")

    # Enviar formulario
    logger.info("Enviando formulario de login...")
    page.click('button[id="bt_ingresar"]')
    time.sleep(SLEEP_LONG)
    logger.debug("Formulario enviado, esperando respuesta del servidor")
    
    # Verificar si hay error de login
    try:
        logger.debug("Verificando si hay mensaje de error de login...")
        error_element = page.wait_for_selector(
            "text=/contraseña.*incorrecta|rut.*inválido|error/i", 
            timeout=3000
        )
        if error_element:
            logger.error("Login fallido: credenciales incorrectas")
            return False
    except PlaywrightTimeoutError:
        # No hay mensaje de error, el login fue exitoso
        logger.debug("No se detectaron errores de login")
    
    logger.info("Login exitoso en el portal SII")
    page.wait_for_load_state("networkidle")
    logger.debug("Página en estado idle después del login")
    return True


def navegar_a_rcv(page, mes=None, anio=None):
    """
    Navega al módulo RCV y selecciona el período si se proporciona
    
    Args:
        page: Objeto page de Playwright
        mes: Mes para filtrar (1-12), None para mes actual
        anio: Año para filtrar (ej: 2025), None para año actual
    """
    logger.info("Navegando al módulo RCV en %s", URL_RCV)
    try:
        page.goto(URL_RCV, timeout=60000)
    except PlaywrightTimeoutError:
        logger.error("Timeout al acceder al módulo RCV en %s", URL_RCV)
        raise
    logger.info("Página RCV cargada correctamente")

    logger.info("Haciendo clic en botón de ingreso al RCV...")
    time.sleep(SLEEP_EXTRA_LONG)
    page.click('button[class="btn btn-default btn-xs-block btn-block"]')
    logger.debug("Botón clickeado, esperando carga del módulo")
    time.sleep(3)
    page.wait_for_load_state("networkidle")
    logger.debug("Módulo RCV cargado y en estado idle")
    
    # Si se proporcionan mes y año, intentar seleccionarlos
    if mes and anio:
        logger.info("Intentando seleccionar período: %02d/%d...", mes, anio)
        try:
            # Esperar a que los selectores de período estén disponibles
            logger.debug("Esperando selector de mes...")
            page.wait_for_selector('select#periodoMes', timeout=5000)
            
            # Seleccionar mes (formato con cero al inicio: "01", "02", etc.)
            mes_formateado = f"{mes:02d}"
            page.select_option('select#periodoMes', mes_formateado)
            logger.info("Mes seleccionado: %s", mes_formateado)
            time.sleep(SLEEP_SHORT)
            
            # Seleccionar año
            selectores_anio = [
                'select#periodoAnho',
                'select#periodoAnio',
                'select#periodoAno',
                'select[ng-model*="periodo"][ng-model*="an" i]'
            ]
            
            anio_seleccionado = False
            for selector in selectores_anio:
                try:
                    if page.query_selector(selector):
                        page.select_option(selector, str(anio))
                        logger.info("Año seleccionado: %d con selector '%s'", anio, selector)
                        anio_seleccionado = True
                        time.sleep(SLEEP_SHORT)
                        break
                except Exception as e_anio:
                    logger.debug("Selector '%s' no funcionó: %s", selector, str(e_anio))
                    continue
            
            if not anio_seleccionado:
                logger.warning("No se pudo seleccionar el año %d", anio)
            
            # Hacer clic en botón de consultar
            botones_consultar = [
                'button:has-text("Consultar")',
                'button:has-text("Buscar")',
                'button.btn:has-text("Consultar")',
                'input[type="submit"]',
                'button[type="submit"]'
            ]
            
            for btn in botones_consultar:
                try:
                    if page.query_selector(btn):
                        logger.info("Haciendo clic en botón consultar: %s", btn)
                        page.click(btn)
                        time.sleep(SLEEP_MEDIUM)
                        page.wait_for_load_state("networkidle")
                        logger.info("Período aplicado exitosamente: %02d/%d", mes, anio)
                        break
                except:
                    logger.debug("Botón '%s' no disponible", btn)
                    continue
                
        except Exception as e:
            logger.warning("No se pudo cambiar el período: %s", str(e))
            logger.info("Continuando con período por defecto del sistema")
    else:
        logger.info("Usando período por defecto del sistema")


def obtener_tipos_documento_disponibles(page):
    """
    Extrae los tipos de documentos disponibles de la tabla "Resúmenes por tipo de documento"
    
    Args:
        page: Objeto page de Playwright
        
    Returns:
        list: Lista de códigos de tipos de documento disponibles (ej: ['33', '39', '61'])
    """
    logger.info("Extrayendo tipos de documentos disponibles...")
    tipos_disponibles = []
    
    try:
        # Esperar un poco para que la página cargue completamente
        time.sleep(SLEEP_MEDIUM)
        logger.debug("Página estabilizada para extracción")
        
        # Buscar todos los enlaces con href que contengan "#detalle/"
        logger.info("Buscando enlaces a detalles de documentos...")
        enlaces = page.query_selector_all('a[href*="#detalle/"]')
        
        if enlaces:
            logger.info("Encontrados %d enlaces a detalles", len(enlaces))
            for enlace in enlaces:
                try:
                    href = enlace.get_attribute("href")
                    if href and "#detalle/" in href:
                        # Extraer el código del tipo de documento
                        tipo_doc = href.split("#detalle/")[1].strip()
                        # Limpiar cualquier parámetro adicional
                        if "?" in tipo_doc:
                            tipo_doc = tipo_doc.split("?")[0]
                        if "&" in tipo_doc:
                            tipo_doc = tipo_doc.split("&")[0]
                        if tipo_doc and tipo_doc.isdigit() and tipo_doc not in tipos_disponibles:
                            tipos_disponibles.append(tipo_doc)
                            # Intentar obtener el texto del enlace para más info
                            try:
                                texto = enlace.inner_text().strip()
                                logger.debug("Tipo %s encontrado: %s", tipo_doc, texto[:50] if texto else 'sin descripción')
                            except:
                                logger.debug("Tipo de documento encontrado: %s", tipo_doc)
                except Exception as e_enlace:
                    logger.debug("Error al procesar enlace: %s", str(e_enlace))
                    continue
        
        # Si no encontró enlaces, buscar en tablas directamente
        if not tipos_disponibles:
            logger.info("No se encontraron enlaces directos, buscando en tablas...")
            tablas = page.query_selector_all("table")
            logger.debug("Encontradas %d tablas en la página", len(tablas))
            
            for idx, tabla in enumerate(tablas):
                try:
                    # Buscar enlaces dentro de la tabla
                    enlaces_tabla = tabla.query_selector_all('a[href*="#detalle/"]')
                    if enlaces_tabla:
                        logger.info("Tabla %d contiene %d enlaces a detalles", idx+1, len(enlaces_tabla))
                        for enlace in enlaces_tabla:
                            href = enlace.get_attribute("href")
                            if href and "#detalle/" in href:
                                tipo_doc = href.split("#detalle/")[1].strip().split("?")[0].split("&")[0]
                                if tipo_doc and tipo_doc.isdigit() and tipo_doc not in tipos_disponibles:
                                    tipos_disponibles.append(tipo_doc)
                                    logger.debug("Tipo de documento extraído de tabla: %s", tipo_doc)
                except Exception as e_tabla:
                    logger.debug("Error al procesar tabla %d: %s", idx+1, str(e_tabla))
                    continue
        
        if not tipos_disponibles:
            logger.warning("No se encontraron tipos de documentos con métodos convencionales")
            logger.info("Intentando extraer de cualquier enlace en la página con expresión regular...")
            # Último intento: buscar cualquier patrón que parezca un tipo de documento
            todo_html = page.content()
            import re
            patrones = re.findall(r'#detalle/(\d+)', todo_html)
            if patrones:
                tipos_disponibles = list(set(patrones))
                logger.info("Encontrados %d tipos mediante expresión regular", len(tipos_disponibles))
                for tipo in tipos_disponibles:
                    logger.debug("Tipo extraído con regex: %s", tipo)
        else:
            logger.info("Total de tipos disponibles: %d", len(tipos_disponibles))
        
        return sorted(tipos_disponibles)
    
    except Exception as e:
        logger.error("Error al extraer tipos de documento: %s", str(e))
        return []


def volver_a_resumen(page):
    """
    Vuelve a la pantalla de resumen usando el botón volver
    
    Args:
        page: Objeto page de Playwright
    """
    logger.info("Volviendo a la pantalla de resumen...")
    try:
        # Buscar botón volver con diferentes variantes
        botones_volver = [
            'button:has-text("Volver")',
            'a:has-text("Volver")',
            'button:has-text("volver")',
            'a:has-text("volver")',
            'button.btn:has-text("Volver")',
            'a.btn:has-text("Volver")',
            '[onclick*="volver"]',
            '[onclick*="back"]'
        ]
        
        for selector in botones_volver:
            try:
                boton = page.query_selector(selector)
                if boton:
                    logger.debug("Botón volver encontrado con selector: %s", selector)
                    boton.click()
                    time.sleep(SLEEP_MEDIUM)
                    page.wait_for_load_state("networkidle")
                    logger.info("Regresado a pantalla de resumen exitosamente")
                    return True
            except:
                logger.debug("Selector '%s' no funcionó para volver", selector)
                continue
        
        # Si no encuentra botón, intentar navegar directamente
        logger.warning("No se encontró botón volver, navegando directamente a URL RCV...")
        page.goto(URL_RCV)
        time.sleep(SLEEP_MEDIUM)
        page.wait_for_load_state("networkidle")
        logger.info("Navegación directa a resumen exitosa")
        return True
        
    except Exception as e:
        logger.error("Error al volver a resumen: %s", str(e))
        # Intentar navegar directamente como fallback
        try:
            logger.info("Intentando fallback: navegación directa a RCV...")
            page.goto(URL_RCV)
            time.sleep(SLEEP_MEDIUM)
            logger.info("Fallback exitoso")
            return True
        except:
            logger.error("Fallback también falló")
            return False


def navegar_a_detalle_tipo(page, tipo_documento):
    """
    Navega al detalle de un tipo de documento específico
    
    Args:
        page: Objeto page de Playwright
        tipo_documento: Código del tipo de documento (33, 39, etc.)
    """
    logger.info("Accediendo a detalle del tipo de documento %s...", tipo_documento)
    url_detalle = f"{URL_RCV}/#detalle/{tipo_documento}"
    logger.debug("Navegando a URL: %s", url_detalle)
    try:
        page.goto(url_detalle, timeout=60000)
    except PlaywrightTimeoutError:
        logger.error("Timeout al navegar al detalle del tipo %s", tipo_documento)
        raise
    time.sleep(SLEEP_LONG)
    logger.info("Página de detalle del tipo %s cargada", tipo_documento)
    
    # Click en el detalle del tipo de documento
    try:
        selector = f'a[href="#detalle/{tipo_documento}"]'
        logger.debug("Haciendo clic en enlace: %s", selector)
        page.click(selector)
        time.sleep(3)
        logger.info("Detalle del tipo %s cargado exitosamente", tipo_documento)
    except Exception as e:
        logger.warning("Advertencia al hacer clic en detalle del tipo %s: %s", tipo_documento, str(e))
        time.sleep(2)


def parsear_tabla(tabla):
    """
    Parsea una tabla HTML y la convierte en una lista de diccionarios
    """
    try:
        # Obtener todas las filas
        filas = tabla.query_selector_all("tr")
        if not filas:
            logger.debug("Tabla sin filas")
            return []
        
        # Obtener encabezados (primera fila)
        headers_row = filas[0]
        headers = [th.inner_text().strip() for th in headers_row.query_selector_all("th, td")]
        logger.debug("Encabezados de tabla: %s", headers)
        
        # Si no hay encabezados válidos, retornar vacío
        if not headers or not any(headers):
            logger.debug("Encabezados inválidos o vacíos")
            return []
        
        # Procesar las filas de datos
        datos = []
        for fila in filas[1:]:  # Saltar la fila de encabezados
            celdas = fila.query_selector_all("td")
            if celdas:
                fila_dict = {}
                for idx, celda in enumerate(celdas):
                    if idx < len(headers):
                        fila_dict[headers[idx]] = celda.inner_text().strip()
                if fila_dict:  # Solo agregar si hay datos
                    datos.append(fila_dict)
        
        logger.debug("Parseada tabla con %d filas de datos", len(datos))
        return datos
    except Exception as e:
        logger.error("Error al parsear tabla: %s", str(e))
        return []


def extraer_razon_social(page, folio):
    """
    Extrae la razón social del emisor desde el detalle del documento
    """
    logger.debug("Extrayendo razón social para folio %s", folio)
    try:
        # Buscar el link/botón del folio para hacer clic
        folio_selector = f'a:has-text("{folio}")'
        elemento = page.query_selector(folio_selector)
        
        if elemento:
            logger.debug("Elemento del folio %s encontrado, haciendo clic...", folio)
            # Hacer clic para abrir el detalle (abre un modal/pop-up)
            elemento.click()
            time.sleep(SLEEP_LONG)
            logger.debug("Modal de detalle abierto para folio %s", folio)
            
            # Buscar la razón social en el detalle
            razon_social = None
            texto_detalle = page.inner_text("body")
            logger.debug("Texto del detalle extraído (%d caracteres)", len(texto_detalle))
            
            # Buscar patrones comunes
            patrones = [
                r"Razón Social[:\s]+([^\n]+)",
                r"Emisor[:\s]+([^\n]+)",
                r"Nombre[:\s]+([^\n]+)",
            ]
            
            for patron in patrones:
                match = re.search(patron, texto_detalle, re.IGNORECASE)
                if match:
                    razon_social = match.group(1).strip()
                    # Limpiar prefijos no deseados
                    razon_social = re.sub(
                        r'^(Emisor|Razón Social|Nombre)\s*[::\t]+\s*', 
                        '', 
                        razon_social, 
                        flags=re.IGNORECASE
                    ).strip()
                    logger.debug("Razón social encontrada con patrón '%s': %s", patron, razon_social)
                    break
            
            if not razon_social:
                logger.debug("No se encontró razón social con patrones predefinidos para folio %s", folio)
            
            # Cerrar el modal/pop-up
            logger.debug("Cerrando modal de folio %s", folio)
            cerrar_modal(page)
            
            return razon_social
        
        logger.debug("No se encontró elemento para folio %s", folio)
        return None
    except Exception as e:
        logger.error("Error al extraer razón social del folio %s: %s", folio, str(e))
        # Intentar cerrar el modal por si quedó abierto
        try:
            page.keyboard.press('Escape')
        except:
            pass
        return None


def cerrar_modal(page):
    """
    Cierra un modal/pop-up abierto
    """
    logger.debug("Intentando cerrar modal...")
    try:
        # Buscar botón de cerrar (X, Cerrar, etc.)
        close_selectors = [
            'button:has-text("Cerrar")',
            'button:has-text("×")',
            'button.close',
            '[aria-label="Close"]',
            '.modal-header button',
            'button[data-dismiss="modal"]'
        ]
        
        for selector in close_selectors:
            close_button = page.query_selector(selector)
            if close_button:
                logger.debug("Botón cerrar encontrado con selector: %s", selector)
                close_button.click()
                time.sleep(SLEEP_SHORT)
                logger.debug("Modal cerrado exitosamente")
                return
        
        # Si no encuentra botón, presionar ESC
        logger.debug("No se encontró botón cerrar, presionando ESC")
        page.keyboard.press('Escape')
        time.sleep(SLEEP_SHORT)
    except:
        # Si falla, intentar con ESC
        logger.debug("Error al cerrar modal, intentando con ESC")
        page.keyboard.press('Escape')
        time.sleep(SLEEP_SHORT)


def extraer_datos_tablas(page):
    """
    Extrae datos de todas las tablas en la página actual
    """
    logger.info("Iniciando extracción de datos de tablas...")
    tablas = page.query_selector_all("table")
    
    if not tablas:
        logger.warning("No se encontraron tablas en la página")
        return []
    
    logger.info("Encontradas %d tablas para procesar", len(tablas))
    todos_los_datos = []
    
    for idx, tabla in enumerate(tablas):
        time.sleep(SLEEP_MEDIUM)
        logger.info("Procesando Tabla %d de %d...", idx+1, len(tablas))
        
        # Parsear la tabla
        logger.debug("Parseando tabla %d...", idx+1)
        datos_tabla = parsear_tabla(tabla)
        
        if datos_tabla:
            logger.info("Tabla %d: %d registros extraídos", idx+1, len(datos_tabla))
            
            # Agregar razón social a cada registro
            logger.info("Extrayendo razones sociales para %d registros...", len(datos_tabla))
            for reg_idx, registro in enumerate(datos_tabla):
                folio = registro.get('Folio')
                if folio:
                    logger.debug("Procesando registro %d/%d - Folio: %s", reg_idx+1, len(datos_tabla), folio)
                    razon_social = extraer_razon_social(page, folio)
                    if razon_social:
                        registro['Razon Social Emisor'] = razon_social
                        logger.debug("Folio %s: razón social obtenida - %s", folio, razon_social)
                    else:
                        logger.debug("Folio %s: no se pudo obtener razón social", folio)
                else:
                    logger.debug("Registro %d sin folio, saltando extracción de razón social", reg_idx+1)
            
            todos_los_datos.extend(datos_tabla)
        else:
            logger.warning("Tabla %d: no se pudieron extraer datos", idx+1)
    
    logger.info("Extracción completada: %d registros totales", len(todos_los_datos))
    return todos_los_datos
