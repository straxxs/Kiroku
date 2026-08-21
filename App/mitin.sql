-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 10-07-2026

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `apuntes_db`
--
CREATE DATABASE IF NOT EXISTS `apuntes_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `apuntes_db`;

-- Desactivar verificación de foreign keys para importar datos
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- 1. CREAR TODAS LAS TABLAS (con PK incluida)
-- ============================================================

CREATE TABLE IF NOT EXISTS `usuario` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `email` varchar(255) DEFAULT NULL,
  `contrasena` varchar(255) NOT NULL,
  `avatar` varchar(255) DEFAULT NULL,
  `rol` enum('alumno','admin','moderador') DEFAULT 'alumno',
  `id_curso` int(11) DEFAULT NULL,
  `estado` enum('activo','bloqueado') DEFAULT 'activo',
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `curso` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `anio` int(11) NOT NULL,
  `division` varchar(25) NOT NULL,
  `id_creador` int(11) DEFAULT NULL,
  `codigo_invitacion` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `profesor` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `materia` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `id_profesor` int(11) DEFAULT NULL,
  `id_curso` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `apunte` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `descripcion` text DEFAULT NULL,
  `id_usuario_creador` int(11) DEFAULT NULL,
  `id_curso` int(11) DEFAULT NULL,
  `id_materia` int(11) DEFAULT NULL,
  `titulo` varchar(100) NOT NULL,
  `estado` enum('pendiente','aprobado','rechazado') DEFAULT 'pendiente',
  `fecha_subida` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `archivo_apunte` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ruta` varchar(255) NOT NULL,
  `tipo` varchar(50) DEFAULT NULL,
  `id_apunte` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `calificacion` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `comentario` text DEFAULT NULL,
  `calificacion` int(11) DEFAULT NULL CHECK (`calificacion` between 1 and 5),
  `id_alumno` int(11) DEFAULT NULL,
  `id_apunte` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_alumno` (`id_alumno`,`id_apunte`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `guardado` (
  `id_alumno` int(11) NOT NULL,
  `id_apunte` int(11) NOT NULL,
  PRIMARY KEY (`id_alumno`,`id_apunte`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ... (todo igual hasta la creación de tablas) ...

-- REEMPLAZAR el bloque de me_gusta por:
CREATE TABLE IF NOT EXISTS `usuario_curso` (
  `id_usuario` int(11) NOT NULL,
  `id_curso` int(11) NOT NULL,
  `rol_curso` enum('alumno','moderador') NOT NULL DEFAULT 'alumno',
  `fecha_union` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id_usuario`,`id_curso`),
  KEY `idx_uc_curso` (`id_curso`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


CREATE TABLE IF NOT EXISTS `audit_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) DEFAULT NULL,
  `accion` varchar(100) NOT NULL,
  `detalle` text DEFAULT NULL,
  `ip` varchar(45) DEFAULT NULL,
  `fecha` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `password_reset_tokens` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) NOT NULL,
  `token` varchar(255) NOT NULL,
  `expira_en` datetime NOT NULL,
  `usado` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ============================================================
-- 2. DATOS DE EJEMPLO (sin FK checks)
-- ============================================================

INSERT INTO `curso` (`id`, `anio`, `division`, `id_creador`, `codigo_invitacion`) VALUES
(1, 3, '5', 1, 'EB2A-CB75'),
(6, 6, '3', 14, '1420-2FE4');

INSERT INTO `usuario` (`id`, `nombre`, `email`, `contrasena`, `avatar`, `rol`, `id_curso`, `estado`) VALUES
(1, 'testuser', 'testuser@kiroku.com', 'c203b9af7abd13b642334c14a08e28b2a326c89c3d367e843c374fab0d487897', 'uploads/avatares/avatar3.png', 'moderador', 1, 'activo'),
(3, 'leon', 'leon@kiroku.com', 'a1159e9df3670d549d04524532629f5477ceb7deec9b45e47e8c009506ecb2c8', 'uploads/avatares/avatar1.png', 'alumno', 1, 'activo'),
(4, 'Matias234', 'matias234@kiroku.com', '114bd151f8fb0c58642d2170da4ae7d7c57977260ac2cc8905306cab6b2acabc', 'uploads/avatares/avatar2.png', 'alumno', NULL, 'activo'),
(8, 'testuser2', 'testuser2@kiroku.com', 'ae5deb822e0d71992900471a7199d0d95b8e7c9d05c40a8245a281fd2c1d6684', 'uploads/avatares/avatar3.png', 'admin', 1, 'activo'),
(9, 'chau', 'chau@kiroku.com', '2274631b81def59664f20cb9fa010e4cde57f64a263f2874dfde0fe346d59c60', NULL, 'moderador', 1, 'activo'),
(10, 'florian', 'florian@kiroku.com', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 'uploads/avatares/avatar9.png', 'moderador', 1, 'activo'),
(11, 'titi', 'titi@kiroku.com', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 'uploads/avatares/avatar3.png', 'alumno', NULL, 'activo'),
(12, 'hamlin', 'hamlin@kiroku.com', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', NULL, 'alumno', NULL, 'activo'),
(14, 'federico', 'federico@kiroku.com', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 'uploads/avatares/avatar3.png', 'moderador', 1, 'activo'),
(15, 'maxi', 'maxi@kiroku.com', 'bd9eb395eea21d71ed21eaffc0c258bd2501c06135371dbfecde0a013630e6e0', NULL, 'alumno', 1, 'activo'),
(16, 'lolaso', 'lolaso@kiroku.com', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', NULL, 'alumno', 1, 'activo');

INSERT INTO `profesor` (`id`, `nombre`) VALUES
(1, 'baglietto'),
(2, 'Silva'),
(3, 'Jones'),
(4, 'FOLIGOAT'),
(5, 'asd'),
(6, 'ramiro'),
(7, 'Mitin');

INSERT INTO `materia` (`id`, `nombre`, `id_profesor`, `id_curso`) VALUES
(1, 'Silva1', 2, 1),
(7, 'POO', 2, 6);

INSERT INTO `apunte` (`id`, `descripcion`, `id_usuario_creador`, `id_curso`, `id_materia`, `titulo`, `estado`, `fecha_subida`) VALUES
(1, 'imagen de google nashee', 1, 1, 1, '', 'rechazado', '2026-07-06 11:39:03'),
(4, 'PDF', 8, 1, 1, '', 'rechazado', '2026-07-06 11:39:03'),
(6, 'Fedroleski', 10, 1, 1, '', 'rechazado', '2026-07-06 11:39:03'),
(8, 'PDF prueba', 14, 6, 7, '', 'pendiente', '2026-07-06 11:39:03'),
(10, '', 14, 1, 1, 'hola', 'aprobado', '2026-07-06 11:48:54'),
(11, '', 14, 1, 1, 'Prueba apuntes', 'aprobado', '2026-07-06 11:50:07'),
(12, '', 14, 1, 1, 'Prueba apuntes2', 'aprobado', '2026-07-06 11:50:42'),
(13, '', 14, 1, 1, 'Prueba apuntes multiples', 'aprobado', '2026-07-06 12:07:37'),
(14, 'gay', 16, 1, 1, 'La concha de tu madre', 'rechazado', '2026-07-08 11:01:55');

INSERT INTO `archivo_apunte` (`id`, `ruta`, `tipo`, `id_apunte`) VALUES
(1, 'uploads/apuntes/apunte1_134272096816238793.jpg', 'jpg', 1),
(4, 'uploads/apuntes/apunte4_figurita_1.pdf', 'pdf', 4),
(6, 'uploads/apuntes/apunte6_avatar9.png', 'png', 6),
(8, 'uploads/apuntes/apunte8_figurita_1.pdf', 'pdf', 8),
(12, 'uploads/apuntes/apunte10_avatar7.png', 'png', 10),
(13, 'uploads/apuntes/apunte11_avatar0.png', 'png', 11),
(14, 'uploads/apuntes/apunte12_avatar0.png', 'png', 12),
(15, 'uploads/apuntes/apunte13_avatar6.png', 'png', 13),
(16, 'uploads/apuntes/apunte13_avatar7.png', 'png', 13),
(17, 'uploads/apuntes/apunte13_no_avatar.png', 'png', 13);

INSERT INTO `calificacion` (`id`, `comentario`, `calificacion`, `id_alumno`, `id_apunte`) VALUES
(1, NULL, 4, 15, 13),
(2, NULL, 3, 16, 12),
(4, NULL, 2, 16, 13);

INSERT INTO `guardado` (`id_alumno`, `id_apunte`) VALUES
(15, 13),
(16, 13);

INSERT INTO `usuario_curso` (`id_usuario`, `id_curso`, `rol_curso`) VALUES
(1, 1, 'moderador'),
(3, 1, 'alumno'),
(8, 1, 'alumno'),
(9, 1, 'moderador'),
(10, 1, 'moderador'),
(14, 1, 'moderador'),
(14, 6, 'moderador'),
(15, 1, 'alumno'),
(16, 1, 'alumno');

-- ============================================================
-- 3. AGREGAR FOREIGN KEYS (ahora que los datos existen)
-- ============================================================

ALTER TABLE `usuario`
  ADD CONSTRAINT `usuario_ibfk_1` FOREIGN KEY (`id_curso`) REFERENCES `curso` (`id`);

ALTER TABLE `curso`
  ADD CONSTRAINT `curso_ibfk_1` FOREIGN KEY (`id_creador`) REFERENCES `usuario` (`id`);

ALTER TABLE `materia`
  ADD CONSTRAINT `materia_ibfk_1` FOREIGN KEY (`id_profesor`) REFERENCES `profesor` (`id`),
  ADD CONSTRAINT `materia_ibfk_2` FOREIGN KEY (`id_curso`) REFERENCES `curso` (`id`);

ALTER TABLE `apunte`
  ADD CONSTRAINT `apunte_ibfk_1` FOREIGN KEY (`id_usuario_creador`) REFERENCES `usuario` (`id`),
  ADD CONSTRAINT `apunte_ibfk_2` FOREIGN KEY (`id_curso`) REFERENCES `curso` (`id`),
  ADD CONSTRAINT `apunte_ibfk_3` FOREIGN KEY (`id_materia`) REFERENCES `materia` (`id`);

ALTER TABLE `archivo_apunte`
  ADD CONSTRAINT `archivo_apunte_ibfk_1` FOREIGN KEY (`id_apunte`) REFERENCES `apunte` (`id`);

ALTER TABLE `calificacion`
  ADD CONSTRAINT `calificacion_ibfk_1` FOREIGN KEY (`id_alumno`) REFERENCES `usuario` (`id`),
  ADD CONSTRAINT `calificacion_ibfk_2` FOREIGN KEY (`id_apunte`) REFERENCES `apunte` (`id`);

ALTER TABLE `guardado`
  ADD CONSTRAINT `guardado_ibfk_1` FOREIGN KEY (`id_alumno`) REFERENCES `usuario` (`id`),
  ADD CONSTRAINT `guardado_ibfk_2` FOREIGN KEY (`id_apunte`) REFERENCES `apunte` (`id`);


ALTER TABLE `usuario_curso`
  ADD CONSTRAINT `uc_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuario` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `uc_ibfk_2` FOREIGN KEY (`id_curso`) REFERENCES `curso` (`id`) ON DELETE CASCADE;


ALTER TABLE `audit_log`
  ADD CONSTRAINT `auditlog_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuario` (`id`) ON DELETE SET NULL;

ALTER TABLE `password_reset_tokens`
  ADD CONSTRAINT `resetoken_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuario` (`id`) ON DELETE CASCADE;

-- ============================================================
-- 4. AUTO_INCREMENT offsets
-- ============================================================

ALTER TABLE `usuario` AUTO_INCREMENT=17;
ALTER TABLE `curso` AUTO_INCREMENT=7;
ALTER TABLE `profesor` AUTO_INCREMENT=8;
ALTER TABLE `materia` AUTO_INCREMENT=8;
ALTER TABLE `apunte` AUTO_INCREMENT=15;
ALTER TABLE `archivo_apunte` AUTO_INCREMENT=18;
ALTER TABLE `calificacion` AUTO_INCREMENT=9;

-- Reactivar verificación de foreign keys
SET FOREIGN_KEY_CHECKS = 1;

COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
