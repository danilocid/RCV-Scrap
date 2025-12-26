# 🚧 Este proyecto está en desarrollo

# RCV Scrap - Extractor de Registro de Compras y Ventas SII

Sistema de automatización para extraer datos del Registro de Compras y Ventas (RCV) del Servicio de Impuestos Internos (SII) de Chile.

## 📋 Requisitos

### Librerías Python

```bash
pip install playwright python-dotenv pandas openpyxl
```

Después de instalar Playwright, ejecutar:

```bash
playwright install chromium
```

## 📁 Estructura del Proyecto

```
RCV_scrap/
├── main.py           # Punto de entrada principal
├── config.py         # Configuración y constantes del sistema
├── scraper.py        # Módulo de extracción web (login, navegación, parseo)
├── procesador.py     # Procesamiento y limpieza de datos
├── guardador.py      # Exportación de datos (JSON, Excel)
├── .env              # Variables de entorno (credenciales)
├── .env.example      # Plantilla de variables de entorno
└── .gitignore        # Archivos excluidos del control de versiones
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
- ✅ Extracción de razón social del emisor desde el detalle
- ✅ Limpieza y eliminación de duplicados
- ✅ Exportación a JSON y Excel
- ✅ Manejo robusto de errores (timeout, credenciales incorrectas)
- ✅ Arquitectura modular para fácil mantenimiento

## 💻 Uso

```bash
python main.py
```

### Flujo de Ejecución

El script realiza las siguientes operaciones:

1. **Validación**: Verifica que las credenciales estén configuradas
2. **Login**: Se conecta al portal del SII con tus credenciales
3. **Navegación**: Accede al módulo RCV y selecciona facturas tipo 33
4. **Extracción**:
   - Lee las tablas de datos
   - Extrae razón social de cada documento
5. **Procesamiento**:
   - Elimina registros duplicados
   - Limpia valores vacíos o nulos
6. **Exportación**:
   - `datos_rcv.json`: Datos estructurados en formato JSON
   - `datos_rcv.xlsx`: Archivo Excel con los registros

### Salida de Datos

Los archivos generados contienen:

- Fecha de extracción
- Tipo de documento
- Datos completos de cada factura:
  - RUT Proveedor/Cliente
  - Folio
  - Fechas (documento, recepción, acuse)
  - Montos (neto, IVA, total)
  - Razón Social del Emisor
  - Otros campos específicos del RCV

## 🔒 Seguridad

- El archivo `.env` está incluido en `.gitignore` para proteger las credenciales
- Los archivos JSON y Excel generados también están en `.gitignore`
- Nunca subas tus credenciales al repositorio
- Utiliza `.env.example` como plantilla sin datos sensibles
