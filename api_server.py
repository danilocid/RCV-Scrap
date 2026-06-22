"""
Servidor API REST para RCV Scrap
"""
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
import os
import json
import logging
from datetime import datetime
from enum import Enum
import uvicorn

from config import ARCHIVO_JSON, ARCHIVO_EXCEL

logger = logging.getLogger("api_server")

# Variable global para almacenar la función de scraping
_ejecutar_scraping_func = None


def configurar_scraping(func):
    """
    Configura la función de scraping que usará la API
    
    Args:
        func: Función que ejecuta el scraping
    """
    global _ejecutar_scraping_func
    _ejecutar_scraping_func = func


def crear_app(ejecutar_scraping_func):
    """
    Crea y configura la aplicación FastAPI
    
    Args:
        ejecutar_scraping_func: Función que ejecuta el scraping
        
    Returns:
        FastAPI: Aplicación configurada
    """
    app = FastAPI(
        title="RCV Scrap API",
        description="API para extraer datos del Registro de Compras y Ventas del SII",
        version="2.0.0"
    )
    
    # Modelo para solicitud de extracción
    class ExtraccionRequest(BaseModel):
        mes: Optional[int] = Field(None, ge=1, le=12, description="Mes para filtrar (1-12). Si no se especifica, usa el mes actual")
        anio: Optional[int] = Field(None, ge=2000, le=2100, description="Año para filtrar. Si no se especifica, usa el año actual")
        tipos_documento: Optional[List[str]] = Field(
            None, 
            description="Lista de códigos de tipos de documento. Si no se especifica, se procesarán TODOS los tipos disponibles."
        )
        
        class Config:
            json_schema_extra = {
                "example": {
                    "mes": 12,
                    "anio": 2025,
                    "tipos_documento": ["33", "39"]
                }
            }
    
    # Estado global de la extracción
    estado_extraccion = {
        "estado": "inactivo",
        "mensaje": "",
        "fecha_inicio": None,
        "fecha_fin": None,
        "total_registros": 0,
        "error": None
    }
    
    class EstadoEnum(str, Enum):
        inactivo = "inactivo"
        ejecutando = "ejecutando"
        completado = "completado"
        error = "error"
    
    class EstadoResponse(BaseModel):
        estado: EstadoEnum
        mensaje: str
        fecha_inicio: Optional[str] = None
        fecha_fin: Optional[str] = None
        total_registros: int = 0
        error: Optional[str] = None
        periodo: Optional[dict] = None
        tipos_documento: Optional[List[str]] = None
    
    def ejecutar_extraccion_background(mes=None, anio=None, tipos_documento=None):
        """Ejecuta la extracción en segundo plano"""
        nonlocal estado_extraccion
        
        try:
            estado_extraccion["estado"] = "ejecutando"
            estado_extraccion["mensaje"] = "Extracción en proceso..."
            estado_extraccion["fecha_inicio"] = datetime.now().isoformat()
            estado_extraccion["fecha_fin"] = None
            estado_extraccion["error"] = None
            estado_extraccion["periodo"] = {"mes": mes, "anio": anio}
            estado_extraccion["tipos_documento"] = tipos_documento
            
            # Ejecutar la extracción con parámetros
            resultado = ejecutar_scraping_func(mes=mes, anio=anio, tipos_documento=tipos_documento)
            
            if resultado:
                estado_extraccion["total_registros"] = len(resultado.get("datos", []))
            
            estado_extraccion["estado"] = "completado"
            estado_extraccion["mensaje"] = "Extracción completada exitosamente"
            estado_extraccion["fecha_fin"] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error("Error durante la extracción: %s", str(e))
            estado_extraccion["estado"] = "error"
            estado_extraccion["mensaje"] = "Error durante la extracción"
            estado_extraccion["error"] = str(e)
            estado_extraccion["fecha_fin"] = datetime.now().isoformat()
    
    @app.get("/", tags=["General"])
    async def root():
        from config import TIPOS_DOCUMENTO
        return {
            "nombre": "RCV Scrap API",
            "version": "2.0.0",
            "descripcion": "API para extraer datos del Registro de Compras y Ventas del SII",
            "tipos_documento_disponibles": TIPOS_DOCUMENTO,
            "endpoints": {
                "GET /": "Información de la API",
                "POST /extraer": "Iniciar extracción de datos. Parámetros opcionales: mes, anio (usa mes/año actual si no se especifican), tipos_documento (usa todos si no se especifica)",
                "GET /estado": "Obtener estado de la extracción",
                "GET /descargar/json": "Descargar datos en formato JSON",
                "GET /descargar/excel": "Descargar datos en formato Excel",
                "GET /datos": "Obtener datos en formato JSON directamente",
                "GET /health": "Health check del servidor"
            }
        }
              
    
    @app.post("/extraer", tags=["Extracción"])
    async def iniciar_extraccion(
        background_tasks: BackgroundTasks,
        request: Optional[ExtraccionRequest] = None
    ):
        nonlocal estado_extraccion
        
        if estado_extraccion["estado"] == "ejecutando":
            raise HTTPException(
                status_code=409,
                detail="Ya hay una extracción en proceso. Por favor espera a que termine."
            )
        
        # Extraer parámetros (usar valores actuales si no se proporcionan)
        mes = request.mes if request else None
        anio = request.anio if request else None
        tipos_documento = request.tipos_documento if request else None
        
        estado_extraccion = {
            "estado": "ejecutando",
            "mensaje": "Extracción iniciada",
            "fecha_inicio": datetime.now().isoformat(),
            "fecha_fin": None,
            "total_registros": 0,
            "error": None,
            "periodo": {"mes": mes, "anio": anio},
            "tipos_documento": tipos_documento
        }
        
        background_tasks.add_task(
            ejecutar_extraccion_background, 
            mes=mes, 
            anio=anio, 
            tipos_documento=tipos_documento
        )
        
        return {
            "mensaje": "Extracción iniciada correctamente",
            "estado": estado_extraccion["estado"],
            "periodo": estado_extraccion["periodo"],
            "tipos_documento": tipos_documento
        }
    
    @app.get("/estado", tags=["Extracción"], response_model=EstadoResponse)
    async def obtener_estado():
        return EstadoResponse(**estado_extraccion)
    
    @app.get("/descargar/json", tags=["Descarga"])
    async def descargar_json():
        if not os.path.exists(ARCHIVO_JSON):
            raise HTTPException(
                status_code=404,
                detail="Archivo JSON no encontrado. Ejecuta primero la extracción."
            )
        return FileResponse(
            path=ARCHIVO_JSON,
            media_type="application/json",
            filename=ARCHIVO_JSON
        )
    
    @app.get("/descargar/excel", tags=["Descarga"])
    async def descargar_excel():
        if not os.path.exists(ARCHIVO_EXCEL):
            raise HTTPException(
                status_code=404,
                detail="Archivo Excel no encontrado. Ejecuta primero la extracción."
            )
        return FileResponse(
            path=ARCHIVO_EXCEL,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=ARCHIVO_EXCEL
        )
    
    @app.get("/datos", tags=["Datos"])
    async def obtener_datos():
        if not os.path.exists(ARCHIVO_JSON):
            raise HTTPException(
                status_code=404,
                detail="Datos no disponibles. Ejecuta primero la extracción."
            )
        try:
            with open(ARCHIVO_JSON, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            return JSONResponse(content=datos)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al leer los datos: {str(e)}"
            )
    
    @app.get("/health", tags=["General"])
    async def health_check():
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat()
        }
    
    return app


def iniciar_servidor(ejecutar_scraping_func):
    """
    Inicia el servidor FastAPI
    
    Args:
        ejecutar_scraping_func: Función que ejecuta el scraping
    """
    app = crear_app(ejecutar_scraping_func)
    
    # Obtener puerto de la variable de entorno (Cloud Run usa PORT=8080)
    # Fallback a 8000 para desarrollo local
    port = int(os.environ.get("PORT", 8000))
    
    logger.info("Iniciando servidor API REST...")
    logger.info("Servidor disponible en: http://0.0.0.0:%d", port)
    logger.info("Documentación Swagger: http://localhost:%d/docs", port)
    logger.info("Documentación ReDoc: http://localhost:%d/redoc", port)
    
    uvicorn.run(app, host="0.0.0.0", port=port)


# Crear instancia de la app para Cloud Run/uvicorn
# La función de scraping se configurará en tiempo de importación
from extractor import ejecutar_scraping as _ejecutar_scraping_default
app = crear_app(_ejecutar_scraping_default)
