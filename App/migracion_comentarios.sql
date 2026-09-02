-- ============================================================
-- KIROKU · MIGRACIÓN: sistema de comentarios en apuntes
-- Archivo: migracion_comentarios.sql
-- Idempotente: se puede ejecutar más de una vez.
-- ============================================================

USE `apuntes_db`;

START TRANSACTION;

-- ------------------------------------------------------------
-- 1. Tabla de comentarios (con soft delete)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `comentario` (
  `id`                INT(11)      NOT NULL AUTO_INCREMENT,
  `id_apunte`         INT(11)      NOT NULL,
  `id_usuario`        INT(11)      NOT NULL,
  `contenido`         VARCHAR(500) NOT NULL,
  `fecha_creacion`    DATETIME     DEFAULT CURRENT_TIMESTAMP,
  `fecha_edicion`     DATETIME     DEFAULT NULL,
  `estado`            ENUM('activo','eliminado') NOT NULL DEFAULT 'activo',
  `eliminado_por`     INT(11)      DEFAULT NULL,
  `fecha_eliminacion` DATETIME     DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_com_apunte`  (`id_apunte`, `estado`, `fecha_creacion`),
  KEY `idx_com_usuario` (`id_usuario`),
  CONSTRAINT `com_ibfk_apunte`  FOREIGN KEY (`id_apunte`)
      REFERENCES `apunte` (`id`)  ON DELETE CASCADE,
  CONSTRAINT `com_ibfk_usuario` FOREIGN KEY (`id_usuario`)
      REFERENCES `usuario` (`id`) ON DELETE CASCADE,
  CONSTRAINT `com_ibfk_elimin`  FOREIGN KEY (`eliminado_por`)
      REFERENCES `usuario` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


-- ------------------------------------------------------------
-- 2. Reportes de comentarios (estructura lista para el futuro)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `reporte_comentario` (
  `id`                 INT(11) NOT NULL AUTO_INCREMENT,
  `id_comentario`      INT(11) NOT NULL,
  `id_usuario_reporta` INT(11) NOT NULL,
  `motivo`             ENUM('spam','ofensivo','incorrecto','otro') NOT NULL DEFAULT 'otro',
  `detalle`            VARCHAR(300) DEFAULT NULL,
  `estado`             ENUM('pendiente','revisado','descartado') NOT NULL DEFAULT 'pendiente',
  `fecha`              DATETIME DEFAULT CURRENT_TIMESTAMP,
  `id_moderador`       INT(11) DEFAULT NULL,
  `fecha_revision`     DATETIME DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_reporte` (`id_comentario`,`id_usuario_reporta`),  -- 1 reporte por user
  KEY `idx_rep_estado` (`estado`, `fecha`),
  CONSTRAINT `rep_ibfk_com`  FOREIGN KEY (`id_comentario`)
      REFERENCES `comentario` (`id`) ON DELETE CASCADE,
  CONSTRAINT `rep_ibfk_user` FOREIGN KEY (`id_usuario_reporta`)
      REFERENCES `usuario` (`id`) ON DELETE CASCADE,
  CONSTRAINT `rep_ibfk_mod`  FOREIGN KEY (`id_moderador`)
      REFERENCES `usuario` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

COMMIT;

-- Verificación
SELECT COUNT(*) AS comentarios FROM `comentario`;
SELECT COUNT(*) AS reportes    FROM `reporte_comentario`;