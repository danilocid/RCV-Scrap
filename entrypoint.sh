#!/bin/bash

echo "Iniciando servidor en puerto 8080..."

# Ejecutar FastAPI usando python -m uvicorn evita problemas de PATH
exec python -m uvicorn api_server:app --host 0.0.0.0 --port 8080
