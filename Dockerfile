FROM python:3.11-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Actualizar sistema e instalar dependencias de Chromium
RUN apt-get update && apt-get install -y \
    wget unzip git curl \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxrandr2 \
    libxdamage1 libxfixes3 libpango-1.0-0 libcairo2 \
    libasound2 libatspi2.0-0 libxshmfence1 xvfb \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario sin privilegios
RUN useradd -m appuser
USER appuser

WORKDIR /app

# Copiar requirements
COPY --chown=appuser:appuser requirements.txt .

# Instalar dependencias Python (incluye Playwright)
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Instalar Chromium para Playwright
RUN playwright install chromium

# Copiar el código
COPY --chown=appuser:appuser . .

# Dar permisos al entrypoint
RUN chmod +x /app/entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/app/entrypoint.sh"]
