# context/migracion_mariadb.md — Auditoría MariaDB antigua → Postgres Aiven

## Estado de la base antigua (termux)
- Host: 192.168.18.59, puerto 8022 = SSH (no MariaDB). MariaDB en 3306 dentro de termux.
- SSH: `sshpass -p 'Peru+123' ssh -p 8022 root@192.168.18.59` (credencial en `mementobloom/.env` TERMUX_ROOT_* y `.memento/vault.json` → `termux_root`).
- MariaDB: `root` / `maria`, base `projects`, datadir `/data/data/com.termux/files/usr/var/lib/mysql`.
- **CORRIENDO** (levantado 2026-07-19, PID 14868). Acceso desde macOS: `pymysql.connect(host="192.168.18.59", port=3306, user="root", password="maria", database="projects")`.

## Hallazgo de la auditoría (2026-07-19)
| Curso (MariaDB) | Mód | Les | En Postgres Aiven |
|-----------------|-----|-----|--------------------|
| UPN Complementos de Matemática (55) | 0 | 0 | ❌ falta |
| Comunicación 1 (56) | 0 | 0 | ❌ falta |
| Desarrollo de Talento (57) | 0 | 0 | ❌ falta |
| Psicología de la Felicidad (58) | 0 | 0 | ❌ falta |
| Responsabilidad Social (59) | 0 | 0 | ❌ falta |
| UPN Complementos (60, borrador) | 0 | 0 | ❌ falta |
| Aritmética (3) | 1 | 3 | ❌ falta |
| Álgebra Básica (50) | 5 | 18 | ❌ falta |

## Conclusión
- Los cursos UPN 55-60 son **cabeceras vacías** en MariaDB → no hay contenido perdido.
- Solo Aritmética y Álgebra tienen lecciones migrables.
- El curso UPN con contenido real (Matemática Básica Ciclo 02) **ya está recreado en Aiven (ID 2)**.
- **No hay pérdida de datos**: la fuente canónica son los sílabos en `projects/Administracion_UPN/docs/`.
