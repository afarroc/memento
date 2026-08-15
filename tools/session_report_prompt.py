#!/usr/bin/env python3
"""Session report prompt generator.

Genera un prompt genérico para solicitar a un subagente externo un informe
de sesión listo para integrarse como handoff en MementoBloom.
"""

from pathlib import Path
from datetime import datetime


def generate_prompt(project: str, session_topic: str, extra_context: str = "", workspace: str = None):
    if workspace is None:
        workspace = str(Path(__file__).resolve().parent.parent)
    ws = Path(workspace)
    today = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""# INSTRUCCIÓN PARA SUBAGENTE EXTERNO — INFORME DE SESIÓN

## Encargo
- Proyecto: {project}
- Tema de la sesión: {session_topic}
- Contexto adicional: {extra_context}

## Tu rol
Eres un documentador de sesiones de desarrollo. Recibes contexto crudo de una sesión y devuelves un informe estructurado listo para integrarse como handoff en MementoBloom.

## Qué es un handoff
Un handoff es un archivo Markdown con secciones fijas que documenta una sesión para que otra sesión o agente pueda retomar el trabajo sin leer la conversación completa.

## Estructura obligatoria
Devuelve SOLO el handoff, sin saludos ni explicaciones adicionales:

# HANDOFF — Sesión <tema>

## Datos básicos
- **Proyecto:** {project}
- **Fecha/hora:** {today} HH:MM -0500
- **Tipo:** <tipo>

## Resumen
<resumen>

## Archivos modificados
1. `<ruta>`
2. `<ruta>`

## Próximos pasos
- <paso 1>
- <paso 2>

## Contexto previo
- <contexto 1>
- <contexto 2>

## Notas
- <nota 1>
- <nota 2>

## Reglas
- No incluyas saludos, preguntas ni contenido fuera del handoff.
- No inventes rutas ni archivos; si no los conoces, escribe "pendiente".
- Usa bullets y rutas absolutas cuando sea posible.
- Mantén el tono técnico y directo.
- No mezcles conceptos de dominio sin etiquetarlos claramente.
- Si hay código, usa bloques markdown con lenguaje.
- Devuelve SOLO el contenido Markdown. No incluyas explicaciones adicionales.
"""

    out_path = ws / "projects" / project / f"PROMPT_INFORME_{today}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(prompt, encoding="utf-8")
    print(f"✓ Prompt generado: {out_path}")
    return str(out_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Uso: python session_report_prompt.py <proyecto> <tema> [contexto_extra]")
        sys.exit(1)
    print(generate_prompt(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ""))
