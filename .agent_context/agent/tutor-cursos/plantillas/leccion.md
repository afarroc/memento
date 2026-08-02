# Plantilla de lección

Título: {{TITULO}}
Módulo: {{MODULO_ID}}
Order: {{ORDER}}
Tipo: text | quiz | assignment | video

## Contenido (markdown fuente)
{{CONTENIDO_MARKDOWN}}

## Conversión a HTML
```python
import markdown
html = markdown.markdown(
    contenido.replace("$", "\\$"),  # escapar moneda
    extensions=['tables', 'fenced_code']
)
```

## Si es quiz (evaluación)
- 5 preguntas de opción múltiple.
- Asociar a la lección con `lesson_type='quiz'`.
