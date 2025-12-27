# RCV Scrap - Extractor de Registro de Compras y Ventas SII

Sistema de automatización para extraer datos del Registro de Compras y Ventas (RCV) del Servicio de Impuestos Internos (SII) de Chile mediante **API REST**.

## 🎯 Características Principales

- ✅ **Extracción dinámica de tipos de documento** - Detecta automáticamente los tipos disponibles en el período
- ✅ **Parámetros opcionales** - Usa mes/año actual si no se especifican
- ✅ **Múltiples tipos simultáneos** - Procesa todos los tipos de documento en una sola ejecución
- ✅ **Extracción de razón social** - Obtiene nombre del emisor desde el detalle del documento
- ✅ **Navegación inteligente** - Vuelve al resumen entre cada tipo para mantener estabilidad
- ✅ **Eliminación de duplicados** - Limpia registros repetidos por Folio
- ✅ **API REST profesional** - FastAPI con documentación automática (Swagger/ReDoc)

## 📋 Requisitos

### Librerías Python

Instalar todas las dependencias desde el archivo requirements.txt:

```bash
pip install -r requirements.txt
```

O instalar manualmente:

```bash
pip install fastapi uvicorn playwright python-dotenv pandas openpyxl
```

Después de instalar Playwright, ejecutar:

```bash
playwright install chromium
```

## 📁 Estructura del Proyecto

```
RCV_scrap/
├── main.py           # Punto de entrada (32 líneas - solo inicia API)
├── extractor.py      # Orquestación del scraping y lógica de negocio
├── api_server.py     # Servidor FastAPI con todos los endpoints
├── config.py         # Configuración y constantes del sistema
├── scraper.py        # Navegación web, extracción y parsing (Playwright)
├── procesador.py     # Procesamiento y limpieza de datos
├── guardador.py      # Exportación de datos (JSON, Excel)
├── requirements.txt  # Dependencias del proyecto
├── .env              # Variables de entorno (credenciales)
├── .env.example      # Plantilla de variables de entorno
├── .gitignore        # Archivos excluidos del control de versiones
└── README.md         # Esta documentación
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

### Extracción Inteligente

- ✅ **Detección automática de tipos de documento** - Lee la tabla de resumen para saber qué tipos están disponibles
- ✅ **Login automático** en el portal Mi SII
- ✅ **Selección de período** - Mes y año configurables (usa actual por defecto)
- ✅ **Extracción completa** - Todos los tipos de documento disponibles (33, 34, 39, 41, 43, 46, 52, 56, 61, 110, 111, 112)
- ✅ **Navegación robusta** - Vuelve al resumen entre cada tipo de documento
- ✅ **Razón social del emisor** - Extrae el nombre desde el detalle de cada documento

### Procesamiento de Datos

- ✅ **Eliminación de duplicados** por Folio
- ✅ **Limpieza de datos** - Elimina valores NaN y vacíos
- ✅ **Exportación dual** - JSON estructurado y Excel con pandas
- ✅ **Metadata completa** - Incluye período, tipos procesados, fecha de extracción

### 🌐 Iniciar el Servidor API

El sistema funciona exclusivamente como API REST:

```bash
python main.py
```

**Servidor disponible en:**

- API: `http://localhost:8000`
- Documentación Swagger: `http://localhost:8000/docs`
- Documentación ReDoc: `http://localhost:8000/redoc`

### 📡 Endpoints Disponibles

| Método | Endpoint           | Descripción                                            |
| ------ | ------------------ | ------------------------------------------------------ |
| GET    | `/`                | Información de la API y tipos de documento disponibles |
| POST   | `/extraer`         | **Inicia extracción** (mes/año/tipos opcionales)       |
| GET    | `/estado`          | Consulta el estado de la extracción en curso           |
| GET    | `/datos`           | Obtiene los datos extraídos en formato JSON            |
| GET    | `/descargar/json`  | Descarga el archivo JSON generado                      |
| GET    | `/descargar/excel` | Descarga el archivo Excel generado                     |
| GET    | `/health`          | Health check del servidor                              |

### 🔥 Ejemplos de Uso

**1. Extracción con período actual y TODOS los tipos:**

```bash
curl -X POST http://localhost:8000/extraer
```

_Extrae todos los tipos de documento disponibles del mes/año actual_

**2. Extracción para período específico:**

```bash
curl -X POST http://localhost:8000/extraer \
  -H "Content-Type: application/json" \
  -d '{"mes": 11, "anio": 2025}'
```

_Extrae todos los tipos disponibles de noviembre 2025_

**3. Extracción selectiva de tipos:**

```bash
curl -X POST http://localhost:8000/extraer \
  -H "Content-Type: application/json" \
  -d '{"mes": 12, "anio": 2025, "tipos_documento": ["33", "39", "61"]}'
```

_Extrae solo Facturas (33), Boletas (39) y Notas de Crédito (61) de diciembre 2025_

**4. Consultar estado:**

```bash
curl http://localhost:8000/estado
```

**5. Descargar datos:**

```bash
curl -O http://localhost:8000/descargar/json
curl -O http://localhost:8000/descargar/excel
```

```bash
python main.py
# o explícitamente:
python main.py --mode api
```

**Características del modo API:**

### 🔄 Flujo de Extracción

El sistema ejecuta los siguientes pasos automáticamente:

1. **Login** - Autenticación en el portal Mi SII
2. **Navegación** - Acceso al módulo RCV
3. **Selección de período** - Mes/año (actual por defecto)
4. **Detección de tipos** - Lee tabla "Resúmenes por tipo de documento"
5. **Extracción iterativa:**
   - Navega al detalle del tipo de documento
   - Extrae datos de la tabla
   - Obtiene razón social de cada registro
   - **Vuelve al resumen** (excepto en el último tipo)
6. **Procesamiento** - Elimina duplicados y limpia datos
7. **Exportación** - Genera JSON y Excel

### 📊 Respuestas de Estado

El endpoint `/estado` devuelve:

| Estado       | Descripción                         |
| ------------ | ----------------------------------- |
| `inactivo`   | No hay extracción en curso          |
| `en_proceso` | Extracción actualmente ejecutándose |
| `completado` | Extracción finalizada con éxito     |
| `error`      | Error durante la extracción         |

**Ejemplo de respuesta:**

```json
{
  "estado": "completado",
  "mensaje": "Extracción completada",
  "fecha_inicio": "2025-01-15T10:30:00",
  "fecha_fin": "2025-01-15T10:35:20",
  "total_registros": 1523,
  "periodo": { "mes": 12, "anio": 2025 },
  "tipos_documento": ["33", "34", "39", "61"]
}
```

## 📊 Formato de Salida

Los archivos generados (`datos_rcv.json` y `datos_rcv.xlsx`) contienen:

```json
{
  "fecha_extraccion": "2025-01-15 10:35:20",
  "periodo": {
    "mes": 12,
    "anio": 2025
  },
  "tipos_documento_procesados": ["33", "34", "39", "61"],
  "total_registros": 1523,
  "datos": [
    {
      "Tipo": "33",
      "RUT Proveedor": "76341652-6",
      "Razon Social": "MERCADOLIBRE S.R.L.",
      "Folio": "12345",
      "Fecha Docto.": "01/12/2025",
      "Fecha Recepción": "01/12/2025",
      "Monto Neto": "100000",
      "Monto IVA": "19000",
      "Monto Total": "119000"
    }
  ]
}
```

### Campos Extraídos

- **Metadata**: Fecha extracción, período (mes/año), tipos procesados, total
- **Tipo**: Código SII del documento (33, 34, 39, etc.)
- **RUT**: RUT completo con dígito verificador
- **Razón Social**: Nombre del emisor (extraído del detalle del documento)
- **Folio**: Número único del documento
- **Fechas**: Documento, recepción, acuse (según disponibilidad)
- **Montos**: Neto, IVA, Total, Exento (según tipo de documento)

---

## 🛠️ Arquitectura y Desarrollo

### Módulos del Sistema

| Archivo         | Líneas | Responsabilidad                                    |
| --------------- | ------ | -------------------------------------------------- |
| `main.py`       | 32     | Punto de entrada, inicia servidor API              |
| `extractor.py`  | 177    | Orquestación del scraping, lógica de negocio       |
| `api_server.py` | 250    | Servidor FastAPI, endpoints, estado global         |
| `scraper.py`    | 340+   | Playwright: login, navegación, parsing, extracción |
| `config.py`     | ~100   | Constantes, URLs, timeouts, tipos de documento     |
| `procesador.py` | ~80    | Limpieza de datos, eliminación de duplicados       |
| `guardador.py`  | ~60    | Exportación a JSON y Excel (pandas)                |

### Tipos de Documento Soportados

```python
TIPOS_DOCUMENTO = {
    "33": "Factura Electrónica",
    "34": "Factura Exenta Electrónica",
    "39": "Boleta Electrónica",
    "41": "Boleta Exenta Electrónica",
    "43": "Liquidación-Factura Electrónica",
    "46": "Factura de Compra Electrónica",
    "52": "Guía de Despacho Electrónica",
    "56": "Nota de Débito Electrónica",
    "61": "Nota de Crédito Electrónica",
    "110": "Factura de Exportación Electrónica",
    "111": "Nota de Débito de Exportación Electrónica",
    "112": "Nota de Crédito de Exportación Electrónica"
}
```

### Extender Funcionalidades

**Agregar nuevos endpoints:**

- Editar [api_server.py](api_server.py)
- Usar la función `estado_extraccion` global para consultar estado

**Modificar extracción:**

- [extractor.py](extractor.py) contiene la lógica principal
- [scraper.py](scraper.py) tiene las funciones de navegación
- Método `volver_a_resumen()` mantiene estabilidad entre tipos

**Cambiar selectores (si SII actualiza portal):**

- Actualizar IDs en [scraper.py](scraper.py): `select#periodoMes`, `select#periodoAnho`
- Revisar regex para detectar tipos: `r'#detalle/(\d+)'`

---

- Utiliza `.env.example` como plantilla sin datos sensibles

```

```
