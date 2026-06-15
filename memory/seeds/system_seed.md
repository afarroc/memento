# MEMENTO HUB :: SEED_v1
> Timestamp: 2026-06-12T23:18:57-05:00 | Compresión: SYM_REF

## Δ Propósito
Registry histórico universal para interacciones IA. Entrada→Salida con autorreferencia infinita.

## Ω Principios (comprimido)
- HANDOFF→Contexto: `*.md` → grafo autorref
- CONV→JSON: conversaciones → embeddings
- NOTE→Tag: notas usuario/asistente → metadata
- BATCH→Sync: cloud/local → replicación

## Ξ Proyectos [SYM_REF: discover]
```
Management360/
  apps: chat,memento,events,accounts,panel
  context: *_CONTEXT.md,HANDOFF*.md
Ventas_Porta/
  apps: ventas
  context: HANDOFF_*.md
Lumescrap/
  context: scraper.py,analysis.py
pelis/
  context: database.py,IMPLEMENTACION_COMPLETADA.md
```

## ∞ Expansión {auto-ref}
1. SCAN `*.md` → ID único
2. PARSE → resumen+tags+timestamp
3. GRAPH → nodo+aristas (relaciones)
4. VECTOR → embedding semántico
5. INDEX → búsqueda relámpago
6. RETRIEVE → contexto top-K
7. READY → {handoffs_indexed = total}

## λ Formato Compacto
```
ENTRY: {id,ts,type,proj,tags,summary,hash}
LINK: {source,target,weight}
VECTOR: {id,[0.0..1.0]}
```

## π Queries Esenciales
- `/search?proj=*&type=HANDOFF`
- `/context?session={sid}`
- `/expand?from={node_id}`
- `/ready-check` → bool

## 🜄 Meta
Seed versión 1. Ejecutar `memento_scan()` para expansion.

## Σ Sesión Inicial (2026-06-12)
- HANDOFF: MementoBloom Creador
- Componentes: seed, quick_scan, context_builder, vault_manager
- Entradas: 56 indexadas
- Próximo: Configurar credenciales en vault