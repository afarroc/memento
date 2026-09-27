# Índice de cursos recreados por el Agente Tutor

> Estado persistente del agente. No duplicar cursos ya listados.

| Slug | M360 ID | Módulos | Lecciones | Fuente sílabo | Metadatos UPN | Estado M360 |
|------|---------|---------|-----------|---------------|---------------|-------------|
| upn-matematica-basica-ciclo02 | 2 | 5 | 17 | projects/Administracion_UPN/docs/Ciclo_02/MATEMATICA_BASICA/ | Migrado | On-demand |
| upn-responsabilidad-social | 4 | 3 | 17 | projects/Administracion_UPN/docs/SILABO_RESPONSABILIDAD_SOCIAL.md | Migrado | On-demand |
| upn-comunicacion-1 | 3 | 3 | 17 | projects/Administracion_UPN/docs/SILABO_COMUNICACION_1.md | Migrado | On-demand |
| upn-complementos-matematica | 7 | 3 | 17 | projects/Administracion_UPN/docs/SILABO_COMPLEMENTOS_MATEMATICA.md | Migrado | On-demand |
| upn-desarrollo-talento | 8 | 3 | 17 | projects/Administracion_UPN/docs/SILABO_DESARROLLO_TALENTO.md | Migrado | On-demand |
| upn-psicologia-felicidad | 9 | 4 | 17 | projects/Administracion_UPN/docs/SILABO_PSICOLOGIA_FELICIDAD.md | Migrado | On-demand |

## Flujo actual
- Creación de curso: API (`api_v1_create_course`).
- Módulos: API (`api_v1_create_module`).
- Lecciones: API (`api_v1_create_lesson`).
- Evaluaciones: API (`api_v1_create_evaluation`).
- Bibliografía: API (`api_v1_create_bibliografia`).
- SQL excepcional: solo si la API falla por validación no superable y el servicio está disponible.
- **Disponibilidad:** M360 es on-demand. Si no responde, registrar estado y consultar antes de continuar.
- **Validación:** listar evaluaciones/bibliografía con `/api/v1/evaluations/?course_id={id}` y `/api/v1/bibliografia/?course_id={id}`; rutas anidadas `/api/v1/courses/{id}/evaluations/` y `/api/v1/courses/{id}/bibliografia/` no existen.

## Pendientes (cola de trabajo)
- [x] UPN Complementos de Matemática (MariaDB 55, vacío) → recreado en M360 ID 7 (3 módulos, 17 lecciones)
- [x] Desarrollo de Talento (MariaDB 57, vacío) → recreado en M360 ID 8 (3 módulos, 17 lecciones)
- [x] Psicología de la Felicidad (MariaDB 58, vacío) → recreado en M360 ID 9 (4 módulos, 17 lecciones)
- [ ] Aritmética (MariaDB 3, 3 les) — recrear desde sílabo + contenido MariaDB
- [ ] Álgebra Básica (MariaDB 50, 18 les) — recrear desde sílabo + contenido MariaDB
