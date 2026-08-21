-- ============================================================
-- KIROKU · MIGRACIÓN: Multi-curso + eliminación de likes
-- Archivo: migracion_multicurso_sin_likes.sql
--
-- IMPORTANTE: ejecutar sobre una base ya inicializada con mitin.sql
-- Es IDEMPOTENTE: se puede correr más de una vez sin romper nada.
-- ============================================================

USE `apuntes_db`;

START TRANSACTION;

-- ------------------------------------------------------------
-- PASO 1: Crear la tabla pivote usuario_curso (N:M)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `usuario_curso` (
  `id_usuario` int(11) NOT NULL,
  `id_curso`   int(11) NOT NULL,
  `rol_curso`  enum('alumno','moderador') NOT NULL DEFAULT 'alumno',
  `fecha_union` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id_usuario`,`id_curso`),   -- impide duplicados
  KEY `idx_uc_curso` (`id_curso`),
  KEY `idx_uc_usuario` (`id_usuario`),
  CONSTRAINT `uc_ibfk_1` FOREIGN KEY (`id_usuario`)
      REFERENCES `usuario` (`id`) ON DELETE CASCADE,
  CONSTRAINT `uc_ibfk_2` FOREIGN KEY (`id_curso`)
      REFERENCES `curso` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


-- ------------------------------------------------------------
-- PASO 2: MIGRAR los datos existentes de usuario.id_curso
--         (NO destructivo: solo inserta lo que falta)
-- ------------------------------------------------------------
INSERT IGNORE INTO `usuario_curso` (`id_usuario`, `id_curso`, `rol_curso`)
SELECT
    u.id,
    u.id_curso,
    CASE WHEN u.rol = 'moderador' THEN 'moderador' ELSE 'alumno' END
FROM `usuario` u
WHERE u.id_curso IS NOT NULL;

-- Garantizar que el creador de cada curso sea moderador en él
INSERT IGNORE INTO `usuario_curso` (`id_usuario`, `id_curso`, `rol_curso`)
SELECT c.id_creador, c.id, 'moderador'
FROM `curso` c
WHERE c.id_creador IS NOT NULL;

UPDATE `usuario_curso` uc
JOIN `curso` c ON c.id = uc.id_curso AND c.id_creador = uc.id_usuario
SET uc.rol_curso = 'moderador';


-- ------------------------------------------------------------
-- PASO 3: VERIFICACIÓN de la migración
--   Si esto devuelve filas, algo quedó sin migrar -> NO seguir.
-- ------------------------------------------------------------
SELECT u.id AS usuario_sin_migrar, u.nombre, u.id_curso
FROM `usuario` u
LEFT JOIN `usuario_curso` uc
       ON uc.id_usuario = u.id AND uc.id_curso = u.id_curso
WHERE u.id_curso IS NOT NULL AND uc.id_usuario IS NULL;

SELECT COUNT(*) AS relaciones_migradas FROM `usuario_curso`;


-- ------------------------------------------------------------
-- PASO 4: ELIMINAR el sistema de LIKES (me_gusta)
--   Backup previo por si hiciera falta auditarlo.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `_backup_me_gusta` (
  `id_usuario` int(11) NOT NULL,
  `id_apunte`  int(11) NOT NULL,
  `fecha_backup` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `_backup_me_gusta` (`id_usuario`, `id_apunte`)
SELECT `id_usuario`, `id_apunte` FROM `me_gusta`;

-- Nadie referencia a me_gusta (es hoja del grafo de FKs) -> drop seguro
DROP TABLE IF EXISTS `me_gusta`;


-- ------------------------------------------------------------
-- PASO 5: Deprecar usuario.id_curso
--   NO se borra la columna todavía (rollback posible).
--   Se elimina solo la FK para que no bloquee borrados de curso.
-- ------------------------------------------------------------
SET @fk := (
  SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'usuario'
    AND COLUMN_NAME = 'id_curso' AND REFERENCED_TABLE_NAME = 'curso'
  LIMIT 1
);
SET @sql := IF(@fk IS NOT NULL,
    CONCAT('ALTER TABLE `usuario` DROP FOREIGN KEY `', @fk, '`'),
    'SELECT "FK ya eliminada" AS info');
PREPARE st FROM @sql; EXECUTE st; DEALLOCATE PREPARE st;

COMMIT;

-- ============================================================
-- OPCIONAL — ejecutar SOLO tras validar la app en producción:
--   ALTER TABLE `usuario` DROP COLUMN `id_curso`;
--   DROP TABLE `_backup_me_gusta`;
-- ============================================================