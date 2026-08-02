# Patrón de metodología de enseñanza UPN

> Análisis de los 6 sílabos UPN existentes para extraer la metodología de enseñanza estándar de la universidad.

## Sílabos analizados
1. Matemática Básica (2016-1, Ciclo 1°)
2. Complementos de Matemática (2018-2, Ciclo 1)
3. Comunicación 1 (2020-2, Ciclo 2°)
4. Desarrollo del Talento (2021-1, Ciclo 1°)
5. Psicología de la Felicidad (2019-4, Según carrera)
6. Responsabilidad Social (2023-1, Según carrera)

## Plan de estudios global
Fuente: `projects/Administracion_UPN/docs/MALLA_CURRICULAR_ADMINISTRACION.md`

- Carrera: Administración
- Ciclos: 07
- Cursos relevantes ya documentados: Complementos de Matemática, Matemática Básica, Comunicación 1, Desarrollo del Talento, Psicología de la Felicidad, Responsabilidad Social, Contabilidad 1, Derecho de la Empresa 1, Probabilidad y Estadística, Comunicación 2, Comunicación 3, Diseño Organizacional, Ideación, Contabilidad 2 P, Metodología Universitaria, Microeconomía para Administradores, Gestión de Recursos Humanos, Administración de Operaciones, Sistemas de Información Gerencial, Investigación de Mercados, Gestión de Procesos, Matemática 1, Matemática Financiera, Marketing, Macroeconomía para Administradores, Comportamiento Organizacional, Finanzas, Empleabilidad, Marketing Internacional, Metodología de la investigación, Proyectos de Inversión, Auditoria Administrativa, Ventas, Empresas Familiares, Finanzas Corporativas, Derecho de la Empresa, Costos y Presupuestos, Gestión de la Cadena de Suministros, Planeamiento Estratégico, Práctica Preprofesional, Gestión de Compensaciones, Proyecto Social, Implementación EMI, Electivo de Especialidad, Proyecto de Tesis, Negociación y Resolución de Conflictos, Expresión Corporal para los Negocios, Tesis.
- Leyendas: (**) 16 semanas; (***) Virtual; (P) teórico-práctico; (*) electivo/especial.
- Implicación para M360: `duration_hours` y `is_published` pueden derivarse de estas leyendas; los cursos virtuales pueden requerir formato de contenido diferente.

## Patrones detectados

### 1. Naturaleza del curso
- Formato estándar: **teórico-práctico** / **teórico-práctica**
- Excepción: Responsabilidad Social es **teórico**
- Convención M360: `level='beginner'`, `price=0`, `duration_hours` según sílabo

### 2. Estructura de unidades
- Unidades numeradas con **romanos**: `Unidad I`, `Unidad II`, `Unidad III`, etc.
- Cada unidad incluye: título, **Logro de unidad**, tabla de semanas
- Título de unidad: `Unidad I: <TEMA> (Semanas X-Y)` cuando aplica rango
- Patrón de títulos M360: `Unidad I: <titulo>`, `Unidad II: <titulo>`

### 3. Tabla de semanas (columnas)
Variantes detectadas:
- `Semana | Saberes Esenciales | Actividades | PC`
- `Semana | Logro de Unidad | Saberes Esenciales | Actividades | Trabajo de Campo`

Convención M360: usar `Semana | Saberes Esenciales | Actividades | PC` como estándar.

### 4. Cronograma estándar de 17 semanas
Patrón casi universal:
- Semana 1: Introducción a los cursos virtuales
- Semana 2-3: Contenido inicial
- Semana 4: **T1** (15%)
- Semana 5-6: Contenido medio
- Semana 7: **T2** (15%)
- Semana 8-9: Contenido medio
- Semana 10: **T3** (15%)
- Semana 11-12: Contenido avanzado
- Semana 13: **T4** (15%)
- Semana 14: Retroalimentación final
- Semana 15: **Evaluación final** (40%)
- Semana 16: Reflexión
- Semana 17: Evaluación sustitutoria (o No aplica)

Excepciones:
- Matemática Básica incluye Evaluación Parcial (20%) en semana 8
- Complementos de Matemática incluye Evaluación parcial (30%) en semana 8
- Psicología de la Felicidad: Evaluación final en semana 14

### 5. Sistema de evaluación
Patrón estándar UPN:
- T1: 15%
- T2: 15%
- T3: 15%
- T4: 15%
- Evaluación final: 40%
- Evaluación sustitutoria: no tiene peso fijo

Variantes:
- Matemática Básica: T1 (4%) + Parcial (20%) + T2 (12%) + T3 (15%) + Final (20%) + Sustitutoria
- Complementos de Matemática: T1 (15%) + Parcial (30%) + T2 (15%) + Final (40%) + Sustitutoria
- Desarrollo del Talento: T1-T4 (15% c/u) + Final (40%)
- Responsabilidad Social: T1-T4 (15% c/u) + Final (40%)

Convención M360: mapear a `lesson_type='quiz'` en semanas de evaluación; contenido de texto en semanas ordinarias.

### 6. Competencias y componentes
- **Competencia General**: siempre presente
- **Competencia Específica**: "Según carrera profesional" cuando aplica
- **Componentes transversales**:
  - Investigación: aparece en cursos de matemáticas
  - Responsabilidad Social: aparece en Psicología de la Felicidad y otros cursos sociales
  - Ciudadanía: ausente en los 6 sílabos
  - Práctica Preprofesional: ausente en los 6 sílabos

### 7. Metodologías activas
Solo documentado explícitamente en:
- Responsabilidad Social: aprendizaje colaborativo, ABP, estudios de casos, exposiciones grupales, trabajos colaborativos/individuales, procesos investigativos, reflexivos y críticos, enfoque socioconstructivista

Patrón implícito en otros sílabos:
- "Problemas de aplicación" en matemáticas
- "Elaboración de textos/infografías/organizadores" en comunicación y psicología
- "Proyecto formativo" en desarrollo del talento

### 8. Logro del curso
Patrón de redacción:
- "Al finalizar el curso, el estudiante [verbo en presente]..."
- Debe ser medible y observable

### 9. Fuente y periodo
- Periodo lectivo: variable por sílabo
- Fuente: siempre al final del documento

## Convenciones derivadas para el tutor
1. **Naturaleza**: usar "teórico-práctico" por defecto; "teórico" solo si el sílabo lo indica explícitamente.
2. **Unidades**: `Unidad I: <titulo>`, `Unidad II: <titulo>`, etc.
3. **Semanas**: `Semana 1: <saberes esenciales>`, siguiendo el patrón de 17 semanas.
4. **Evaluaciones**: distribuir T1-T4 en semanas 4, 7, 10, 13; Evaluación final en semana 15; Reflexión en 16; Sustitutoria en 17.
5. **lesson_type**: `text` en semanas ordinarias; `quiz` en semanas de evaluación; `assignment` en proyectos integradores.
6. **Contenido**: incluir siempre "Problemas de aplicación" o actividad práctica alineada al sílabo.
