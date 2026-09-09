-- ============================================================
-- KIROKU · MIGRACIÓN: Sistema de gamificación (XP / niveles / logros)
-- Archivo: migracion_gamificacion.sql
-- Idempotente: se puede ejecutar más de una vez.
-- Requiere: migracion_multicurso_sin_likes.sql y migracion_comentarios.sql
-- ============================================================

USE `apuntes_db`;
START TRANSACTION;

-- ------------------------------------------------------------
-- 1. CATÁLOGO DE NIVELES (configurable sin tocar código)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `nivel` (
  `id`          INT(11)     NOT NULL,
  `codigo`      VARCHAR(30) NOT NULL,
  `nombre`      VARCHAR(50) NOT NULL,
  `xp_minimo`   INT(11)     NOT NULL,
  `xp_maximo`   INT(11)     DEFAULT NULL,   -- NULL = sin techo
  `color`       VARCHAR(20) DEFAULT 'gris',
  `icono`       VARCHAR(20) DEFAULT NULL,
  `descripcion` VARCHAR(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_nivel_codigo` (`codigo`),
  KEY `idx_nivel_xp` (`xp_minimo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

REPLACE INTO `nivel`
  (`id`,`codigo`,`nombre`,`xp_minimo`,`xp_maximo`,`color`,`icono`,`descripcion`) VALUES
(0,'bully',       'Bully',        -999999,  -1, 'rojo',    '🚫','Acumulaste más penalizaciones que aportes.'),
(1,'principiante','Principiante',       0,  49, 'gris',    '🌱','Recién empezás a colaborar.'),
(2,'cooperativo', 'Cooperativo',       50, 199, 'celeste', '🤝','Aportás con regularidad al curso.'),
(3,'experto',     'Experto',          200, 599, 'violeta', '🎓','Sos un referente para tus compañeros.'),
(4,'nerd',        'Nerd',             600,NULL, 'amarillo','🤓','Leyenda de KIROKU.');


-- ------------------------------------------------------------
-- 2. REGLAS DE PUNTUACIÓN (editables por SQL, sin deploy)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `regla_puntos` (
  `codigo`        VARCHAR(40)  NOT NULL,
  `descripcion`   VARCHAR(200) NOT NULL,
  `puntos`        INT(11)      NOT NULL,
  `activa`        TINYINT(1)   NOT NULL DEFAULT 1,
  `unico`         TINYINT(1)   NOT NULL DEFAULT 1,  -- 1 = idempotente por clave_objeto
  `cap_diario`    INT(11)      DEFAULT NULL,        -- máx. eventos/día (NULL = sin cap)
  `cooldown_seg`  INT(11)      DEFAULT NULL,        -- seg. mínimos entre eventos
  `permite_auto`  TINYINT(1)   NOT NULL DEFAULT 1,  -- 0 = no XP si actor == beneficiario
  `reversible`    TINYINT(1)   NOT NULL DEFAULT 0,
  PRIMARY KEY (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

REPLACE INTO `regla_puntos`
 (`codigo`,`descripcion`,`puntos`,`unico`,`cap_diario`,`cooldown_seg`,`permite_auto`,`reversible`) VALUES
('APUNTE_APROBADO',          'Tu apunte fue aprobado',              25, 1, NULL, NULL, 1, 1),
('APUNTE_RECHAZADO',         'Tu apunte fue rechazado',            -10, 1, NULL, NULL, 1, 0),
('PRIMER_APUNTE_MATERIA',    'Primer apunte en una materia',        15, 1, NULL, NULL, 1, 0),
('VALORACION_ALTA_RECIBIDA', 'Recibiste 4 o 5 estrellas',            5, 1, NULL, NULL, 0, 1),
('VALORACION_BAJA_RECIBIDA', 'Recibiste 1 o 2 estrellas',           -2, 1, NULL, NULL, 0, 1),
('VALORAR_APUNTE',           'Valoraste un apunte de otro',          2, 1,   10, NULL, 0, 0),
('GUARDADO_RECIBIDO',        'Alguien guardó tu apunte',             4, 1, NULL, NULL, 0, 1),
('COMENTARIO_PUBLICADO',     'Publicaste un comentario',             3, 0,    5,   60, 1, 0),
('COMENTARIO_MODERADO',      'Un moderador eliminó tu comentario',  -5, 1, NULL, NULL, 1, 0),
('MODERAR_APUNTE',           'Moderaste un apunte',                  2, 1,   20, NULL, 0, 0),
('CURSO_CREADO',             'Creaste un curso',                    10, 1, NULL, NULL, 1, 0),
('PERFIL_COMPLETO',          'Completaste tu perfil',                5, 1, NULL, NULL, 1, 0),
('LOGIN_DIARIO',             'Entraste hoy a KIROKU',                1, 1, NULL, NULL, 1, 0);


-- ------------------------------------------------------------
-- 3. LEDGER DE EVENTOS XP (append-only, auditable)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `xp_evento` (
  `id`            BIGINT(20)  NOT NULL AUTO_INCREMENT,
  `id_usuario`    INT(11)     NOT NULL,          -- quién recibe el XP
  `codigo_regla`  VARCHAR(40) NOT NULL,
  `puntos`        INT(11)     NOT NULL,          -- puede ser negativo
  `clave_objeto`  VARCHAR(80) DEFAULT NULL,      -- 'apunte:42', 'apunte:42|user:7'
  `id_curso`      INT(11)     DEFAULT NULL,      -- contexto (rankings por curso)
  `id_actor`      INT(11)     DEFAULT NULL,      -- quién disparó la acción
  `es_reversion`  TINYINT(1)  NOT NULL DEFAULT 0,
  `meta`          VARCHAR(255) DEFAULT NULL,
  `fecha`         DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  -- 🔒 LA defensa anti-farming: la BD rechaza el duplicado
  UNIQUE KEY `uq_xp_idem` (`id_usuario`,`codigo_regla`,`clave_objeto`,`es_reversion`),
  KEY `idx_xp_usuario_fecha` (`id_usuario`,`fecha`),
  KEY `idx_xp_regla_fecha`   (`id_usuario`,`codigo_regla`,`fecha`),
  KEY `idx_xp_curso`         (`id_curso`,`fecha`),
  CONSTRAINT `xpev_ibfk_user`  FOREIGN KEY (`id_usuario`)   REFERENCES `usuario` (`id`) ON DELETE CASCADE,
  CONSTRAINT `xpev_ibfk_actor` FOREIGN KEY (`id_actor`)     REFERENCES `usuario` (`id`) ON DELETE SET NULL,
  CONSTRAINT `xpev_ibfk_regla` FOREIGN KEY (`codigo_regla`) REFERENCES `regla_puntos` (`codigo`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


-- ------------------------------------------------------------
-- 4. AGREGADO POR USUARIO (lectura rápida)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `usuario_xp` (
  `id_usuario`         INT(11)  NOT NULL,
  `xp_total`           INT(11)  NOT NULL DEFAULT 0,
  `id_nivel`           INT(11)  NOT NULL DEFAULT 1,
  `xp_ganado`          INT(11)  NOT NULL DEFAULT 0,  -- solo positivos (histórico)
  `xp_perdido`         INT(11)  NOT NULL DEFAULT 0,  -- solo negativos (abs)
  `racha_dias`         INT(11)  NOT NULL DEFAULT 0,
  `racha_maxima`       INT(11)  NOT NULL DEFAULT 0,
  `ultimo_dia_activo`  DATE     DEFAULT NULL,
  `actualizado`        DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_usuario`),
  KEY `idx_xp_total` (`xp_total` DESC),
  CONSTRAINT `uxp_ibfk_user`  FOREIGN KEY (`id_usuario`) REFERENCES `usuario` (`id`) ON DELETE CASCADE,
  CONSTRAINT `uxp_ibfk_nivel` FOREIGN KEY (`id_nivel`)   REFERENCES `nivel` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


-- ------------------------------------------------------------
-- 5. CATÁLOGO DE LOGROS (agregar uno = 1 INSERT)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `logro` (
  `codigo`      VARCHAR(40)  NOT NULL,
  `nombre`      VARCHAR(80)  NOT NULL,
  `descripcion` VARCHAR(200) NOT NULL,
  `icono`       VARCHAR(20)  DEFAULT '🏅',
  `categoria`   ENUM('aportes','social','constancia','moderacion','especial') DEFAULT 'aportes',
  `metrica`     VARCHAR(40)  NOT NULL,   -- clave en METRICAS (gamificacion.py)
  `operador`    ENUM('>=','>','=','<=','<') NOT NULL DEFAULT '>=',
  `valor`       DECIMAL(10,2) NOT NULL,
  `xp_bonus`    INT(11)      NOT NULL DEFAULT 0,
  `orden`       INT(11)      NOT NULL DEFAULT 0,
  `activo`      TINYINT(1)   NOT NULL DEFAULT 1,
  `oculto`      TINYINT(1)   NOT NULL DEFAULT 0,   -- 1 = secreto hasta desbloquearlo
  PRIMARY KEY (`codigo`),
  KEY `idx_logro_orden` (`activo`,`orden`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

REPLACE INTO `logro`
 (`codigo`,`nombre`,`descripcion`,`icono`,`categoria`,`metrica`,`operador`,`valor`,`xp_bonus`,`orden`) VALUES
('PRIMER_PASO',  'Primer paso',    'Subiste tu primer apunte aprobado.',        '🌟','aportes',    'apuntes_aprobados',   '>=',  1,  5,  10),
('COLABORADOR',  'Colaborador',    'Subiste 5 apuntes aprobados.',              '📚','aportes',    'apuntes_aprobados',   '>=',  5, 10,  20),
('BIBLIOTECARIO','Bibliotecario',  'Subiste 20 apuntes aprobados.',             '🏛️','aportes',    'apuntes_aprobados',   '>=', 20, 25,  30),
('ARCHIVISTA',   'Archivista',     'Subiste 50 apuntes aprobados.',             '🗄️','aportes',    'apuntes_aprobados',   '>=', 50, 50,  40),
('ESTRELLA',     'Estrella',       'Promedio de 4.5+ con al menos 5 valoraciones.','⭐','aportes','promedio_recibido',   '>=',4.5, 30,  50),
('POPULAR',      'Popular',        'Tus apuntes fueron guardados 10 veces.',    '🔖','social',     'guardados_recibidos', '>=', 10, 15,  60),
('CRITICO',      'Crítico',        'Valoraste 10 apuntes de tus compañeros.',   '🔍','social',     'valoraciones_dadas',  '>=', 10, 10,  70),
('CONVERSADOR',  'Conversador',    'Publicaste 10 comentarios.',                '💬','social',     'comentarios',         '>=', 10, 10,  80),
('POLIMATA',     'Polímata',       'Subiste apuntes en 5 materias distintas.',  '🎨','aportes',    'materias_distintas',  '>=',  5, 20,  90),
('MULTICURSO',   'Multicurso',     'Pertenecés a 3 cursos.',                    '🎒','especial',   'cantidad_cursos',     '>=',  3, 10, 100),
('CONSTANTE',    'Constante',      'Entraste 7 días seguidos.',                 '🔥','constancia', 'racha_dias',          '>=',  7, 15, 110),
('MARATON',      'Maratón',        'Entraste 30 días seguidos.',                '🏃','constancia', 'racha_dias',          '>=', 30, 50, 120),
('GUARDIAN',     'Guardián',       'Moderaste 20 apuntes.',                     '🛡️','moderacion', 'apuntes_moderados',   '>=', 20, 25, 130),
('NERD_SUPREMO', 'Nerd supremo',   'Alcanzaste el nivel máximo.',               '🤓','especial',   'xp_total',            '>=',600, 0,  140);


-- ------------------------------------------------------------
-- 6. LOGROS DESBLOQUEADOS POR USUARIO
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `usuario_logro` (
  `id_usuario`    INT(11)     NOT NULL,
  `codigo_logro`  VARCHAR(40) NOT NULL,
  `fecha`         DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `visto`         TINYINT(1)  NOT NULL DEFAULT 0,   -- para notificar "¡nuevo logro!"
  PRIMARY KEY (`id_usuario`,`codigo_logro`),
  KEY `idx_ul_fecha` (`id_usuario`,`fecha`),
  CONSTRAINT `ul_ibfk_user`  FOREIGN KEY (`id_usuario`)   REFERENCES `usuario` (`id`) ON DELETE CASCADE,
  CONSTRAINT `ul_ibfk_logro` FOREIGN KEY (`codigo_logro`) REFERENCES `logro` (`codigo`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


-- ------------------------------------------------------------
-- 7. Inicializar usuario_xp para los usuarios existentes
-- ------------------------------------------------------------
INSERT IGNORE INTO `usuario_xp` (`id_usuario`, `xp_total`, `id_nivel`)
SELECT `id`, 0, 1 FROM `usuario`;

COMMIT;

-- Verificación
SELECT COUNT(*) AS niveles FROM `nivel`;
SELECT COUNT(*) AS reglas  FROM `regla_puntos`;
SELECT COUNT(*) AS logros  FROM `logro`;
SELECT COUNT(*) AS usuarios_inicializados FROM `usuario_xp`;