# PROPUESTA - CATÁLOGO DE PRODUCTOS RETAIL

## 1. OBJETIVO DE NEGOCIO

Reemplazar la lógica hardcodeada de precios y productos con un catálogo administrable por marketing, soportando multiples proveedores (ENTEL, CLARO, VIRGIN) y la compatibilidad entre chips y equipos para optimizar el proceso de venta.

## 2. PROBLEMAS ACTUALES

### 2.1 Hardcodeo Múltiple
El sistema tiene precios y productos definidos en 4 ubicaciones distintas que no se sincronizan:
- Models.py: constantes PLANES_CHIP, PRECIOS_PREPAGO, PRECIOS_POSTPAGO
- Views.py: diccionario planPrecioMap duplicado de lógica
- Forms.py: validaciones con referencias hardcodeadas
- JavaScript: tabla tipoRentaTable duplicada completa

### 2.2 Inconsistencias Detectadas
- Los planes ENTEL_LIBRE_149_LIBRE y ENTEL_LIBRE_99_LIBRE aparecen en planPrecioMap pero no en PLANES_CHIP
- Precios sospechosos: varios equipos tienen precio 1 en combinaciones PACK+postpago (error de digitación probable)
- Faltan planes ENTEL_CONTROL_199_CONTROL en PRECIOS_POSTPAGO

### 2.3 Falta de Flexibilidad
- Cada nuevo equipo requiere modificación manual en código
- No hay histórico de cambios de precios
- Imposible gestionar ofertas por proveedor

## 3. ARQUITECTURA PROPUESTA

### 3.1 Entidades Principales

**Producto** - Item único de venta (equipo o chip)
- SKU único como identificador (ej: MOTO_G_PLAY, CHIP_ENTEL_POWER)
- Tipo: EQUIPO o CHIP
- Marca y nombre descriptivo
- Stock actual y mínimo para inventario
- Estado activo

**ProveedorCatalogo** - Proveedores de ofertas
- Código único (ENTEL, CLARO, VIRGIN, MOVISTAR)
- Nombre descriptivo
- Estado activo

**Oferta** - Relación producto-proveedor-condiciones
- Producto asociado (equipo o chip)
- Proveedor que ofrece
- Código y tipo de plan
- Precio del plan mensual
- Precio del equipo en esta oferta
- Tipo de línea (PREPAGO/POSTPAGO)
- Origen (PORTABILIDAD/LINEA_NUEVA)
- Meses de contrato
- Disponibilidad y fechas de vigencia

**ChipCompatibilidad** - Relación N:N entre equipos y chips
- Equipo compatible con chip específico
- Estado de disponibilidad

### 3.2 Flujo de Negocio

**Venta en Portabilidad:**
1. Vendedor selecciona origen = PORTABILIDAD
2. Sistema filtra equipos con ofertas disponibles
3. Vendedor elige equipo (ej: MOTO_G_PLAY)
4. Sistema muestra ofertas: plan CONTROL 199 - equipo $1 - 18 meses
5. Sistema filtra chips compatibles con equipo
6. Vendedor elige chip (ej: CHIP_ENTEL_POWER)
7. Venta registra 2 items: CHIP + EQUIPO

**Venta en Línea Nueva:**
1. Vendedor selecciona origen = LINEA_NUEVA
2. Sistema filtra productos según tipo línea
3. Vendedor elige producto disponible
4. Se registra item único o combo

## 4. CAMBIOS EN MODELO VENTA

### 4.1 ItemVenta Ampliado

Campos actuales:
- tipo_venta (genérico)
- tipo_producto (genérico)
- precio_plan (genérico)

Nuevos campos:
- tipo: CHIP o EQUIPO
- producto: FK a Producto (sku)
- oferta: FK a Oferta
- cantidad: integer (default 1)
- precio_unitario: decimal (desde oferta)
- despacho_programado: boolean
- fecha_despacho: date

## 5. ENDPOINTS API REQUERIDOS

### 5.1 CatalogoProductosAPI
GET /api/catalogo/productos/
Query params: origen, tipo_linea, incluir_chips
Retorna: lista de productos con sus ofertas disponibles

### 5.2 OfertasPorProductoAPI
GET /api/catalogo/productos/{sku}/ofertas/
Query params: origen, tipo_linea
Retorna: ofertas específicas del producto

### 5.3 ChipsCompatiblesAPI
GET /api/catalogo/equipos/{sku}/chips/
Retorna: chips compatibles con el equipo

## 6. ADMINISTRACIÓN

**ProveedorCatalogo:** Lista de proveedores de productos
**Producto:** CRUD completo de equipos y chips
**Oferta:** Gestión de precios, planes, proveedores y condiciones
**ChipCompatibilidad:** Relación equipo-chíp

Cada sección con filtros, búsquedas y exportación.

## 7. MIGRACION DE DATOS

Pasos:
1. Crear tabla Producto desde MODELO_PRODUCTO_CHOICES
2. Identificar chips en MODELOS_CHIP_LIST y PLANES_CHIP
3. Crear tabla Oferta desde PRECIOS_POSTPAGO y PRECIOS_PREPAGO
4. Migrar TIPO_RENTA_TABLE como metadata en Oferta
5. Setup ProveedorCatalogo (ENTEL principal)

Advertencias:
- Precio 1 en combinaciones equivocado
- Validar que todos los planes tengan referencia
- Verificar compatibilidad chip-equipo

## 8. BRANCH DE TRABAJO

Branch: feature/catalogo-productos-retail
Repositorio: /Volumes/Macintosh HD - Datos/projects/Ventas_Porta
Commit base: 33fca40 (centralizar reglas de precio)

## 9. CHECKLIST DE IMPLEMENTACIÓN

- [x] Crear estructura apps/catalogo/
- [x] Modelos Producto, ProveedorCatalogo, Oferta, ChipCompatibilidad
- [x] Migration seed con datos actuales (35 productos, 1106 ofertas)
- [x] Endpoints API (/api/catalogo/*)
- [x] Modificar VentaForm para usar catálogo (con fallback legacy)
- [x] Templates con carga AJAX de productos
- [x] Admin completo para marketing
- [x] Tests de integración (34/34 pasados)
- [x] Validación de migración precios
- [ ] Eliminar hardcodeo existente (Fase 2)