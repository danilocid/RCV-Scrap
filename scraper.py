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


def navegar_a_rcv(page, tipo_documento):
    """
    Navega al módulo RCV y al detalle del tipo de documento especificado
    """
    print("Navegando al RCV...")
    page.goto(URL_RCV)

    time.sleep(SLEEP_EXTRA_LONG)
    page.click('button[class="btn btn-default btn-xs-block btn-block"]')
    time.sleep(3)
    page.wait_for_load_state("networkidle")
    
    print("Accediendo a detalle de facturas...")
    page.goto(f"{URL_RCV}/#detalle/{tipo_documento}")
    time.sleep(SLEEP_LONG)
    
    # Click en el detalle del tipo de documento
    page.click(f'a[href="#detalle/{tipo_documento}"]')
    time.sleep(3)


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
