FROM python:3.11-slim

# Evita mensajes interactivos
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crea un usuario no root (Cloud Run recomendable)
RUN adduser --disabled-password appuser
USER appuser

# Define el directorio de trabajo
WORKDIR /app

# Copia requirements antes para aprovechar cache
COPY --chown=appuser:appuser requirements.txt /app/requirements.txt

# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia toda la aplicación
COPY --chown=appuser:appuser . /app

# Asegura permisos del entrypoint
RUN chmod +x /app/entrypoint.sh

# Cloud Run define PORT, pero definimos uno por defecto
ENV PORT=8080

# Exponemos el puerto localmente (no usado por Cloud Run)
EXPOSE 8080

# Inicia el servidor
ENTRYPOINT ["/app/entrypoint.sh"]
