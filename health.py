"""
Health check endpoint para Cloud Run
"""
import os
from datetime import datetime

def health_check():
    """
    Verifica que el servicio esté respondiendo
    """
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "port": os.environ.get("PORT", "8000"),
        "ambiente": os.environ.get("AMBIENTE", "DEV")
    }
