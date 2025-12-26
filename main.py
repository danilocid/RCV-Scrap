from playwright.sync_api import sync_playwright
import time
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env
load_dotenv()

# Leer credenciales y configuración desde variables de entorno
RUT = os.getenv("SII_RUT")
CLAVE = os.getenv("SII_CLAVE")
AMBIENTE = os.getenv("AMBIENTE", "PROD")  # Por defecto PROD si no se especifica

if not RUT or not CLAVE:
    raise ValueError("Las variables de entorno SII_RUT y SII_CLAVE deben estar definidas en el archivo .env")

with sync_playwright() as p:
    # En desarrollo (DEV) muestra el navegador, en producción lo oculta
    headless = AMBIENTE != "DEV"
    browser = p.chromium.launch(headless=headless)
    page = browser.new_page()

    # 1. Ir a login SII
    page.goto("https://misii.sii.cl/cgi_misii/siihome.cgi")

    # 2. Click en "Ingresar a Mi SII"
    page.click("text=Ingresar a Mi SII")
    time.sleep(1)  # espera que cargue
    # 3. Completar RUT y clave
    page.fill('input[name="rutcntr"]', RUT)   # parte numérica
    time.sleep(1)  # espera que cargue
    page.fill('input[name="clave"]', CLAVE)
    time.sleep(1)  # espera que cargue

    # 4. Enviar formulario
    page.click('button[id="bt_ingresar"]')
    time.sleep(1)  # espera que cargue
    page.wait_for_load_state("networkidle")

    # 5. Ir al RCV
    page.goto("https://www4.sii.cl/consdcvinternetui")

    time.sleep(5)  # espera que cargue
    page.click('button[class="btn btn-default btn-xs-block btn-block"]')
    time.sleep(3)  # espera que cargue
    page.wait_for_load_state("networkidle")
    page.goto("https://www4.sii.cl/consdcvinternetui/#detalle/33")
    time.sleep(2)  # espera que cargue
    # 6. Ejemplo: obtener títulos de las tablas
    page.click('a[href="#detalle/33"]')
    time.sleep(3)  # espera que cargue
    tablas = page.query_selector_all("table")
    for idx, tabla in enumerate(tablas):
        time.sleep(1)
        print(f"Tabla {idx+1}:")
        print(tabla.inner_text())  # imprime los primeros 500 chars
        #print(tabla.inner_html())

    browser.close()
