# MANUAL — Agente Tutor de Cursos

Mapa de instrucciones para recrear un curso UPN en M360. Este manual es autónomo: un instructor debe poder ejecutarlo sin indagar archivos adicionales.

## Política de ejecución
- **Ruta preferida:** API REST de M360 (`tools/m360_bridge/client.py`).
- **SQL directo:** solo como último recurso excepcional. Se permite si:
  - M360 no está disponible temporalmente (servicio on-demand) y el humano decide proceder sin UI, o
  - La API falla por una validación no superable del modelo. Registrar la incidencia en `estado/indice_cursos.md` y derivar una mejora en `estado/mejoras.md`.
- **Disponibilidad M360:** M360 es un servicio local on-demand. Si M360 no responde, NO es un blocker técnico. Consultar al humano: ¿levanto M360 o continuamos con otra tarea?

## Paso 0 — Checklist de preparación
- [ ] Leer el sílabo fuente en `projects/Administracion_UPN/docs/`.
- [ ] Leer `projects/Administracion_UPN/docs/MALLA_CURRICULAR_ADMINISTRACION.md` para confirmar ciclo, naturaleza teórico/práctico y duración (17 semanas estándar, 16 para cursos marcados con **).
- [ ] Abrir `estado/indice_cursos.md` y confirmar que el curso NO está ya registrado.
- [ ] Abrir `context/m360_modelo.md` y confirmar el modelo/campos actuales.
- [ ] Abrir `context/patron_metodologia_upn.md` y confirmar las convenciones de nomenclatura y cronograma.
- [ ] Abrir `estado/mejoras.md` y confirmar que no existe una mejora pendiente para la entidad que se va a crear.
- [ ] Tener a mano las credenciales M360 (`.env` del proyecto).

## Paso 1 — Crear curso
1. Llamar a `client.api_v1_create_course(...)` con:
   - `title`, `slug`
   - `tutor_id=1`
   - `is_published=True`
   - `level='beginner'`
   - `price=0`
   - `duration_hours=<horas del sílabo>`
   - Metadatos UPN obligatorios: `codigo`, `creditos`, `ht`, `hp`, `hl`, `pc`, `requisitos`, `naturaleza`, `competencia_general`, `componentes`, `sumilla`, `logro_curso`, `sistema_evaluacion`, `bibliografia`.
   - `description` y `short_description` resumidos del sílabo.
2. Si la API responde con éxito, guardar el `course_id`.
3. Si M360 no está disponible o la API falla por una validación no superable:
   - Registrar en `estado/indice_cursos.md` columna `Estado M360`.
   - Crear una entrada en `estado/mejoras.md` si corresponde.
   - Usar SQL directo excepcional para `courses_course` solo en este curso cuando el humano autorice continuar sin M360 levantado.

## Paso 1b — Actualizar metadatos UPN en cursos existentes
- Si el curso ya existe en M360 pero falta información UPN, usar `client.api_v1_update_course(course_id, ...)` con los mismos metadatos UPN.
- Registrar en `estado/indice_cursos.md` columna `Metadatos UPN = Migrado`.

## Paso 2 — Categoría (opcional)
- Preferir API: `client.api_v1_create_course_category(name="UPN Ciclo 02")`.

## Paso 3 — Módulos (unidades del sílabo)
- **Convención de título:** `Unidad I: <titulo de la unidad>`, `Unidad II: <titulo>`, etc.
- Si el sílabo incluye rango de semanas en el título de unidad, usar formato: `Unidad I: <titulo> (Semanas X-Y)`.
- `order` = 1, 2, 3... según orden en el sílabo.
- **Ruta estándar:** API `client.api_v1_create_module(course_id, title, order, description, logro_unidad)`.
- **Excepcional:** solo si la API falla por validación no superable: SQL directo `INSERT INTO courses_module (...)` y registrar mejora en `estado/mejoras.md`.

## Paso 4 — Lecciones (semanas)
Por cada semana del sílabo:
1. Convertir contenido markdown → HTML con `markdown.markdown(content, extensions=['tables','fenced_code'])`.
2. Escapar símbolos `$` de moneda.
3. **Convención de título:** `Semana 1: <saberes esenciales de la semana>`, `Semana 2: <saberes>`, etc.
4. **Convención de tipo:** `lesson_type='text'` por defecto; `lesson_type='quiz'` para evaluaciones; `lesson_type='assignment'` para proyectos/actividades prácticas. Usar valores en minúsculas.
5. **Cronograma estándar UPN (17 semanas):**
   - Semana 1: Introducción a los cursos virtuales
   - Semana 4: T1
   - Semana 7: T2
   - Semana 10: T3
   - Semana 13: T4
   - Semana 14: Retroalimentación final
   - Semana 15: Evaluación final
   - Semana 16: Reflexión
   - Semana 17: Evaluación sustitutoria (o No aplica)
6. **Ruta estándar:** API `client.api_v1_create_lesson(module_id, title, lesson_type, order, saberes_esenciales, actividades, trabajo_campo, content, quiz_questions)`.
7. **Excepcional:** solo si la API falla por validación no superable: SQL directo `INSERT INTO courses_lesson (...)` y registrar mejora en `estado/mejoras.md`.

## Paso 4b — Evaluaciones y bibliografía
- **Evaluaciones:** crear por API `client.api_v1_create_evaluation(course_id, nombre, peso, semana, descripcion)` para cada T1-T4, Final y Sustitutoria.
- **Bibliografía:** crear por API `client.api_v1_create_bibliografia(course_id, autor, titulo, anio, enlace)` para cada referencia del sílabo.
- **Excepcional:** solo si la API falla, usar SQL directo y registrar mejora.

## Paso 5 — Validación post-creación
- [ ] Consultar `client.api_v1_list_courses()` y confirmar presencia del curso.
- [ ] Consultar `client.api_v1_list_modules(course_id=...)` y confirmar módulos esperados.
- [ ] Consultar `client.api_v1_list_lessons(module_id=...)` y confirmar lecciones esperadas.
- [ ] Consultar `client.api_v1_list_evaluations(course_id=...)` y confirmar evaluaciones esperadas.
- [ ] Consultar `client.api_v1_list_bibliografia(course_id=...)` y confirmar bibliografía esperada.
- [ ] **Validación automática (admin):** al guardar el curso en admin, se verifica:
  - Módulos tienen `logro_unidad`.
  - 17 lecciones exactas.
  - Lecciones tienen `logro_semana` y `saberes_esenciales`.
  - Evaluaciones T1, T2, T3, T4, Final, Sustitutoria presentes.
  - Cualquier falta se muestra como `messages.warning` en admin.
- [ ] Si faltan entidades, corregir antes de continuar.

## Paso 6 — Registro
- Escribir en `estado/indice_cursos.md`:
  ```
  | <slug> | M360 ID <n> | módulos <x> | lecciones <y> | fuente <ruta silabo> | Metadatos UPN | B-M360 |
  ```
- Si se usó SQL excepcional, agregar una nota en `estado/mejoras.md` con la entidad faltante.

## Paso 7 — Resumen al padre
Devolver: ID curso, módulos, lecciones, evaluaciones, bibliografía, incidencias, mejoras derivadas. Una sola línea por curso.

## Mapa de decisión rápida
```
¿Existe endpoint API para la entidad?
  ├─ Sí → Usar API
  └─ No → Usar SQL excepcional + registrar mejora en estado/mejoras.md
```

## Notas
- Fuente canónica de contenido = sílabos en `projects/Administracion_UPN/docs/`.
- El bridge `tools/m360_bridge/client.py` soporta CRUD de curso/categoría/módulos/lecciones/evaluaciones/bibliografía. Usar API por defecto.
- No usar tablas `courses_quiz` ni `courses_question`; no existen en producción actual.
- Los déficits detectados se convierten en mejoras documentadas; no se ignoran ni se archivan sin seguimiento.

