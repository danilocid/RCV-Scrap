"""
RCV Scrap - Sistema de extracción del Registro de Compras y Ventas del SII
API REST para extracción automática de datos
"""
import sys
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from extractor import ejecutar_scraping
from api_server import iniciar_servidor


def main():
    """
    Función principal - inicia el servidor API REST
    """
    try:
        iniciar_servidor(ejecutar_scraping)
    
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
