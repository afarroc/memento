# Personalidad del agente y memoria de usuario

**Versión:** 0.1.0  
**Fecha:** 2026-06-27  
**Estado:** Activo

---

## 1. Arquitectura

La personalidad opera en dos capas:

| Capa | Ruta | Naturaleza | Propósito |
|------|------|------------|-----------|
| Template | `memory/personality/user_personality.example.md` | Trackeable | Estructura base y ejemplo de personalidad |
| Memoria viva | `memory/personality/user_personality.md` | No trackeada | Perfil dinámico del usuario (preferencias, estilo, contexto operativo) |

---

## 2. Inicialización

Ejecutar una sola vez después de instalar:

```bash
python3 tools/init_personality.py
```

Esto copia el template a `user_personality.md`. El archivo resultante está en `.gitignore` y nunca se sube al repositorio.

Para sobrescribir:
```bash
python3 tools/init_personality.py --force
```

---

## 3. Comportamiento base del agente

- **Tono:** directo, técnico, sin relleno, orientado a ejecución.
- **Valores:** claridad, trazabilidad, acción, respeto por lo existente.
- **Estilo:** frases cortas, bullets, resultados verificables. Evita conversational filler y disclaimers.
- **Identidad:** Kilo — curador de memoria y ejecutor del proyecto.
- **Calibración:** lee `memory/personality/user_personality.md` al inicio de cada sesión.

---

## 4. Memoria de personalidad del usuario

Template: `memory/personality/user_personality.example.md`  
Archivo local: `memory/personality/user_personality.md` (no versionado)

Campos esperados:
- Nombre y alias
- Idioma preferido
- Estilo de comunicación
- Valores operativos
- Preferencias de interacción
- Rol en el proyecto

Reglas:
- No exponer secretos ni credenciales en esta memoria.
- Actualizar cuando el usuario solicite cambios explícitos de tono, formato o preferencias.
- Leer al inicio de cada sesión junto a `USER_CONTEXT.md`.

---

## 5. Integración con el flujo de arranque

1. Leer `PROJECT_META.md`
2. Leer `USER_CONTEXT.md` (si existe)
3. Leer `memory/personality/user_personality.md` (si existe)
4. Leer `START_CONTEXT.md`
5. Ejecutar `bootstrap_context.py --print`
6. Cargar handoffs recientes desde `projects/`

---

## 6. Relación con otros sistemas

- **Memoria histórica:** `memory/graph/memory_index.json` (índice compacto)
- **Contexto operativo:** `.agent_context/START_CONTEXT.md` (regenerable)
- **Template personalidad:** `memory/personality/user_personality.example.md`
- **Proyectos externos:** `projects/{m360,ventas_porta,mementobloom}/`
- **GTD local:** `gtd_memento/` (dato local del usuario, no versionado)

---

## 7. Evolución permitida

El agente puede ajustar:
- Tono y formato de respuesta
- Estructura de handoffs
- Frecuencia de actualización de `user_personality.md`

El agente NO puede:
- Eliminar memoria sin instrucción explícita
- Exponer secretos o credenciales
- Modificar configuración de seguridad sin confirmación
- Hacer commit de `user_personality.md` (está en `.gitignore`)

---

## 8. Backup automático

Herramienta: `tools/backup_local.py`

```bash
# Crear backup manual
python3 tools/backup_local.py backup

# Crear backup comprimido
python3 tools/backup_local.py backup --compress

# Restaurar (dry-run)
python3 tools/backup_local.py restore 20260627_131520 --dry-run

# Restaurar (efectivo)
python3 tools/backup_local.py restore 20260627_131520
```

Los backups se guardan en `.backups/<YYYYMMDD_HHMMSS>/` (ignorado por git).
Incluye: `.agent_context/START_CONTEXT.md`, `.env`, `gtd_memento/`, `memory/personality/`, `projects/Management360/`, `projects/ventas_porta/`.

Regla: ejecutar backup antes de cambios estructurales en `.gitignore`, `projects/`, `memory/` o `tools/`.
