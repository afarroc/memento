# 15 Credenciales y .env por proyecto

## Regla operativa (reforzada 2026-10-14)

**Cada proyecto con carpeta física puede y debe tener su `.env` local** con sus propias credenciales. Esto es el patrón correcto, no una excepción.

- Ubicación: `<repo físico del proyecto>/.env`
- Protección obligatoria: `chmod 600` + entrada `.env` en el `.gitignore` **del proyecto**
- Contenido: solo variables de ese proyecto (prefijo por proyecto, ej. `NANOBOT_*`)
- Carga: `set -a && source .env && set + a` antes de ejecutar tools del proyecto

## El .env del workspace memento

`/Volumes/Macintosh HD - Datos/mementobloom/.env` es **exclusivamente** para las herramientas del workspace (p. ej. `M360_*` del bridge). **No absorber las credenciales de los proyectos** — cada proyecto administra las suyas.

## Prohibiciones

1. **NUNCA eliminar un `.env` de proyecto** (ni moverlo, ni vaciarlo) sin verificar primero que **todos** sus valores existen duplicados en otra ubicación. Si no existen, mover su contenido al `.env` del workspace antes de cualquier eliminación.
2. NUNCA commitear `.env` en ningún repo.
3. NUNCA exponer valores de `.env` en handoffs, docs, logs o conversación.

## Lección que origina esta regla

El 2026-10-14 se eliminó el `.env` de `tiktok_agent_bot` por aplicar de forma mecánica "las credenciales van solo en el .env del workspace", sin comprobar que dicho `.env` no contenía esas variables. Resultado: se borró la única copia persistente y hubo que reconstruirla. **La regla anterior no invalida el .env por proyecto; la complementa.**
