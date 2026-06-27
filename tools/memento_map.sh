#!/usr/bin/env bash
# =============================================================================
# memento_map.sh — Mapa completo del proyecto MementoBloom
# Compatible con bash 3.2 (macOS) y bash 4+
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
info()    { echo -e "${CYAN}▸ $*${RESET}"; }
ok()      { echo -e "${GREEN}✔ $*${RESET}"; }
warn()    { echo -e "${YELLOW}⚠ $*${RESET}"; }
err()     { echo -e "${RED}✘ $*${RESET}"; }
section() { echo -e "\n${BOLD}$*${RESET}"; }

# ─── Parsing de argumentos ────────────────────────────────────────────────────
MODE="project"
APP_ARG=""
OUT_FILE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    project|app|urls|tree) MODE="$1"; shift ;;
    app) MODE="app"; shift; [[ $# -gt 0 && "$1" != --* ]] && { APP_ARG="$1"; shift; } ;;
    --out) OUT_FILE="$2"; shift 2 ;;
    --help) sed -n '2,22p' "$0" | sed 's/^# \?//'; exit 0 ;;
    *) if [[ -d "$1" ]]; then APP_ARG="$1"; [[ -z "$MODE" || "$MODE" == "project" ]] && MODE="app"; fi; shift ;;
  esac
done

# ─── Localizar raíz del proyecto ─────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT=""
SEARCH="$SCRIPT_DIR"
for _ in 1 2 3 4; do
  if [[ -f "$SEARCH/pyproject.toml" || -f "$SEARCH/setup.py" ]]; then PROJECT_ROOT="$SEARCH"; break; fi
  SEARCH="$(dirname "$SEARCH")"
done
[[ -z "$PROJECT_ROOT" ]] && { err "No se encontró pyproject.toml/setup.py"; exit 1; }
cd "$PROJECT_ROOT"

# ─── Helpers ──────────────────────────────────────────────────────────────────
_render_tree() {
  python3 - "$1" <<'PYTREE'
import os, sys
root = sys.argv[1]
SKIP = {'__pycache__', '.git', 'node_modules', 'migrations', 'venv', '.venv', '.django_cache'}
EXT  = {'.py', '.html', '.js', '.css', '.md', '.sh', '.json', '.sql', '.yaml', '.yml', '.toml', '.txt'}
def _tree(path, prefix=''):
    try: entries = sorted(os.listdir(path))
    except PermissionError: return
    dirs  = [e for e in entries if os.path.isdir(os.path.join(path, e)) and e not in SKIP]
    files = [e for e in entries if os.path.isfile(os.path.join(path, e)) and os.path.splitext(e)[1] in EXT and not e.endswith('.pyc') and e != '.DS_Store']
    items = dirs + files
    for i, item in enumerate(items):
        connector = '└── ' if i == len(items)-1 else '├── '
        full = os.path.join(path, item)
        print(prefix + connector + item)
        if os.path.isdir(full):
            extension = '    ' if i == len(items)-1 else '│   '
            _tree(full, prefix + extension)
print(os.path.basename(root) + '/')
_tree(root)
PYTREE
}

categorize() {
  local rel="${1#$2/}"
  case "$rel" in
    */__pycache__/*|*/__pycache__) echo pycache; return ;;
    .git/*|.git) echo git; return ;;
    */node_modules/*) echo node; return ;;
    */migrations/*) echo migrations; return ;;
    */venv/*|.venv/*) echo venv; return ;;
    */tests/*|*test*.py) echo tests; return ;;
    */templates/*|*templates/*) echo templates; return ;;
    */static/*|*static/*) echo static; return ;;
    */services/*) echo services; return ;;
    */utils/*) echo utils; return ;;
    */views/*|*views*.py) echo views; return ;;
    */models/*|*models*.py) echo models; return ;;
    */urls/*|*urls*.py) echo urls; return ;;
    */admin/*|*admin*.py) echo admin; return ;;
    */forms/*|*forms*.py) echo forms; return ;;
    core/*) echo core; return ;;
    tools/*) echo tools; return ;;
    memory/*) echo memory; return ;;
    archive/*) echo archive; return ;;
    config/*) echo config; return ;;
    docs/*) echo docs; return ;;
    projects/*) echo projects; return ;;
    scripts/*) echo scripts; return ;;
    memento/*) echo memento; return ;;
    models/*) echo models; return ;;
    *.cfg|*.ini|*.toml|*.yaml|*.yml) echo config; return ;;
    *.md) echo docs; return ;;
    panel_server.py|sala.py) echo services; return ;;
    vault_*.py|memento_cli.py) echo tools; return ;;
  esac
  echo other
}

# ─── Modos ────────────────────────────────────────────────────────────────────
_mode_project() {
  section "═══ project mode: MementoBloom ══════════════════════════════"
  info "Raíz:   $PROJECT_ROOT"
  info "Salida: docs/PROJECT_CONTEXT.md"
  TOTAL=$(find "$PROJECT_ROOT" -type f \( -name "*.py" -o -name "*.md" -o -name "*.sh" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.toml" -o -name "*.html" -o -name "*.css" -o -name "*.js" \) ! -path "*/__pycache__/*" ! -path "*/.git/*" ! -path "*/node_modules/*" ! -path "*/migrations/*" ! -path "*/venv/*" ! -path "*/.venv/*" ! -name "*.pyc" ! -name ".DS_Store" | wc -l | tr -d ' ')
  ok "$TOTAL archivos relevantes"
  mkdir -p docs
  cat > docs/PROJECT_CONTEXT.md <<EOFMARKER
# Mapa de Contexto — MementoBloom

> Generado por \`memento_map.sh\`  |  $(date '+%Y-%m-%d %H:%M:%S')
> Ruta: \`$PROJECT_ROOT\`  |  Total archivos: **$TOTAL**

---

## Resumen de arquitectura

| Capa | Directorio | Descripción |
|------|------------|-------------|
| Core | \`core/\` | Módulos compartidos: paths, git, index, services, health |
| Tools | \`tools/\` | CLI tools: session_start, bootstrap_context, quick_scan, optimize |
| Panel | \`panel_server.py\` | Dashboard HTTP (8766) |
| Sala | \`sala.py\` | Sala de mensajes HTTP+Redis (8767) |
| Vault | \`vault_\*.py\` | Gestión de credenciales |
| Models | \`models/\` | Modelos de dominio (grafo de memoria) |
| Memory | \`memory/\` | Índice compacto, seeds, sesiones |
| Config | \`config/\` | Configuración JSON de servicios |
| Docs | \`docs/\` | Documentación técnica |
| Projects | \`projects/\` | Handoffs por proyecto |
| Archive | \`archive/\` | Backups y datos obsoletos |
| Agent | \`.agent_context/\` | Contexto, seeds, instrucciones del agente |
| Módulo | \`memento/\` | Paquete cliente para proyectos externos |

---

## Entry Points / CLI
\`\`\`toml
$(awk '/\[project.scripts\]/,0' pyproject.toml || true)
\`\`\`

_Wrappers bash en raíz:_ \`memento-init\`, \`session_start\`, \`bootstrap_context\`, \`quick_scan\`, \`optimize_agent\`, \`optimize_memento\`, \`memento-clean\`, \`memento-export\`

_Servicios:_ \`panel_server.py\` (8766), \`sala.py\` (8767)

---

## Dependencias

- Python >= 3.9
- Build: \`setuptools\`, \`wheel\`
- Runtime: stdlib-only (futuro: sentence-transformers, faiss-cpu)
- Redis: accesible (no requiere cliente Python; usa socket RAW)

---

## Estructura de directorios
\`\`\`
$(_render_tree "$PROJECT_ROOT")
\`\`\`

---

## Componentes detallados
EOFMARKER
  for dir in core tools memento models memory config docs; do
    [[ -d "$dir" ]] || continue
    cat >> docs/PROJECT_CONTEXT.md <<EOFMARKER
### \`$dir/\`
EOFMARKER
    _list_files() {
      find "$1" -maxdepth 1 -type f \( -name "*.py" -o -name "*.json" -o -name "*.md" -o -name "*.sh" \) ! -name ".DS_Store" | sort
    }
    while IFS= read -r f; do
      rel="${f#$PROJECT_ROOT/}"
      lines=$(wc -l < "$f" 2>/dev/null || echo "?")
      echo "- \`$(basename "$f")\` ($lines líneas) — \`$rel\`" >> docs/PROJECT_CONTEXT.md
    done < <(_list_files "$dir")
    echo "" >> docs/PROJECT_CONTEXT.md
  done
  cat >> docs/PROJECT_CONTEXT.md <<'EOFMARKER'
---

## Handoffs recientes
| Archivo |
|---------|
EOFMARKER
  find projects/mementobloom -maxdepth 1 -name "HANDOFF_*.md" -printf "| \`%f\` |\n" 2>/dev/null | sort -r | head -10 >> docs/PROJECT_CONTEXT.md || true
  echo "" >> docs/PROJECT_CONTEXT.md
}

_mode_app() {
  APP_DIR="$(realpath "${APP_ARG:-./core}")"
  [[ -d "$APP_DIR" ]] || { err "No se encontró: $APP_DIR"; exit 1; }
  APP_NAME="$(basename "$APP_DIR")"
  APP_UPPER="$(echo "$APP_NAME" | tr '[:lower:]' '[:upper:]')"
  OUT="${OUT_FILE:-docs/${APP_UPPER}_CONTEXT.md}"
  NOW="$(date '+%Y-%m-%d %H:%M:%S')"
  section "═══ app mode: $APP_NAME ══════════════════════════════════════"
  info "App:    $APP_DIR"
  info "Salida: $OUT"
  TOTAL=$(find "$APP_DIR" -type f \( -name "*.py" -o -name "*.html" -o -name "*.js" -o -name "*.css" -o -name "*.json" -o -name "*.md" -o -name "*.sh" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sql" -o -name "*.toml" \) ! -path "*/__pycache__/*" ! -path "*/.git/*" ! -path "*/node_modules/*" ! -path "*/migrations/*" ! -name "*.pyc" ! -name ".DS_Store" | wc -l | tr -d ' ')
  ok "$TOTAL archivos"
  mkdir -p docs
  cat > "$OUT" <<EOFMARKER
# Mapa de Contexto — \`${APP_NAME}\`

> Generado por \`memento_map.sh\`  |  $NOW
> Ruta: \`$APP_DIR\`  |  Total archivos: **$TOTAL**

---
EOFMARKER
  declare -A CAT_COUNT
  while IFS= read -r f; do
    c=$(categorize "$f" "$APP_DIR")
    CAT_COUNT[$c]=$((${CAT_COUNT[$c]:-0} + 1))
  done < <(find "$APP_DIR" -type f \( -name "*.py" -o -name "*.html" -o -name "*.js" -o -name "*.css" -o -name "*.json" -o -name "*.md" -o -name "*.sh" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sql" -o -name "*.toml" \) ! -path "*/__pycache__/*" ! -path "*/.git/*" ! -path "*/node_modules/*" ! -path "*/migrations/*" ! -name "*.pyc" ! -name ".DS_Store" | sort)
  cat >> "$OUT" <<'EOFMARKER'
## Índice
| # | Categoría | Archivos |
|---|-----------|----------|
EOFMARKER
  idx=1
  for cat in views templates models forms services utils urls admin management static tests config migrations memory core tools docs projects archive other pycache git node venv; do
    cnt="${CAT_COUNT[$cat]:-0}"; [[ $cnt -eq 0 ]] && continue
    icon="📄"
    case "$cat" in
      views) icon="👁";; templates) icon="🎨";; models) icon="🗃";;
      forms) icon="📝";; services) icon="⚙️";; utils) icon="🔧";;
      urls) icon="🔗";; admin) icon="🛡";; tests) icon="🧪";;
      static) icon="📦";; migrations) icon="🔄";; config) icon="🔧";;
      memory) icon="🧠";; core) icon="⚙️";; tools) icon="🛠";;
      docs) icon="📚";; projects) icon="📂";; archive) icon="🗄";;
      venv) icon="🌿";;
    esac
    echo "| $idx | $icon \`$cat\` | $cnt |" >> "$OUT"
    idx=$((idx+1))
  done
  cat >> "$OUT" <<'EOFMARKER'

---

## Archivos por Categoría
EOFMARKER
  for cat in views templates models forms services utils urls admin management static tests config migrations memory core tools docs projects archive other pycache git node venv; do
    cnt="${CAT_COUNT[$cat]:-0}"; [[ $cnt -eq 0 ]] && continue
    echo "" >> "$OUT"
    echo "### $(echo "$cat" | tr '[:lower:]' '[:upper:]') ($cnt archivos)" >> "$OUT"
    echo "" >> "$OUT"
    echo "| Archivo | Líneas | Ruta relativa |" >> "$OUT"
    echo "|---------|--------|---------------|" >> "$OUT"
    while IFS= read -r f; do
      [[ $(categorize "$f" "$APP_DIR") != "$cat" ]] && continue
      rel="${f#$APP_DIR/}"
      lines=$(wc -l < "$f" 2>/dev/null || echo "?")
      echo "| \`$(basename "$f")\` | $lines | \`$rel\` |" >> "$OUT"
    done < <(find "$APP_DIR" -type f \( -name "*.py" -o -name "*.html" -o -name "*.js" -o -name "*.css" -o -name "*.json" -o -name "*.md" -o -name "*.sh" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sql" -o -name "*.toml" \) ! -path "*/__pycache__/*" ! -path "*/.git/*" ! -path "*/node_modules/*" ! -path "*/migrations/*" ! -name "*.pyc" ! -name ".DS_Store" | sort)
  done
  cat >> "$OUT" <<'EOFMARKER'

---

## Árbol de Directorios
\`\`\`
EOFMARKER
  _render_tree "$APP_DIR" >> "$OUT"
  cat >> "$OUT" <<'EOFMARKER'
\`\`\`

---

## Endpoints / Entry Points
\`\`\`python
EOFMARKER
  if [[ -f "pyproject.toml" ]]; then
    awk '/\[project.scripts\]/,0' pyproject.toml >> "$OUT" || true
  fi
  if [[ -f "$APP_DIR/urls.py" ]]; then
    grep -E "path\(" "$APP_DIR/urls.py" >> "$OUT" || true
  fi
  echo '```' >> "$OUT"
  cat >> "$OUT" <<'EOFMARKER'

---

## Modelos detectados
EOFMARKER
  for mf in "$APP_DIR/models.py" "$APP_DIR/models/"*.py; do
    [[ -f "$mf" ]] || continue
    echo "**\`${mf#$APP_DIR/}\`**" >> "$OUT"
    echo "" >> "$OUT"
    grep -n "^class " "$mf" >> "$OUT" || true
    echo "" >> "$OUT"
  done
  cat >> "$OUT" <<'EOFMARKER'

---

## Funciones clave
\`\`\`
EOFMARKER
  while IFS= read -r pyf; do
    [[ -f "$pyf" ]] || continue
    funcs=$(grep -n "^def \|^    def " "$pyf" 2>/dev/null | grep -v "__\b" | head -40 || true)
    [[ -z "$funcs" ]] && continue
    echo "$funcs" >> "$OUT"
    echo "" >> "$OUT"
  done < <(find "$APP_DIR" -maxdepth 1 -type f -name "*.py" | sort)
  echo '```' >> "$OUT"
}

_mode_urls() {
  section "═══ Entry Points — MementoBloom ═════════════════════════════════"
  echo ""
  echo "_CLI tools (pyproject.toml [project.scripts])_"; echo ""
  if [[ -f pyproject.toml ]]; then
    awk '/\[project.scripts\]/,0' pyproject.toml | grep -E '^\s+\w+\s*=' | sed 's/^\s*/  /' || true
  fi
  echo ""
  echo "_Root wrappers_"; echo ""
  for f in memento-init session_start bootstrap_context quick_scan optimize_agent optimize_memento memento-clean memento-export; do
    [[ -f "$f" ]] && echo "  \`$f\`"
  done
  echo ""
  echo "_Servicios_"; echo ""
  echo "  \`panel_server.py\`  →  http://0.0.0.0:8766"
  echo "  \`sala.py\`          →  http://0.0.0.0:8767"
  echo ""
  echo "_Agents_"; echo ""
  echo "  \`memento-curador\`  →  seed-based agent"
  echo "  \`memento-onboarding\` → onboarding agent"
  echo ""
}

_mode_tree() {
  section "═══ Directory Tree — MementoBloom ════════════════════════════════"
  echo ""
  _render_tree "$PROJECT_ROOT"
  echo ""
}

# ─── Dispatch ─────────────────────────────────────────────────────────────────
case "$MODE" in
  project) _mode_project ;;
  app)     _mode_app ;;
  urls)    _mode_urls ;;
  tree)    _mode_tree ;;
  *)       err "Modo desconocido: $MODE"; exit 1 ;;
esac
