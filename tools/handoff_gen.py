#!/usr/bin/env python3
"""Handoff generator - Crea documentación de sesión"""

from pathlib import Path
from datetime import datetime

def generate_handoff(project: str, problem: str, solution: str, workspace: str = None):
    if workspace is None:
        workspace = str(Path(__file__).resolve().parent.parent)
    ws = Path(workspace) / "projects" / project
    ws.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now().strftime("%Y-%m-%d")
    filename = ws / f"HANDOFF_{today}.md"
    
    content = f"""# HANDOFF - {today} - Auto-generado

## Problema
{problem}

## Solución Implementada
{solution}

## Próximos Pasos
- [ ] Verificar integración con MementoBloom
- [ ] Actualizar documentación
"""
    
    filename.write_text(content)
    print(f"✓ Handoff creado: {filename}")
    return str(filename)

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        generate_handoff(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "Pendiente")
    else:
        print("Uso: python handoff_gen.py <proyecto> <problema> [solucion]")