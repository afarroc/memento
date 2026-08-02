# context/silabo_upn.md — Convenciones de sílabos UPN

Fuente canónica: `projects/Administracion_UPN/docs/Ciclo_02/`.

## Estructura típica de un sílabo UPN
- **Curso**: nombre, código, ciclo, créditos, horas.
- **Unidades** (4-5): cada una → 1 módulo en M360.
- **Semanas** (17): cada una → 1 lección en M360.
- **Sistema de evaluación**: T1 (4%), Parcial (20%), T2 (12%), T3 (15%), Final (20%), Sustitutoria.
- Las semanas de evaluación → `lesson_type='quiz'` con 5 preguntas.

## Cursos UPN documentados
- Matemática Básica Ciclo 02 (ya recreado en M360 ID 2: 5 mód, 17 les).
- Complementos de Matemática, Comunicación 1, Desarrollo de Talento, Psicología de la Felicidad, Responsabilidad Social (solo cabeceras en MariaDB antigua; recrear desde sílabo).
- Aritmética (3 les), Álgebra Básica (18 les) — tienen contenido en MariaDB antigua.

## Regla de oro
El sílabo en markdown es la ÚNICA fuente de verdad para recrear contenido. La MariaDB antigua es solo referencia de auditoría.
