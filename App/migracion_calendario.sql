-- ============================================================
-- KIROKU · MIGRACIÓN: Calendario académico
-- Archivo: migracion_calendario.sql
-- Idempotente. Requiere: migracion_multicurso_sin_likes.sql
-- ============================================================

USE `apuntes_db`;
START TRANSACTION;

-- ------------------------------------------------------------
-- 1. EVENTOS
--    Guarda SOLO eventos manuales. Los derivados (tareas de
--    proyecto) se PROYECTAN en vivo desde su tabla origen.
--    Las columnas origen_* permiten materializar si algún día
--    hace falta (ver "Modo B" en la doc del módulo).
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `evento` (
  `id`                 INT(11)      NOT NULL AUTO_INCREMENT,
  `titulo`             VARCHAR(120) NOT NULL,
  `descripcion`        VARCHAR(500) DEFAULT NULL,
  `tipo`               ENUM('examen','entrega','tarea','reunion','otro')
                       NOT NULL DEFAULT 'otro',
  -- 'proyecto' YA está en el enum: sin ALTER TABLE cuando llegue la feature
  `ambito`             ENUM('personal','curso','proyecto')
                       NOT NULL DEFAULT 'personal',
  `fecha`              DATE         NOT NULL,
  `hora`               TIME         DEFAULT NULL,   -- hora límite (opcional)
  `fecha_fin`          DATE         DEFAULT NULL,   -- rango (opcional)
  `id_usuario_creador` INT(11)      NOT NULL,
  `id_curso`           INT(11)      DEFAULT NULL,   -- NULL si ambito='personal'
  `id_materia`         INT(11)      DEFAULT NULL,   -- etiqueta/filtro
  -- ---- Polimorfismo para fuentes externas (proyectos, etc.) ----
  `origen_tipo`        VARCHAR(30)  NOT NULL DEFAULT 'manual',
  `origen_id`          INT(11)      DEFAULT NULL,
  -- --------------------------------------------------------------
  `color`              VARCHAR(20)  DEFAULT NULL,
  `estado`             ENUM('activo','archivado') NOT NULL DEFAULT 'activo',
  `fecha_creacion`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_edicion`      DATETIME     DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_ev_curso_fecha`   (`id_curso`, `fecha`, `estado`),
  KEY `idx_ev_autor_fecha`   (`id_usuario_creador`, `fecha`, `estado`),
  KEY `idx_ev_materia`       (`id_materia`),
  KEY `idx_ev_fecha`         (`fecha`),
  -- Evita materializar dos veces el mismo objeto externo
  UNIQUE KEY `uq_ev_origen`  (`origen_tipo`, `origen_id`),
  CONSTRAINT `ev_ibfk_user`    FOREIGN KEY (`id_usuario_creador`)
      REFERENCES `usuario` (`id`) ON DELETE CASCADE,
  CONSTRAINT `ev_ibfk_curso`   FOREIGN KEY (`id_curso`)
      REFERENCES `curso` (`id`)   ON DELETE CASCADE,
  CONSTRAINT `ev_ibfk_materia` FOREIGN KEY (`id_materia`)
      REFERENCES `materia` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


-- ------------------------------------------------------------
-- 2. COMPLETADO POR USUARIO
--    Un examen de curso lo marca cada alumno individualmente.
--    'origen_tipo' permite marcar también eventos derivados.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `evento_completado` (
  `id_usuario`  INT(11)     NOT NULL,
  `origen_tipo` VARCHAR(30) NOT NULL DEFAULT 'manual',
  `origen_id`   INT(11)     NOT NULL,   -- id del evento o del objeto externo
  `fecha`       DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_usuario`, `origen_tipo`, `origen_id`),
  KEY `idx_evc_obj` (`origen_tipo`, `origen_id`),
  CONSTRAINT `evc_ibfk_user` FOREIGN KEY (`id_usuario`)
      REFERENCES `usuario` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


-- ------------------------------------------------------------
-- 3. Regla de XP (si ya corriste migracion_gamificacion.sql)
--    Solo eventos de CURSO creados por moderadores.
--    Cap 3/día → no se puede farmear creando eventos basura.
-- ------------------------------------------------------------
INSERT IGNORE INTO `regla_puntos`
 (`codigo`,`descripcion`,`puntos`,`unico`,`cap_diario`,`cooldown_seg`,`permite_auto`,`reversible`)
VALUES
('EVENTO_CURSO_CREADO','Publicaste un evento para el curso',3,1,3,NULL,1,1);


-- ------------------------------------------------------------
-- 4. Logro (opcional, solo si existe la tabla `logro`)
-- ------------------------------------------------------------
INSERT IGNORE INTO `logro`
 (`codigo`,`nombre`,`descripcion`,`icono`,`categoria`,`metrica`,`operador`,`valor`,`xp_bonus`,`orden`)
VALUES
('ORGANIZADO','Organizado','Publicaste 10 eventos para tu curso.','📅','aportes',
 'eventos_curso','>=',10,15,105);

COMMIT;

-- Verificación
SELECT COUNT(*) AS eventos FROM `evento`;
SHOW COLUMNS FROM `evento` LIKE 'ambito';