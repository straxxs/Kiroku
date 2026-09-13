-- ========================================================
-- MIGRACIÓN: Cumplimiento del contrato Kiroku
-- Agrega: email, me_gusta, audit_log, password_reset_tokens
-- ========================================================

-- 1. Agregar columna email a usuario
ALTER TABLE `usuario`
  ADD COLUMN IF NOT EXISTS `email` VARCHAR(255) DEFAULT NULL AFTER `nombre`;

-- 2. Tabla de "Me Gusta" (likes)
CREATE TABLE IF NOT EXISTS `me_gusta` (
  `id_usuario` int(11) NOT NULL,
  `id_apunte` int(11) NOT NULL,
  PRIMARY KEY (`id_usuario`, `id_apunte`),
  KEY `id_apunte` (`id_apunte`),
  CONSTRAINT `megusta_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuario` (`id`) ON DELETE CASCADE,
  CONSTRAINT `megusta_ibfk_2` FOREIGN KEY (`id_apunte`) REFERENCES `apunte` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 3. Tabla de auditoría
CREATE TABLE IF NOT EXISTS `audit_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) DEFAULT NULL,
  `accion` varchar(100) NOT NULL,
  `detalle` text DEFAULT NULL,
  `ip` varchar(45) DEFAULT NULL,
  `fecha` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `id_usuario` (`id_usuario`),
  KEY `fecha` (`fecha`),
  CONSTRAINT `auditlog_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuario` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 4. Tabla de tokens de recuperación de contraseña
CREATE TABLE IF NOT EXISTS `password_reset_tokens` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) NOT NULL,
  `token` varchar(255) NOT NULL,
  `expira_en` datetime NOT NULL,
  `usado` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `id_usuario` (`id_usuario`),
  KEY `token` (`token`),
  CONSTRAINT `resetoken_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuario` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
