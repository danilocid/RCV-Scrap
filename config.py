"""
Configuración y constantes del sistema RCV Scrap
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Credenciales
RUT = os.getenv("SII_RUT")
CLAVE = os.getenv("SII_CLAVE")
AMBIENTE = os.getenv("AMBIENTE", "PROD")

# URLs
URL_LOGIN_SII = "https://misii.sii.cl/cgi_misii/siihome.cgi"
URL_RCV = "https://www4.sii.cl/consdcvinternetui"

# Configuración de timeouts (en milisegundos)
DEFAULT_TIMEOUT = 30000
SLEEP_SHORT = 0.5
SLEEP_MEDIUM = 1
SLEEP_LONG = 2
SLEEP_EXTRA_LONG = 5

# Tipos de documento SII
TIPOS_DOCUMENTO = {
    "33": "Factura Electrónica",
    "34": "Factura No Afecta o Exenta Electrónica",
    "39": "Boleta Electrónica",
    "41": "Boleta No Afecta o Exenta Electrónica",
    "43": "Liquidación Factura Electrónica",
    "46": "Factura de Compra Electrónica",
    "52": "Guía de Despacho Electrónica",
    "56": "Nota de Débito Electrónica",
    "61": "Nota de Crédito Electrónica",
    "110": "Factura de Exportación Electrónica",
    "111": "Nota de Débito de Exportación Electrónica",
    "112": "Nota de Crédito de Exportación Electrónica"
}

# Tipo de documento por defecto
TIPO_DOCUMENTO_FACTURA = "33"

# Archivos de salida
ARCHIVO_JSON = "datos_rcv.json"
ARCHIVO_EXCEL = "datos_rcv.xlsx"

def validar_configuracion():
    """
    Valida que las variables de entorno necesarias estén configuradas
    """
    if not RUT or not CLAVE:
        raise ValueError("Las variables de entorno SII_RUT y SII_CLAVE deben estar definidas en el archivo .env")
    return True
