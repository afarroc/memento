#!/usr/bin/env python3
"""Genera/actualiza el dashboard HTML de microformatos UPN desde Documentos_Escaneados/microformatos/."""

import argparse
import json
import hashlib
import os
from pathlib import Path
from datetime import datetime
from collections import Counter

ENV_BASE = "UPN_DOCS_ROOT"


def detect_base() -> Path:
    """Resuelve BASE sin hardcodear paths absolutos."""
    # 1. CLI arg
    parser = argparse.ArgumentParser(description="Dashboard microformatos UPN")
    parser.add_argument("--base", help="Ruta base de Documentos_Escaneados (con microformatos/ y dashboard/ adentro)")
    parser.add_argument("--output", help="Ruta de salida del HTML (default: <base>/dashboard/index.html)")
    args = parser.parse_args()

    base = None
    if args.base:
        base = Path(args.base)
    else:
        env_base = os.environ.get(ENV_BASE)
        if env_base:
            base = Path(env_base)

    if not base:
        # 2. Búsqueda relativa al workspace
        try:
            ws = Path(__file__).resolve().parent.parent
            candidates = [
                ws.parent / "otros_proyectos" / "Administracion_UPN" / "Documentos_Escaneados",
                ws / "projects" / "Administracion_UPN" / "Documentos_Escaneados",
            ]
            for candidate in candidates:
                if candidate.exists() and (candidate / "microformatos").exists():
                    base = candidate
                    break
        except Exception:
            pass

    if not base:
        raise FileNotFoundError(
            f"UPN Documentos_Escaneados no encontrado. "
            f"Pasar --base / setear env {ENV_BASE} / tenerlo en ruta relativa conocida."
        )
    return base, args.output


BASE, OUTPUT_ARG = detect_base()
MICROFORMATOS = BASE / "microformatos"
DASHBOARD_DIR = BASE / "dashboard"
DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def load_records():
    records = []
    for p in sorted(MICROFORMATOS.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            data["_filename"] = p.name
            data["_microformat_path"] = str(p.relative_to(BASE))
            records.append(data)
        except Exception as e:
            print(f"Skip {p}: {e}")
    return records


def build_html(records):
    now = datetime.now().isoformat()
    total_docs = len(records)
    type_counts = Counter(r.get("type", "Sin tipo") for r in records)
    ocr_pending = sum(1 for r in records if r.get("processing", {}).get("ocrEngine") == "pending")
    pdfa_pending = sum(1 for r in records if not r.get("processing", {}).get("convertedToPdfA"))

    cards = []
    for r in records:
        doc_id = r.get("documentId", r.get("_filename", ""))
        title = r.get("dublinCore", {}).get("title", "Sin título")
        doc_type = r.get("type", "Sin tipo")
        creator = r.get("dublinCore", {}).get("creator", "")
        date = r.get("dublinCore", {}).get("date", "")
        pages = len(r.get("structuredContent", {}).get("pages", []))
        ocr = r.get("processing", {}).get("ocrEngine", "pending")
        confidence = r.get("processing", {}).get("ocrConfidence")
        pdfa = r.get("processing", {}).get("convertedToPdfA")
        images = len(r.get("source", {}).get("originalFiles", []))
        checksum = r.get("processing", {}).get("checksum", {}).get("sha256", "")
        rel_microformat = r.get("_microformat_path", "")

        confidence_str = f"{confidence:.0%}" if isinstance(confidence, (int, float)) else "N/A"
        pdfa_str = "Sí" if pdfa else "No"
        ocr_str = ocr if ocr != "pending" else "Pendiente"
        checksum_str = checksum[:12] + "…" if checksum else "Pendiente"

        cards.append(f"""
        <div class="card" data-type="{doc_type}" data-ocr="{ocr}" data-pdfa="{str(pdfa).lower()}">
          <div class="card-header">
            <div class="card-title">{title}</div>
            <div class="card-meta">{doc_id}</div>
          </div>
          <div class="card-body">
            <div class="badge badge-type">{doc_type}</div>
            <div class="badge badge-date">{date}</div>
            <div class="meta-row"><span class="meta-label">Creador:</span> {creator}</div>
            <div class="meta-row"><span class="meta-label">Páginas:</span> {pages}</div>
            <div class="meta-row"><span class="meta-label">Imágenes:</span> {images}</div>
            <div class="meta-row"><span class="meta-label">OCR:</span> <span class="status status-{'ok' if ocr != 'pending' else 'pending'}">{ocr_str}</span></div>
            <div class="meta-row"><span class="meta-label">Confianza OCR:</span> {confidence_str}</div>
            <div class="meta-row"><span class="meta-label">PDF/A:</span> <span class="status status-{'ok' if pdfa else 'pending'}">{pdfa_str}</span></div>
            <div class="meta-row"><span class="meta-label">Checksum:</span> <code>{checksum_str}</code></div>
          </div>
          <div class="card-footer">
            <a class="btn" href="../microformatos/{rel_microformat}" target="_blank">Microformato JSON</a>
          </div>
        </div>
        """)

    cards_html = "\n".join(cards)

    type_options = "".join(f'<option value="{t}">{t} ({c})</option>' for t, c in sorted(type_counts.items()))

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard Digitalización UPN</title>
<style>
:root {{
  --bg: #f5f7fa;
  --card: #ffffff;
  --text: #1f2937;
  --muted: #6b7280;
  --accent: #2563eb;
  --ok: #16a34a;
  --pending: #f59e0b;
  --border: #e5e7eb;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); }}
header {{ background: linear-gradient(135deg, #1e3a8a, #2563eb); color: white; padding: 24px; }}
header h1 {{ margin: 0 0 8px; font-size: 22px; }}
header p {{ margin: 0; opacity: 0.85; font-size: 13px; }}
.filters {{ padding: 16px 24px; display: flex; gap: 12px; flex-wrap: wrap; align-items: center; background: #eef2ff; border-bottom: 1px solid var(--border); }}
.filters label {{ font-size: 12px; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }}
.filters select, .filters input {{ padding: 8px 10px; border: 1px solid var(--border); border-radius: 6px; font-size: 13px; background: white; }}
.stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; padding: 16px 24px; }}
.stat {{ background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 14px; text-align: center; }}
.stat-value {{ font-size: 22px; font-weight: 700; color: var(--accent); }}
.stat-label {{ font-size: 11px; color: var(--muted); margin-top: 4px; text-transform: uppercase; letter-spacing: 0.05em; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; padding: 16px 24px 24px; }}
.card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; display: flex; flex-direction: column; transition: transform .1s ease, box-shadow .1s ease; }}
.card:hover {{ transform: translateY(-2px); box-shadow: 0 10px 25px rgba(0,0,0,0.06); }}
.card-header {{ padding: 14px 14px 0; }}
.card-title {{ font-size: 15px; font-weight: 700; line-height: 1.3; }}
.card-meta {{ font-size: 11px; color: var(--muted); margin-top: 4px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
.card-body {{ padding: 12px 14px; display: flex; flex-direction: column; gap: 6px; }}
.badge {{ display: inline-block; padding: 3px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; background: #eef2ff; color: #1e3a8a; width: max-content; }}
.badge-date {{ background: #f3f4f6; color: #374151; }}
.meta-row {{ font-size: 13px; display: flex; justify-content: space-between; gap: 8px; }}
.meta-label {{ color: var(--muted); font-size: 12px; }}
.status {{ font-weight: 600; }}
.status-ok {{ color: var(--ok); }}
.status-pending {{ color: var(--pending); }}
.card-footer {{ padding: 10px 14px; border-top: 1px solid var(--border); display: flex; justify-content: flex-end; }}
.btn {{ text-decoration: none; font-size: 12px; padding: 6px 10px; border-radius: 6px; background: var(--accent); color: white; font-weight: 600; }}
.btn:hover {{ background: #1d4ed8; }}
footer {{ text-align: center; padding: 16px; font-size: 11px; color: var(--muted); border-top: 1px solid var(--border); }}
.empty {{ padding: 24px; text-align: center; color: var(--muted); }}
</style>
</head>
<body>
<header>
  <h1>📄 Dashboard Digitalización UPN</h1>
  <p>Catálogo vivo de microformatos · {total_docs} documentos · Actualizado {now}</p>
</header>

<div class="filters">
  <div>
    <label for="typeFilter">Tipo</label><br>
    <select id="typeFilter"><option value="">Todos</option>{type_options}</select>
  </div>
  <div>
    <label for="ocrFilter">OCR</label><br>
    <select id="ocrFilter">
      <option value="">Cualquiera</option>
      <option value="pending">Pendiente</option>
      <option value="tesseract">Tesseract</option>
    </select>
  </div>
  <div>
    <label for="pdfaFilter">PDF/A</label><br>
    <select id="pdfaFilter">
      <option value="">Cualquiera</option>
      <option value="true">Sí</option>
      <option value="false">No</option>
    </select>
  </div>
  <div>
    <label for="search">Buscar</label><br>
    <input id="search" type="text" placeholder="Título o ID…">
  </div>
</div>

<div class="stats">
  <div class="stat"><div class="stat-value">{total_docs}</div><div class="stat-label">Documentos</div></div>
  <div class="stat"><div class="stat-value">{len(type_counts)}</div><div class="stat-label">Tipos</div></div>
  <div class="stat"><div class="stat-value">{ocr_pending}</div><div class="stat-label">OCR pendiente</div></div>
  <div class="stat"><div class="stat-value">{pdfa_pending}</div><div class="stat-label">PDF/A pendiente</div></div>
</div>

<div class="grid" id="grid">{cards_html if cards_html else '<div class="empty">No hay microformatos.</div>'}</div>

<footer>Generado automáticamente por mementobloom · Proyecto Administracion_UPN</footer>

<script>
const grid = document.getElementById('grid');
const cards = Array.from(grid.querySelectorAll('.card'));
const typeFilter = document.getElementById('typeFilter');
const ocrFilter = document.getElementById('ocrFilter');
const pdfaFilter = document.getElementById('pdfaFilter');
const search = document.getElementById('search');

function applyFilters() {{
  const type = typeFilter.value;
  const ocr = ocrFilter.value;
  const pdfa = pdfaFilter.value;
  const q = search.value.trim().toLowerCase();

  cards.forEach(card => {{
    const matchType = !type || card.dataset.type === type;
    const matchOcr = !ocr || card.dataset.ocr === ocr;
    const matchPdfA = !pdfa || card.dataset.pdfa === pdfa;
    const text = (card.textContent || '').toLowerCase();
    const matchSearch = !q || text.includes(q);
    card.style.display = (matchType && matchOcr && matchPdfA && matchSearch) ? '' : 'none';
  }});
}}
typeFilter.addEventListener('change', applyFilters);
ocrFilter.addEventListener('change', applyFilters);
pdfaFilter.addEventListener('change', applyFilters);
search.addEventListener('input', applyFilters);
</script>
</body>
</html>
"""


def main():
    try:
        base = BASE
        output = OUTPUT_ARG or (DASHBOARD_DIR / "index.html")
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        return 1

    records = load_records()
    html = build_html(records)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(html, encoding="utf-8")
    print(f"Dashboard actualizado: {output}")
    print(f"Documentos indexados: {len(records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
