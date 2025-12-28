# Imagen base compatible ARM64 para Raspberry Pi
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Instalar dependencias necesarias para Chromium en ARM
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario
RUN adduser --disabled-password appuser
USER appuser

WORKDIR /app

# Copiar requerimientos
COPY --chown=appuser:appuser requirements.txt /app/

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Instalar NAVAGADORES Playwright (incluye Chromium ARM64)
RUN playwright install chromium

# Copiar el código
COPY --chown=appuser:appuser . /app

# Permisos
RUN chmod +x /app/entrypoint.sh

# Exponer API
EXPOSE 8080

ENTRYPOINT ["./entrypoint.sh"]
