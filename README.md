# 🚧 Este proyecto está en desarrollo

# RCV Scrap - Extractor de Registro de Compras y Ventas SII

Sistema de automatización para extraer datos del Registro de Compras y Ventas (RCV) del Servicio de Impuestos Internos (SII) de Chile.

## 📋 Requisitos

### Librerías Python

```bash
pip install playwright python-dotenv
```

Después de instalar Playwright, ejecutar:

```bash
playwright install chromium
```

## ⚙️ Configuración

### Variables de Entorno

Crear un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
SII_RUT=tu-rut-completo
SII_CLAVE=tu-clave-tributaria
AMBIENTE=DEV
```

**Ejemplo:**

```env
SII_RUT=12345678-9
SII_CLAVE=MiClave123
AMBIENTE=DEV
```

#### Descripción de Variables

- `SII_RUT`: RUT completo con dígito verificador (ej: 12345678-9)
- `SII_CLAVE`: Contraseña tributaria del SII
- `AMBIENTE`: Entorno de ejecución
  - `DEV`: Modo desarrollo (muestra el navegador)
  - `PROD` o cualquier otro valor: Modo producción (navegador oculto)

## 🚀 Funcionalidades

- ✅ Login automático en el portal Mi SII
- ✅ Navegación automática al módulo RCV
- ✅ Extracción de datos de facturas electrónicas (tipo 33)
- ✅ Obtención de tablas HTML con información del registro

## 💻 Uso

```bash
python main.py
```

El script:

1. Se conecta al portal del SII
2. Inicia sesión con las credenciales configuradas
3. Navega al Registro de Compras y Ventas
4. Extrae y muestra el contenido de las tablas encontradas

## 🔒 Seguridad

- El archivo `.env` está incluido en `.gitignore` para proteger las credenciales
- Nunca subas tus credenciales al repositorio
- Utiliza `.env.example` como plantilla sin datos sensibles
