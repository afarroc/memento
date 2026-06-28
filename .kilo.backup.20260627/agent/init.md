# Semilla inicial del agente MementoBloom

Objetivo: construir progresivamente un agente de memoria histórica para MementoBloom.

Flujo obligatorio:
1. Leer esta semilla inicial.
2. Cargar las instrucciones progresivas listadas abajo.
3. Leer `.kilo/START_CONTEXT.md` si existe, pero no lo trackees.
4. Usar `memory/graph/memory_index.json` como memoria compacta local.
5. Priorizar HANDOFF recientes de `projects/mementobloom`, `projects/Management360` y `projects/Ventas_Porta`.
6. Continuar desde el último handoff relevante sin pedir información ya registrada.
7. No destruir memoria, Redis ni handoffs salvo instrucción explícita.

# Instrucciones progresivas
#include instructions/00-core.md
#include instructions/10-context.md
#include instructions/20-memory.md
#include instructions/30-redis-panel.md
#include instructions/40-projects.md
#include instructions/90-safety.md
