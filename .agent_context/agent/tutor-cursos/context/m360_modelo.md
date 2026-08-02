# context/m360_modelo.md — Modelo de datos de cursos en M360

Fuente: `projects/Management360/courses/models.py` (Postgres Aiven `management360_dev`).

## Entidades (tablas)
- `courses_course` — curso. Campos relevantes: id, title, slug, description, short_description, tutor_id, category_id, level ('beginner'|'intermediate'|'advanced'), price (numeric), duration_hours (int), thumbnail, is_published, is_featured, students_count, average_rating, created_at, updated_at, published_at.
- `courses_coursecategory` — categoría (name, description, slug).
- `courses_module` — unidad. Campos: id, course_id (FK), title, description, order (positive int).
- `courses_lesson` — lección/semana. Campos: id, module_id (FK nullable), title, description, slug, lesson_type ('VIDEO'|'TEXT'|'QUIZ'|'ASSIGNMENT'), content (text/markdown), structured_content (jsonb), video_url, duration_minutes, order, is_published, is_featured, is_free, quiz_questions (jsonb), assignment_instructions, assignment_file, assignment_due_date, author_id, created_at, updated_at.
- `courses_enrollment` — matrícula.
- `courses_progress` — progreso por estudiante.
- `courses_review` — reseña.

## Relación
Course 1─* Module 1─* Lesson. Category es FK opcional en Course.

## Notas de validación (B-M360)
- `Course.save()` exige que el tutor tenga un `Curriculum` asociado; POST/PATCH por API puede fallar con 500 si no se cumple.
- Tutor válido confirmado: `instructor_pl300` (ID 1) con `cv_curriculum` ID 1.
- Política de ejecución: **preferir siempre la API REST de M360**. SQL directo solo como último recurso excepcional si la API falla por validación no superable, y debe registrarse como incidencia en `estado/indice_cursos.md`.

## Templates SQL (solo para fallback excepcional)
```sql
-- Curso (fallback excepcional)
INSERT INTO courses_course (title, slug, description, short_description, tutor_id, category_id, level, price, duration_hours, thumbnail, is_published, is_featured, students_count, average_rating, created_at, updated_at)
VALUES ('UPN Responsabilidad Social', 'upn-responsabilidad-social', '', '', 1, NULL, 'beginner', 0, 2, NULL, true, false, 0, 0, NOW(), NOW());

-- Módulo (fallback excepcional)
INSERT INTO courses_module (course_id, title, description, "order", created_at, updated_at)
VALUES (123, 'Unidad 1', '', 1, NOW(), NOW());

-- Lección (fallback excepcional)
INSERT INTO courses_lesson (module_id, title, description, slug, lesson_type, content, structured_content, video_url, duration_minutes, "order", is_published, is_featured, is_free, quiz_questions, assignment_instructions, assignment_file, assignment_due_date, author_id, created_at, updated_at)
VALUES (456, 'Semana 1', '', 'semana-1', 'TEXT', '# Contenido', '[]'::jsonb, '', 0, 1, true, false, false, '[]'::jsonb, '', NULL, NULL, 1, NOW(), NOW());
```

## Convenciones de nomenclatura (obligatorias)
- Módulos: `Unidad I: <titulo>`, `Unidad II: <titulo>`, etc.
- Lecciones: `Semana 1: <saberes esenciales>`, `Semana 2: <saberes>`, etc.
- lesson_type: valores en minúsculas (`text`, `quiz`, `assignment`).

## Ejemplo real: Matemática Básica (ID 2)
- Módulos: `Unidad I: Ecuaciones e Inecuaciones`, `Unidad II: Matrices y Sistemas de Ecuaciones Lineales`, etc.
- Lecciones: `Semana 1: Intervalos e Inecuaciones Lineales`, `Semana 2: Inecuaciones Cuadráticas`, etc.
- Evaluaciones: semana 4 `quiz`, semana 8 `quiz`, semana 12 `quiz`, semana 15 `assignment`, semana 16 `quiz`, semana 17 `quiz`.

## Campos API cursos (mapeo bridge)
- `api_v1_create_course`: title, slug, project_id (default 0), description, short_description, tutor_id, category_id, level, price, duration_hours, is_published, is_featured.
