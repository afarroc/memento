# CATÁLOGO DE PRODUCTOS - PROPUESTA RETAIL FASE 2

## RESUMEN EJECUTIVO

Transformar el sistema de ventas de Ventas_Porta de hardcodeo estático a catálogo dinámico gestionado por marketing, con soporte para multiples proveedores y compatibilidad chip-equipo.

## ESTADO ACTUAL

### Hardcodeo Detectado
- `models.py`: PLANES_CHIP, MODELOS_CHIP_LIST, PRECIOS_PREPAGO, PRECIOS_POSTPAGO, TIPO_RENTA_TABLE
- `views.py`: planPrecioMap duplicado
- `venta-form.js`: tipoRentaTable duplicado
- Inconsistencias: planes ENTEL_LIBRE_* faltantes en PLANES_CHIP

### Validación Producto
✅ Implementada: endpoint /api/ventas/validar-producto/, template btnValidarProducto, id_producto_validado

## ARQUITECTURA PROPUESTA

### Entidades Principales

```
Producto (sku único)
├── EQUIPO: iPhone XX, Moto G Play, etc
└── CHIP: chip-entel-power, chip-virgin-freedom, etc

Oferta (producto + condición)
├── plan_codigo, plan_precio_mes
├── tipo_linea (PREPAGO/POSTPAGO)
├── origen (PORTABILIDAD/LINEA_NUEVA)
├── precio_equipo, contrato_meses
└── proveedor (ENTEL, CLARO, VIRGIN)

ChipCompatibilidad (equipo ↔ chip)
Venta
ItemVenta
├── tipo: CHIP | EQUIPO
├── producto (FK → Producto)
├── oferta (FK → Oferta)
└── despacho_programado, fecha_despacho
```

## FLUJO DE NEGOCIO

### Escenario Portabilidad
1. Vendedor: "Cliente quiere iPhone XX con portabilidad"
2. Sistema: GET /api/catalogo/productos/IPHONE_XX/ofertas/?origen=PORTABILIDAD
3. Respuesta: [{plan: "CONTROL 199", precio: "$1", contrato: "18 meses"}, ...]
4. Sistema: GET /api/catalogo/equipos/IPHONE_XX/chips/
5. Respuesta: [{sku: "CHIP_ENTEL_POWER", compatibilidad: true}]

### Escenario Línea Nueva
1. Vendedor: "Cliente quiere línea nueva"
2. Sistema: GET /api/catalogo/productos/?tipo_linea=PREPAGO&origen=LINEA_NUEVA
3. Respuesta: solo productos con ofertas disponibles

## BRANCH Y SETUP

```bash
git -C "/Volumes/Macintosh HD - Datos/projects/Ventas_Porta" checkout -b feature/catalogo-productos-retail
```

Workspace: `/Volumes/Macintosh HD - Datos/projects/Ventas_Porta`

## ARCHIVOS A CREAR

- apps/catalogo/models.py
- apps/catalogo/views.py
- apps/catalogo/urls.py
- apps/catalogo/admin.py
- apps/catalogo/migrations/0001_initial.py

## MIGRACIÓN DE DATOS

Seed desde hardcodeo actual:
- 21 modelos → Producto (EQUIPO)
- 8 planes CHIP → Producto (CHIP)
- 14 planes → ProveedorCatalogo references
- 16 combinaciones POSTPAGO → Oferta
- 8 precios PREPAGO → Oferta

## ENDPOINTS API

| Método | URL | Descripción |
|--------|-----|-------------|
| GET | /api/catalogo/productos/ | Productos disponibles |
| GET | /api/catalogo/productos/{sku}/ofertas/ | Ofertas de un producto |
| GET | /api/catalogo/equipos/{sku}/chips/ | Chips compatibles |
| POST | /api/catalogo/ofertas/validar/ | Validar oferta (futuro) |

## ADMIN PARA MARKETING

ProveedorCatalogo: gestión de proveedores
Producto: CRUD equipo/chip
Oferta: CRUD precios/plan/origen/tipo_línea
ChipCompatibilidad: Asociar chips a equipos

## IMPACTO TÉCNICO

- Backend: 3 nuevos modelos
- Frontend: 2 endpoints AJAX nuevos
- DB: 3 tablas nuevas
- Tests: validar migración de precios

## CHECKLIST

- [x] Crear estructura apps/catalogo/
- [x] Generar migration seed
- [x] Implementar endpoints
- [x] Modificar VentaForm (con fallback legacy)
- [x] Actualizar templates
- [x] Tests integración (34/34 pasados)
- [x] Documentar seed datos

## ESTADO IMPLEMENTACIÓN (2026-06-21)

- **Completado**: 35 productos, 1106 ofertas, 66 compatibilidades cargados
- **Branch activo**: `feature/catalogo-productos-retail`
- **Tests**: 34/34 pasados
- **Pendiente**: Decidir ofertas con `confianza='REVISION'` (16 ofertas)