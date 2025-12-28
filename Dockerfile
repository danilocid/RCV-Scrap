FROM python:3.11-slim

# Instalar dependencias esenciales del sistema
RUN apt-get update && apt-get install -y \
    wget gnupg curl unzip \
    && rm -rf /var/lib/apt/lists/*

# Instalar Playwright + Chromium (compatible con Raspberry Pi ARM64)
RUN pip install --no-cache-dir playwright && \
    playwright install --with-deps chromium

# Crear usuario no root
RUN useradd -ms /bin/bash appuser

WORKDIR /app

# Copiar requerimientos primero (optimiza caché)
COPY requirements.txt .

# Instalar dependencias de Python como root (uvicorn queda en /usr/local/bin)
RUN pip install --no-cache-dir -r requirements.txt

# Copiar la aplicación
COPY . .

# Asegurar permisos
RUN chown -R appuser:appuser /app && \
    chmod +x /app/entrypoint.sh

# Cambiar usuario final
USER appuser

ENTRYPOINT ["/app/entrypoint.sh"]
