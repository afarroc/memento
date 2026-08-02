# Índice de cursos recreados por el Agente Tutor

> Estado persistente del agente. No duplicar cursos ya listados.

| Slug | M360 ID | Módulos | Lecciones | Fuente sílabo | Metadatos UPN | Estado M360 |
|------|---------|---------|-----------|---------------|---------------|-------------|
| upn-matematica-basica-ciclo02 | 2 | 5 | 17 | projects/Administracion_UPN/docs/Ciclo_02/MATEMATICA_BASICA/ | Migrado | On-demand |
| upn-responsabilidad-social | 4 | 3 | 17 | projects/Administracion_UPN/docs/SILABO_RESPONSABILIDAD_SOCIAL.md | Migrado | On-demand |
| upn-comunicacion-1 | 3 | 3 | 17 | projects/Administracion_UPN/docs/SILABO_COMUNICACION_1.md | Migrado | On-demand |

## Flujo actual
- Creación de curso: API (`api_v1_create_course`).
- Módulos: API (`api_v1_create_module`).
- Lecciones: API (`api_v1_create_lesson`).
- Evaluaciones: API (`api_v1_create_evaluation`).
- Bibliografía: API (`api_v1_create_bibliografia`).
- SQL excepcional: solo si la API falla por validación no superable y el servicio está disponible.
- **Disponibilidad:** M360 es on-demand. Si no responde, registrar estado y consultar antes de continuar.

## Pendientes (cola de trabajo)
- [ ] UPN Complementos de Matemática (MariaDB 55, vacío) — recrear desde sílabo
- [ ] Desarrollo de Talento (MariaDB 57, vacío) — recrear desde sílabo
- [ ] Psicología de la Felicidad (MariaDB 58, vacío) — recrear desde sílabo
- [ ] Aritmética (MariaDB 3, 3 les) — recrear desde sílabo + contenido MariaDB
- [ ] Álgebra Básica (MariaDB 50, 18 les) — recrear desde sílabo + contenido MariaDB
