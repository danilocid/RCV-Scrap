"""
Módulo de extracción de datos del portal SII
"""
import time
import re
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from config import *


def login_sii(page, rut, clave):
    """
    Realiza el login en el portal del SII
    """
    print("Accediendo al portal del SII...")
    page.goto(URL_LOGIN_SII)

    # Click en "Ingresar a Mi SII"
    page.click("text=Ingresar a Mi SII")
    time.sleep(SLEEP_MEDIUM)
    
    # Completar RUT y clave
    print("Ingresando credenciales...")
    page.fill('input[name="rutcntr"]', rut)
    time.sleep(SLEEP_MEDIUM)
    page.fill('input[name="clave"]', clave)
    time.sleep(SLEEP_MEDIUM)

    # Enviar formulario
    page.click('button[id="bt_ingresar"]')
    time.sleep(SLEEP_LONG)
    
    # Verificar si hay error de login
    try:
        error_element = page.wait_for_selector(
            "text=/contraseña.*incorrecta|rut.*inválido|error/i", 
            timeout=3000
        )
        if error_element:
            return False
    except PlaywrightTimeoutError:
        # No hay mensaje de error, el login fue exitoso
        pass
    
    print("✓ Login exitoso")
    page.wait_for_load_state("networkidle")
    return True


def navegar_a_rcv(page, mes=None, anio=None):
    """
    Navega al módulo RCV y selecciona el período si se proporciona
    
    Args:
        page: Objeto page de Playwright
        mes: Mes para filtrar (1-12), None para mes actual
        anio: Año para filtrar (ej: 2025), None para año actual
    """
    print("Navegando al RCV...")
    page.goto(URL_RCV)

    time.sleep(SLEEP_EXTRA_LONG)
    page.click('button[class="btn btn-default btn-xs-block btn-block"]')
    time.sleep(3)
    page.wait_for_load_state("networkidle")
    
    # Si se proporcionan mes y año, intentar seleccionarlos
    if mes and anio:
        print(f"Intentando seleccionar período: {mes:02d}/{anio}...")
        try:
            # Esperar a que los selectores de período estén disponibles
            page.wait_for_selector('select#periodoMes', timeout=5000)
            
            # Seleccionar mes (formato con cero al inicio: "01", "02", etc.)
            mes_formateado = f"{mes:02d}"
            page.select_option('select#periodoMes', mes_formateado)
            print(f"  ✓ Mes seleccionado: {mes_formateado}")
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
                        print(f"  ✓ Año seleccionado: {anio}")
                        anio_seleccionado = True
                        time.sleep(SLEEP_SHORT)
                        break
                except Exception as e_anio:
                    continue
            
            if not anio_seleccionado:
                print(f"  ⚠ No se pudo seleccionar el año")
            
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
                        page.click(btn)
                        time.sleep(SLEEP_MEDIUM)
                        page.wait_for_load_state("networkidle")
                        print(f"  ✓ Período aplicado: {mes:02d}/{anio}")
                        break
                except:
                    continue
                
        except Exception as e:
            print(f"  ⚠ No se pudo cambiar el período: {str(e)}")
            print(f"  Continuando con período por defecto...")
    else:
        print("  ℹ️  Usando período por defecto del sistema")


def obtener_tipos_documento_disponibles(page):
    """
    Extrae los tipos de documentos disponibles de la tabla "Resúmenes por tipo de documento"
    
    Args:
        page: Objeto page de Playwright
        
    Returns:
        list: Lista de códigos de tipos de documento disponibles (ej: ['33', '39', '61'])
    """
    print("\nExtrayendo tipos de documentos disponibles...")
    tipos_disponibles = []
    
    try:
        # Esperar un poco para que la página cargue completamente
        time.sleep(SLEEP_MEDIUM)
        
        # Buscar todos los enlaces con href que contengan "#detalle/"
        print("  Buscando enlaces a detalles de documentos...")
        enlaces = page.query_selector_all('a[href*="#detalle/"]')
        
        if enlaces:
            print(f"  ✓ Encontrados {len(enlaces)} enlaces a detalles")
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
                                print(f"    → Tipo {tipo_doc}: {texto[:50] if texto else 'sin descripción'}")
                            except:
                                print(f"    → Tipo de documento encontrado: {tipo_doc}")
                except Exception as e_enlace:
                    continue
        
        # Si no encontró enlaces, buscar en tablas directamente
        if not tipos_disponibles:
            print("  Buscando en tablas...")
            tablas = page.query_selector_all("table")
            print(f"  Encontradas {len(tablas)} tablas en la página")
            
            for idx, tabla in enumerate(tablas):
                try:
                    # Buscar enlaces dentro de la tabla
                    enlaces_tabla = tabla.query_selector_all('a[href*="#detalle/"]')
                    if enlaces_tabla:
                        print(f"  ✓ Tabla {idx+1} contiene {len(enlaces_tabla)} enlaces a detalles")
                        for enlace in enlaces_tabla:
                            href = enlace.get_attribute("href")
                            if href and "#detalle/" in href:
                                tipo_doc = href.split("#detalle/")[1].strip().split("?")[0].split("&")[0]
                                if tipo_doc and tipo_doc.isdigit() and tipo_doc not in tipos_disponibles:
                                    tipos_disponibles.append(tipo_doc)
                                    print(f"    → Tipo de documento: {tipo_doc}")
                except Exception as e_tabla:
                    continue
        
        if not tipos_disponibles:
            print("  ⚠ No se encontraron tipos de documentos")
            print("  Intentando extraer de cualquier enlace en la página...")
            # Último intento: buscar cualquier patrón que parezca un tipo de documento
            todo_html = page.content()
            import re
            patrones = re.findall(r'#detalle/(\d+)', todo_html)
            if patrones:
                tipos_disponibles = list(set(patrones))
                print(f"  ✓ Encontrados {len(tipos_disponibles)} tipos mediante expresión regular")
                for tipo in tipos_disponibles:
                    print(f"    → Tipo: {tipo}")
        else:
            print(f"\n  ✓ Total de tipos disponibles: {len(tipos_disponibles)}")
        
        return sorted(tipos_disponibles)
    
    except Exception as e:
        print(f"  ⚠ Error al extraer tipos de documento: {str(e)}")
        return []


def volver_a_resumen(page):
    """
    Vuelve a la pantalla de resumen usando el botón volver
    
    Args:
        page: Objeto page de Playwright
    """
    print("\nVolviendo a la pantalla de resumen...")
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
                    boton.click()
                    time.sleep(SLEEP_MEDIUM)
                    page.wait_for_load_state("networkidle")
                    print("  ✓ Regresado a resumen")
                    return True
            except:
                continue
        
        # Si no encuentra botón, intentar navegar directamente
        print("  ⚠ No se encontró botón volver, navegando directamente...")
        page.goto(URL_RCV)
        time.sleep(SLEEP_MEDIUM)
        page.wait_for_load_state("networkidle")
        return True
        
    except Exception as e:
        print(f"  ⚠ Error al volver a resumen: {str(e)}")
        # Intentar navegar directamente como fallback
        try:
            page.goto(URL_RCV)
            time.sleep(SLEEP_MEDIUM)
            return True
        except:
            return False


def navegar_a_detalle_tipo(page, tipo_documento):
    """
    Navega al detalle de un tipo de documento específico
    
    Args:
        page: Objeto page de Playwright
        tipo_documento: Código del tipo de documento (33, 39, etc.)
    """
    print(f"Accediendo a detalle del tipo de documento {tipo_documento}...")
    page.goto(f"{URL_RCV}/#detalle/{tipo_documento}")
    time.sleep(SLEEP_LONG)
    
    # Click en el detalle del tipo de documento
    try:
        page.click(f'a[href="#detalle/{tipo_documento}"]')
        time.sleep(3)
    except Exception as e:
        print(f"  ⚠ Advertencia al hacer clic en detalle: {str(e)}")
        time.sleep(2)


def parsear_tabla(tabla):
    """
    Parsea una tabla HTML y la convierte en una lista de diccionarios
    """
    try:
        # Obtener todas las filas
        filas = tabla.query_selector_all("tr")
        if not filas:
            return []
        
        # Obtener encabezados (primera fila)
        headers_row = filas[0]
        headers = [th.inner_text().strip() for th in headers_row.query_selector_all("th, td")]
        
        # Si no hay encabezados válidos, retornar vacío
        if not headers or not any(headers):
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
        
        return datos
    except Exception as e:
        print(f"   Error al parsear tabla: {str(e)}")
        return []


def extraer_razon_social(page, folio):
    """
    Extrae la razón social del emisor desde el detalle del documento
    """
    try:
        # Buscar el link/botón del folio para hacer clic
        folio_selector = f'a:has-text("{folio}")'
        elemento = page.query_selector(folio_selector)
        
        if elemento:
            # Hacer clic para abrir el detalle (abre un modal/pop-up)
            elemento.click()
            time.sleep(SLEEP_LONG)
            
            # Buscar la razón social en el detalle
            razon_social = None
            texto_detalle = page.inner_text("body")
            
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
                    break
            
            # Cerrar el modal/pop-up
            cerrar_modal(page)
            
            return razon_social
        
        return None
    except Exception as e:
        print(f"    ⚠ Error al extraer razón social del folio {folio}: {str(e)}")
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
                close_button.click()
                time.sleep(SLEEP_SHORT)
                return
        
        # Si no encuentra botón, presionar ESC
        page.keyboard.press('Escape')
        time.sleep(SLEEP_SHORT)
    except:
        # Si falla, intentar con ESC
        page.keyboard.press('Escape')
        time.sleep(SLEEP_SHORT)


def extraer_datos_tablas(page):
    """
    Extrae datos de todas las tablas en la página actual
    """
    print("Extrayendo datos de las tablas...")
    tablas = page.query_selector_all("table")
    
    if not tablas:
        print("⚠ ADVERTENCIA: No se encontraron tablas en la página")
        return []
    
    todos_los_datos = []
    
    for idx, tabla in enumerate(tablas):
        time.sleep(SLEEP_MEDIUM)
        print(f"\nProcesando Tabla {idx+1}...")
        
        # Parsear la tabla
        datos_tabla = parsear_tabla(tabla)
        
        if datos_tabla:
            print(f"  ✓ {len(datos_tabla)} registros encontrados")
            
            # Agregar razón social a cada registro
            print(f"  Extrayendo razones sociales...")
            for registro in datos_tabla:
                folio = registro.get('Folio')
                if folio:
                    razon_social = extraer_razon_social(page, folio)
                    if razon_social:
                        registro['Razon Social Emisor'] = razon_social
                        print(f"    ✓ Folio {folio}: {razon_social}")
                    else:
                        print(f"    ⚠ Folio {folio}: No se pudo extraer razón social")
            
            todos_los_datos.extend(datos_tabla)
        else:
            print(f"  ⚠ No se pudieron extraer datos de esta tabla")
    
    return todos_los_datos
