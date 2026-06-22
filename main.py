"""
RCV Scrap - Sistema de extracción del Registro de Compras y Ventas del SII
API REST para extracción automática de datos
"""
import sys
import logging
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from extractor import ejecutar_scraping
from api_server import iniciar_servidor

logger = logging.getLogger("rcv_scrap")


def main():
    """
    Función principal - inicia el servidor API REST
    """
    logger.info("Iniciando RCV Scrap...")
    
    try:
        iniciar_servidor(ejecutar_scraping)
    
    except PlaywrightTimeoutError as e:
        logger.error("ERROR DE TIMEOUT: La operación tardó demasiado tiempo")
        logger.error("Detalle: %s", str(e))
        logger.info("Intenta nuevamente o verifica tu conexión a internet")
        sys.exit(1)
    
    except Exception as e:
        logger.error("ERROR INESPERADO: %s", type(e).__name__)
        logger.error("Detalle: %s", str(e))
        logger.info("Por favor, revisa el error y contacta al administrador si persiste")
        sys.exit(1)


if __name__ == "__main__":
    main()
