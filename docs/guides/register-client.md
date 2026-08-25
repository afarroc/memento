# Procedimiento — Registrar y mantener clientes en mementobloom

**Herramienta:** `tools/register_client.py`  
**Propósito:** registro inicial, actualización conservadora, migración masiva y validación de estructura de proyectos cliente.

---

## 1. Estructura canónica

```
projects/CLIENT_NAME/
├── PROJECT_CONTEXT.md
├── README.md
├── .gitignore
├── handoffs/
├── docs/
│   ├── guides/
│   ├── runbooks/
│   └── reference/
├── memory/
│   └── graph/
│       └── memory_index.json
└── src/
```

Reglas:
- `PROJECT_CONTEXT.md` es la fuente de verdad del registro.
- `docs/` almacena procedimientos permanentes.
- `memory/` es local al cliente; no se comparte entre clientes.
- Handoffs y memoria no se tocan en migraciones.

---

## 2. Comandos

### 2.1 Registrar cliente nuevo

```bash
python3 tools/register_client.py --name Ventas_Porta
python3 tools/register_client.py --name Administracion_UPN --from-project ../otros_proyectos/Admin_UPN
```

### 2.2 Actualizar cliente existente

```bash
python3 tools/register_client.py --update Ventas_Porta
python3 tools/register_client.py --update Management360 --force
```

- Por defecto preserva todo el contenido existente.
- `--force` actualiza `PROJECT_CONTEXT.md`, `README.md` y `.gitignore` solo si se desea refrescarlos.

### 2.3 Migrar todos los clientes

```bash
python3 tools/register_client.py --migrate-all --dry-run
python3 tools/register_client.py --migrate-all
```

### 2.4 Validar estructura

```bash
python3 tools/register_client.py --validate
python3 tools/register_client.py --validate --json
```

### 2.5 Listar clientes

```bash
python3 tools/register_client.py --list
python3 tools/register_client.py --list --json
```

### 2.6 Sincronizar registry global

```bash
python3 tools/register_client.py --sync
python3 tools/register_client.py --sync --json
```

Output: `.agent_context/secure/client_projects.json`

---

## 3. Nomenclatura

- Cliente: **kebab-case**, sin espacios.
- Ejemplos válidos: `Ventas_Porta`, `Administracion_UPN`, `Management360`, `jewelry_catalog`.

---

## 4. Post-registro

Después de registrar un cliente:

1. Editar `PROJECT_CONTEXT.md` para completar:
   - Fuente, repo, rama, venv, producción, servicios.
   - Tipo, dominio memoria, relación con mementobloom.
2. Registrar procedimientos específicos en `docs/guides/` y `docs/runbooks/`.
3. Si el cliente requiere integración M360, documentar nomenclatura de items en `docs/` o en `PROJECT_CONTEXT.md` según corresponda.
4. Ejecutar `python3 tools/register_client.py --sync` para actualizar el registry global.

---

## 5. Integración M360 por cliente

La integración con `tools/m360_bridge/client.py` es específica por cliente y se define post-registro.

- `Management360`: bridge activo, nomenclatura `M360-REVIEW-*`, `DIGIT-*`, `CV-REVIEW-*`, etc.
- Otros clientes: definir en `PROJECT_CONTEXT.md` o `docs/` si aplica.

No hardcodear `bridge_m360` en el template genérico.

---

## 6. Troubleshooting

| Problema | Solución |
|----------|----------|
| Cliente no aparece en `--list` | Verificar que exista `projects/CLIENTE/PROJECT_CONTEXT.md` |
| `client_projects.json` desactualizado | Ejecutar `python3 tools/register_client.py --sync` |
| Estructura incompleta | Ejecutar `python3 tools/register_client.py --validate` y luego `--update CLIENTE` |
| Handoffs o memoria perdidos | La migración nunca borra estos archivos; verificar ruta y permisos |
