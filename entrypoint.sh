#!/bin/sh
PORT=${PORT:-8080}

echo "Iniciando servidor en puerto $PORT..."
exec uvicorn api_server:app --host 0.0.0.0 --port $PORT
