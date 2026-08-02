# Mejoras pendientes del Agente Tutor

> Déficits detectados → mejoras a implementar para eliminar SQL excepcional y hacer el flujo 100% API.

## Backlog API-first
1. **Crear módulos por API**
   - Déficit: M360 no expone endpoint API para `courses_module`. Hoy se inserta por SQL.
   - Evidencia: Comunicación 1 y Responsabilidad Social requirieron SQL para módulos.
   - Mejora: implementar en M360 un endpoint `/api/v1/courses/{course_id}/modules/` (POST/GET) o `/api/v1/modules/` con `course_id`.
   - Criterio de aceptación: el tutor puede crear módulos con `client.api_v1_create_module(...)` sin SQL.

2. **Crear lecciones por API**
   - Déficit: M360 no expone endpoint API para `courses_lesson`. Hoy se inserta por SQL.
   - Evidencia: Comunicación 1 y Responsabilidad Social requirieron SQL para lecciones.
   - Mejora: implementar `/api/v1/modules/{module_id}/lessons/` (POST/GET) o `/api/v1/lessons/` con `module_id`.
   - Criterio de aceptación: el tutor puede crear lecciones con `client.api_v1_create_lesson(...)` sin SQL.

3. **Implementar quizzes por API**
   - Déficit: Los quizzes se almacenan en `quiz_questions` JSONB de `courses_lesson`, sin modelo/endpoint separado.
   - Evidencia: Quizzes de Comunicación 1 y Responsabilidad Social insertados como JSONB vía SQL.
   - Mejora: implementar `/api/v1/lessons/{lesson_id}/quiz/` (POST/GET) con validación de preguntas/respuestas.
   - Criterio de aceptación: el tutor puede crear quizzes con `client.api_v1_create_quiz(...)` sin SQL.

4. **Puente del tutor a API de cursos**
   - Déficit: El bridge actual no tiene métodos para módulos/lecciones/quizzes.
   - Evidencia: `tools/m360_bridge/client.py` solo cubre curso/categoría.
   - Mejora: extender con métodos:
     - `api_v1_create_module(course_id, title, description, order)`
     - `api_v1_create_lesson(module_id, ...)`
     - `api_v1_create_quiz(lesson_id, ...)`
   - Criterio de aceptación: el agente tutor usa exclusivamente el bridge; no abre conexiones SQL.

5. **Automatizar validación visual**
   - Déficit: La validación requiere abrir el curso manualmente.
   - Mejora: implementar un helper que consulte `/api/v1/courses/{id}/` y valide presencia de módulos/lecciones automáticamente.

6. **Convención de nomenclatura formalizada**
   - Déficit: Los títulos de módulos y lecciones no estaban estandarizados; se generaron duplicados y formatos inconsistentes.
   - Evidencia: Responsabilidad Social tuvo módulos duplicados; RS y COM no usaban prefijo `Unidad I:` ni `Semana X:` como Matemática Básica.
   - Mejora: documentar y exigir convención en `MANUAL.md` y `context/m360_modelo.md`:
     - Módulos: `Unidad I: <titulo>`
     - Lecciones: `Semana 1: <saberes esenciales>`
     - lesson_type en minúsculas: `text`, `quiz`, `assignment`
    - Criterio de aceptación: todo curso recreado por el tutor cumple la convención sin corrección manual posterior.

## Estado
- Prioridad: Alta (mejoras 1-6) para cumplir API-first y consistencia.
- Responsable: equipo M360 / mementobloom.
- Cursos afectados por SQL excepcional: Matemática Básica (ID 2), Responsabilidad Social (ID 4), Comunicación 1 (ID 3).
- Cursos corregidos por nomenclatura: Responsabilidad Social (ID 4), Comunicación 1 (ID 3).

## Completadas
1. **Metadatos UPN en Course** — Implementados campos `codigo`, `creditos`, `ht`, `hp`, `hl`, `pc`, `requisitos`, `naturaleza`, `competencia_general`, `componentes`, `sumilla`, `logro_curso`, `sistema_evaluacion`, `bibliografia`. Migración `0002_upn_metodologia` aplicada. Cursos 2, 3 y 4 migrados.
2. **logro_unidad en Module** — Campo agregado.
3. **Columnas UPN en Lesson** — Campos agregados: `logro_semana`, `saberes_esenciales`, `actividades`, `trabajo_campo`.
4. **Modelos Evaluation y Bibliografia** — Creados y migrados.
5. **Admin actualizado** — CourseAdmin, ModuleAdmin, LessonAdmin, EvaluationAdmin, BibliografiaAdmin actualizados.
6. **API extendida** — `CourseSerializer` y `client.py` aceptan metadatos UPN.
7. **Nomenclatura formalizada** — Convención documentada y aplicada en cursos 3 y 4.
8. **Endpoints API para módulos/lecciones** — `ModuleViewSet`, `LessonViewSet`, `EvaluationViewSet`, `BibliografiaViewSet` creados y registrados en `api/v1/urls.py`.
9. **Bridge extendido** — `client.py` incluye `api_v1_create_module`, `api_v1_create_lesson`, `api_v1_create_evaluation`, `api_v1_create_bibliografia` y métodos list.
