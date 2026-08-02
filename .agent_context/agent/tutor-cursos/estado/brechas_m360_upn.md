# Brechas M360 vs metodología UPN

## Contexto global
- Plan de estudios: `projects/Administracion_UPN/docs/MALLA_CURRICULAR_ADMINISTRACION.md`
- 7 ciclos, con reglas de duración: 17 semanas estándar, 16 para cursos con `**`, virtuales con `***`, teórico-práctico con `(P)`.
- 6 sílabos analizados: Matemática Básica, Complementos de Matemática, Comunicación 1, Desarrollo del Talento, Psicología de la Felicidad, Responsabilidad Social.

## Brechas por entidad

### Course
| Campo UPN | Estado M360 | Impacto |
|-----------|-------------|---------|
| `periodo_lectivo` | No existe | Se pierde periodo oficial |
| `codigo` | No existe | No se puede mapear código UPN |
| `creditos` | No existe | No se puede mapear créditos |
| `ht/hp/hl/pc` | No existe | No se puede mapear carga horaria |
| `requisitos` | No existe | No se puede indicar requisito |
| `naturaleza` | No existe | No se distingue teórico/práctico |
| `competencia_general` | No existe | Se pierde competencia |
| `componentes` | No existe | No se indica Investigación/RS/etc |
| `sumilla` | Parcialmente en `description` | Mezclado con otro texto |
| `logro_curso` | No existe | Se pierde logro formal |
| `sistema_evaluacion` | No existe | Solo se ve en lecciones quiz |
| `bibliografia` | No existe | No hay modelo ni campo |

### Module
| Campo UPN | Estado M360 | Impacto |
|-----------|-------------|---------|
| `logro_unidad` | No existe | No se puede mapear logro por unidad |

### Lesson
| Campo UPN | Estado M360 | Impacto |
|-----------|-------------|---------|
| `logro_semana` | No existe | No se puede mapear logro semanal |
| `saberes_esenciales` | No existe | Se pierde la columna explícita |
| `actividades` | No existe | Se pierde la columna explícita |
| `trabajo_campo` | No existe | Se pierde la columna explícita |

### Evaluation
| Campo UPN | Estado M360 | Impacto |
|-----------|-------------|---------|
| Modelo separado | No existe | No hay trazabilidad de T1-T4/Final/Sustitutoria con peso, semana y descripción |

### Bibliography
| Campo UPN | Estado M360 | Impacto |
|-----------|-------------|---------|
| Modelo separado | No existe | No se puede mapear sección VI del sílabo |

### API
| Necesidad UPN | Estado M360 | Impacto |
|---------------|-------------|---------|
| Endpoints módulos/lecciones | No existen | Obliga a SQL excepcional |

### Admin
| Necesidad UPN | Estado M360 | Impacto |
|---------------|-------------|---------|
| Editor amigable de quizzes | JSON crudo colapsado | Mantenimiento difícil |

## Prioridad de implementación
1. Alta: metadatos UPN en `Course`, `logro_unidad` en `Module`, campos de semana en `Lesson`.
2. Media: modelos `Evaluation` y `Bibliografia`.
3. Media: endpoints API para módulos/lecciones.
4. Baja: mejoras de admin.
