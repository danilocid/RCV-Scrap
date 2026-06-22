FROM python:3.11-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Instalar Chromium y todas las dependencias del sistema como root
RUN apt-get update && \
    python -m pip install playwright && \
    playwright install --with-deps chromium && \
    rm -rf /var/lib/apt/lists/*

# Crear usuario sin privilegios
RUN useradd -m appuser
USER appuser

WORKDIR /app

# Copiar requirements
COPY --chown=appuser:appuser requirements.txt .

# Instalar dependencias Python (incluye Playwright)
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar el código
COPY --chown=appuser:appuser . .

# Dar permisos al entrypoint
RUN chmod +x /app/entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/app/entrypoint.sh"]
