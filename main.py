"""
RCV Scrap - Sistema de extracción del Registro de Compras y Ventas del SII
"""
import sys
import time
import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Importar módulos propios
from config import (
    RUT, CLAVE, AMBIENTE, TIPO_DOCUMENTO_FACTURA,
    ARCHIVO_JSON, ARCHIVO_EXCEL, DEFAULT_TIMEOUT,
    validar_configuracion
)
from scraper import login_sii, navegar_a_rcv, extraer_datos_tablas
from procesador import eliminar_duplicados
from guardador import guardar_datos_json, guardar_datos_excel


def main():
    """
    Función principal del sistema
    """
    print(f"Ejecutando en modo: {AMBIENTE}")
    
    # Validar configuración
    try:
        validar_configuracion()
    except ValueError as e:
        print(f"❌ ERROR DE CONFIGURACIÓN: {str(e)}")
        sys.exit(1)
    
    try:
        with sync_playwright() as p:
            # Configurar navegador
            headless = AMBIENTE != "DEV"
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            page.set_default_timeout(DEFAULT_TIMEOUT)
            
            # Login en el SII
            login_exitoso = login_sii(page, RUT, CLAVE)
            if not login_exitoso:
                print("❌ ERROR: Credenciales incorrectas. Verifica tu RUT y contraseña.")
                browser.close()
                sys.exit(1)
            
            # Navegar al RCV
            navegar_a_rcv(page, TIPO_DOCUMENTO_FACTURA)
            
            # Extraer datos
            datos_extraidos = extraer_datos_tablas(page)
            
            # Procesar y guardar datos
            if datos_extraidos:
                print(f"\n📊 Procesando datos finales...")
                print(f"  Total de registros antes de eliminar duplicados: {len(datos_extraidos)}")
                
                # Crear estructura de datos
                datos_completos = {
                    "fecha_extraccion": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "tipo_documento": TIPO_DOCUMENTO_FACTURA,
                    "datos": eliminar_duplicados(datos_extraidos)
                }
                
                # Guardar en JSON
                guardar_datos_json(datos_completos, ARCHIVO_JSON)
                
                # Guardar en Excel
                if datos_completos["datos"]:
                    df_final = pd.DataFrame(datos_completos["datos"])
                    guardar_datos_excel([df_final], ARCHIVO_EXCEL)
                
                print(f"\n✓ Total de registros únicos guardados: {len(datos_completos['datos'])}")
            else:
                print("\n⚠ No se extrajeron datos de ninguna tabla")
            
            print("\n✓ Extracción completada exitosamente")
            browser.close()
    
    except PlaywrightTimeoutError as e:
        print(f"❌ ERROR DE TIMEOUT: La operación tardó demasiado tiempo.")
        print(f"   Detalle: {str(e)}")
        print("   Intenta nuevamente o verifica tu conexión a internet.")
        sys.exit(1)
    
    except Exception as e:
        print(f"❌ ERROR INESPERADO: {type(e).__name__}")
        print(f"   Detalle: {str(e)}")
        print("   Por favor, revisa el error y contacta al administrador si persiste.")
        sys.exit(1)


if __name__ == "__main__":
    main()
