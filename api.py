"""
API REST para RCV Scrap usando FastAPI
"""
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import os
import json
from datetime import datetime
from enum import Enum

# Importar funciones del sistema
from main import main as ejecutar_extraccion
from config import ARCHIVO_JSON, ARCHIVO_EXCEL

app = FastAPI(
    title="RCV Scrap API",
    description="API para extraer datos del Registro de Compras y Ventas del SII",
    version="1.0.0"
)

# Estado global de la extracción
estado_extraccion = {
    "estado": "inactivo",  # inactivo, ejecutando, completado, error
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


def ejecutar_extraccion_background():
    """
    Ejecuta la extracción en segundo plano
    """
    global estado_extraccion
    
    try:
        estado_extraccion["estado"] = "ejecutando"
        estado_extraccion["mensaje"] = "Extracción en proceso..."
        estado_extraccion["fecha_inicio"] = datetime.now().isoformat()
        estado_extraccion["fecha_fin"] = None
        estado_extraccion["error"] = None
        
        # Ejecutar la extracción
        ejecutar_extraccion()
        
        # Leer el archivo JSON para obtener el total de registros
        if os.path.exists(ARCHIVO_JSON):
            with open(ARCHIVO_JSON, 'r', encoding='utf-8') as f:
                datos = json.load(f)
                total = len(datos.get("datos", []))
                estado_extraccion["total_registros"] = total
        
        estado_extraccion["estado"] = "completado"
        estado_extraccion["mensaje"] = "Extracción completada exitosamente"
        estado_extraccion["fecha_fin"] = datetime.now().isoformat()
        
    except Exception as e:
        estado_extraccion["estado"] = "error"
        estado_extraccion["mensaje"] = "Error durante la extracción"
        estado_extraccion["error"] = str(e)
        estado_extraccion["fecha_fin"] = datetime.now().isoformat()


@app.get("/", tags=["General"])
async def root():
    """
    Endpoint raíz - Información de la API
    """
    return {
        "nombre": "RCV Scrap API",
        "version": "1.0.0",
        "descripcion": "API para extraer datos del Registro de Compras y Ventas del SII",
        "endpoints": {
            "GET /": "Información de la API",
            "POST /extraer": "Iniciar extracción de datos",
            "GET /estado": "Obtener estado de la extracción",
            "GET /descargar/json": "Descargar datos en formato JSON",
            "GET /descargar/excel": "Descargar datos en formato Excel",
            "GET /datos": "Obtener datos en formato JSON directamente"
        }
    }


@app.post("/extraer", tags=["Extracción"], response_model=dict)
async def iniciar_extraccion(background_tasks: BackgroundTasks):
    """
    Inicia el proceso de extracción de datos del RCV en segundo plano
    """
    global estado_extraccion
    
    if estado_extraccion["estado"] == "ejecutando":
        raise HTTPException(
            status_code=409,
            detail="Ya hay una extracción en proceso. Por favor espera a que termine."
        )
    
    # Reiniciar estado
    estado_extraccion = {
        "estado": "ejecutando",
        "mensaje": "Extracción iniciada",
        "fecha_inicio": datetime.now().isoformat(),
        "fecha_fin": None,
        "total_registros": 0,
        "error": None
    }
    
    # Agregar tarea en segundo plano
    background_tasks.add_task(ejecutar_extraccion_background)
    
    return {
        "mensaje": "Extracción iniciada correctamente",
        "estado": estado_extraccion["estado"]
    }


@app.get("/estado", tags=["Extracción"], response_model=EstadoResponse)
async def obtener_estado():
    """
    Obtiene el estado actual de la extracción
    """
    return EstadoResponse(**estado_extraccion)


@app.get("/descargar/json", tags=["Descarga"])
async def descargar_json():
    """
    Descarga el archivo JSON con los datos extraídos
    """
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
    """
    Descarga el archivo Excel con los datos extraídos
    """
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
    """
    Obtiene los datos extraídos directamente en formato JSON
    """
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
    """
    Verifica el estado de salud de la API
    """
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
