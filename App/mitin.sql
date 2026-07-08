-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 08-07-2026 a las 16:06:31
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

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

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `apunte`
--

CREATE TABLE `apunte` (
  `id` int(11) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `id_usuario_creador` int(11) DEFAULT NULL,
  `id_curso` int(11) DEFAULT NULL,
  `id_materia` int(11) DEFAULT NULL,
  `titulo` varchar(100) NOT NULL,
  `estado` enum('pendiente','aprobado','rechazado') DEFAULT 'pendiente',
  `fecha_subida` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `apunte`
--

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

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `archivo_apunte`
--

CREATE TABLE `archivo_apunte` (
  `id` int(11) NOT NULL,
  `ruta` varchar(255) NOT NULL,
  `tipo` varchar(50) DEFAULT NULL,
  `id_apunte` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `archivo_apunte`
--

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

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `calificacion`
--

CREATE TABLE `calificacion` (
  `id` int(11) NOT NULL,
  `comentario` text DEFAULT NULL,
  `calificacion` int(11) DEFAULT NULL CHECK (`calificacion` between 1 and 5),
  `id_alumno` int(11) DEFAULT NULL,
  `id_apunte` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `calificacion`
--

INSERT INTO `calificacion` (`id`, `comentario`, `calificacion`, `id_alumno`, `id_apunte`) VALUES
(1, NULL, 4, 15, 13),
(2, NULL, 3, 16, 12),
(4, NULL, 2, 16, 13);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `curso`
--

CREATE TABLE `curso` (
  `id` int(11) NOT NULL,
  `anio` int(11) NOT NULL,
  `division` varchar(25) NOT NULL,
  `id_creador` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `curso`
--

INSERT INTO `curso` (`id`, `anio`, `division`, `id_creador`) VALUES
(1, 3, '5', 1),
(6, 6, '3', 14);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `guardado`
--

CREATE TABLE `guardado` (
  `id_alumno` int(11) NOT NULL,
  `id_apunte` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `guardado`
--

INSERT INTO `guardado` (`id_alumno`, `id_apunte`) VALUES
(15, 13),
(16, 13);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `materia`
--

CREATE TABLE `materia` (
  `id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `id_profesor` int(11) DEFAULT NULL,
  `id_curso` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `materia`
--

INSERT INTO `materia` (`id`, `nombre`, `id_profesor`, `id_curso`) VALUES
(1, 'Silva1', 2, 1),
(7, 'POO', 2, 6);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `profesor`
--

CREATE TABLE `profesor` (
  `id` int(11) NOT NULL,
  `nombre` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `profesor`
--

INSERT INTO `profesor` (`id`, `nombre`) VALUES
(1, 'baglietto'),
(2, 'Silva'),
(3, 'Jones'),
(4, 'FOLIGOAT'),
(5, 'asd'),
(6, 'ramiro'),
(7, 'Mitin');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuario`
--

CREATE TABLE `usuario` (
  `id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `contrasena` varchar(255) NOT NULL,
  `avatar` varchar(255) DEFAULT NULL,
  `rol` enum('alumno','admin','moderador') DEFAULT 'alumno',
  `id_curso` int(11) DEFAULT NULL,
  `estado` enum('activo','bloqueado') DEFAULT 'activo'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `usuario`
--

INSERT INTO `usuario` (`id`, `nombre`, `contrasena`, `avatar`, `rol`, `id_curso`, `estado`) VALUES
(1, 'testuser', 'c203b9af7abd13b642334c14a08e28b2a326c89c3d367e843c374fab0d487897', 'uploads/avatares/avatar3.png', 'moderador', 1, 'activo'),
(3, 'leon', 'a1159e9df3670d549d04524532629f5477ceb7deec9b45e47e8c009506ecb2c8', 'uploads/avatares/avatar1.png', 'alumno', 1, 'activo'),
(4, 'Matias234', '114bd151f8fb0c58642d2170da4ae7d7c57977260ac2cc8905306cab6b2acabc', 'uploads/avatares/avatar2.png', 'alumno', NULL, 'activo'),
(8, 'testuser2', 'ae5deb822e0d71992900471a7199d0d95b8e7c9d05c40a8245a281fd2c1d6684', 'uploads/avatares/avatar3.png', 'admin', 1, 'activo'),
(9, 'chau', '2274631b81def59664f20cb9fa010e4cde57f64a263f2874dfde0fe346d59c60', NULL, 'moderador', 1, 'activo'),
(10, 'florian', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 'uploads/avatares/avatar9.png', 'moderador', 1, 'activo'),
(11, 'titi', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 'uploads/avatares/avatar3.png', 'alumno', NULL, 'activo'),
(12, 'hamlin', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', NULL, 'alumno', NULL, 'activo'),
(14, 'federico', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 'uploads/avatares/avatar3.png', 'moderador', 1, 'activo'),
(15, 'maxi', 'bd9eb395eea21d71ed21eaffc0c258bd2501c06135371dbfecde0a013630e6e0', NULL, 'alumno', 1, 'activo'),
(16, 'lolaso', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', NULL, 'alumno', 1, 'activo');

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `apunte`
--
ALTER TABLE `apunte`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id_usuario_creador` (`id_usuario_creador`),
  ADD KEY `id_curso` (`id_curso`),
  ADD KEY `id_materia` (`id_materia`);

--
-- Indices de la tabla `archivo_apunte`
--
ALTER TABLE `archivo_apunte`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id_apunte` (`id_apunte`);

--
-- Indices de la tabla `calificacion`
--
ALTER TABLE `calificacion`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id_alumno` (`id_alumno`,`id_apunte`),
  ADD KEY `id_apunte` (`id_apunte`);

--
-- Indices de la tabla `curso`
--
ALTER TABLE `curso`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id_creador` (`id_creador`);

--
-- Indices de la tabla `guardado`
--
ALTER TABLE `guardado`
  ADD PRIMARY KEY (`id_alumno`,`id_apunte`),
  ADD KEY `id_apunte` (`id_apunte`);

--
-- Indices de la tabla `materia`
--
ALTER TABLE `materia`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id_profesor` (`id_profesor`),
  ADD KEY `id_curso` (`id_curso`);

--
-- Indices de la tabla `profesor`
--
ALTER TABLE `profesor`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `usuario`
--
ALTER TABLE `usuario`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nombre` (`nombre`),
  ADD KEY `id_curso` (`id_curso`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `apunte`
--
ALTER TABLE `apunte`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT de la tabla `archivo_apunte`
--
ALTER TABLE `archivo_apunte`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=18;

--
-- AUTO_INCREMENT de la tabla `calificacion`
--
ALTER TABLE `calificacion`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT de la tabla `curso`
--
ALTER TABLE `curso`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT de la tabla `materia`
--
ALTER TABLE `materia`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT de la tabla `profesor`
--
ALTER TABLE `profesor`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT de la tabla `usuario`
--
ALTER TABLE `usuario`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=17;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `apunte`
--
ALTER TABLE `apunte`
  ADD CONSTRAINT `apunte_ibfk_1` FOREIGN KEY (`id_usuario_creador`) REFERENCES `usuario` (`id`),
  ADD CONSTRAINT `apunte_ibfk_2` FOREIGN KEY (`id_curso`) REFERENCES `curso` (`id`),
  ADD CONSTRAINT `apunte_ibfk_3` FOREIGN KEY (`id_materia`) REFERENCES `materia` (`id`);

--
-- Filtros para la tabla `archivo_apunte`
--
ALTER TABLE `archivo_apunte`
  ADD CONSTRAINT `archivo_apunte_ibfk_1` FOREIGN KEY (`id_apunte`) REFERENCES `apunte` (`id`);

--
-- Filtros para la tabla `calificacion`
--
ALTER TABLE `calificacion`
  ADD CONSTRAINT `calificacion_ibfk_1` FOREIGN KEY (`id_alumno`) REFERENCES `usuario` (`id`),
  ADD CONSTRAINT `calificacion_ibfk_2` FOREIGN KEY (`id_apunte`) REFERENCES `apunte` (`id`);

--
-- Filtros para la tabla `curso`
--
ALTER TABLE `curso`
  ADD CONSTRAINT `curso_ibfk_1` FOREIGN KEY (`id_creador`) REFERENCES `usuario` (`id`);

--
-- Filtros para la tabla `guardado`
--
ALTER TABLE `guardado`
  ADD CONSTRAINT `guardado_ibfk_1` FOREIGN KEY (`id_alumno`) REFERENCES `usuario` (`id`),
  ADD CONSTRAINT `guardado_ibfk_2` FOREIGN KEY (`id_apunte`) REFERENCES `apunte` (`id`);

--
-- Filtros para la tabla `materia`
--
ALTER TABLE `materia`
  ADD CONSTRAINT `materia_ibfk_1` FOREIGN KEY (`id_profesor`) REFERENCES `profesor` (`id`),
  ADD CONSTRAINT `materia_ibfk_2` FOREIGN KEY (`id_curso`) REFERENCES `curso` (`id`);

--
-- Filtros para la tabla `usuario`
--
ALTER TABLE `usuario`
  ADD CONSTRAINT `usuario_ibfk_1` FOREIGN KEY (`id_curso`) REFERENCES `curso` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
