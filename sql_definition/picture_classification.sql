-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 05-11-2024 a las 22:41:57
-- Versión del servidor: 10.4.28-MariaDB
-- Versión de PHP: 8.2.4

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `picture_classification`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `album`
--

CREATE TABLE `album` (
  `album_id` int(11) NOT NULL,
  `location_id` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `date` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `album`
--

INSERT INTO `album` (`album_id`, `location_id`, `name`, `date`) VALUES
(1, 1, 'album 23', '2024-11-05');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `audit`
--

CREATE TABLE `audit` (
  `audit_id` int(11) NOT NULL,
  `date` timestamp NOT NULL DEFAULT current_timestamp(),
  `type` enum('UPDATE','DELETE','CREATE','REQUEST','OTHERS') NOT NULL,
  `request` text NOT NULL,
  `message` text NOT NULL,
  `status` enum('success','error') NOT NULL,
  `user_id` int(11) NOT NULL,
  `entity` enum('project','location','album','picture','category','tag','user','rating') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `audit`
--

INSERT INTO `audit` (`audit_id`, `date`, `type`, `request`, `message`, `status`, `user_id`, `entity`) VALUES
(1, '2024-11-05 19:56:40', 'CREATE', 'http://127.0.0.1:5000/users/register', '{\'status\': \'success\', \'message\': \'Account successfully created\', \'user_name\': \'rafael\', \'user_email\': \'humer-merlin@hotmail.com\'}', 'success', 1, 'user'),
(2, '2024-11-05 19:56:45', 'OTHERS', 'http://127.0.0.1:5000/users/login', '{\'status\': \'success\', \'message\': \'Successful login\', \'token\': \'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MzA5MDE0MDV9.VE5FN45foTHmj2evVAzZie3_AQvTuLvyvM9k04v8txk\'}', 'success', 1, 'user'),
(3, '2024-11-05 19:56:55', 'CREATE', 'http://127.0.0.1:5000/projects/create_project', '{\'status\': \'success\', \'message\': \'The project was saved correctly\', \'project_name\': \'proyecto 1\', \'project_description\': \'swwdsfeswfewfewf\', \'project_date\': \'2024-11-05\'}', 'success', 1, 'project'),
(4, '2024-11-05 19:57:08', 'CREATE', 'http://127.0.0.1:5000/projects/create_location', '{\'status\': \'success\', \'message\': \'Record was saved correctly\', \'location_name\': \'punto 20\', \'location_coordinates\': \'1231231232131, 121213213123\', \'project_id\': 1}', 'success', 1, 'location'),
(5, '2024-11-05 19:57:14', 'CREATE', 'http://127.0.0.1:5000/projects/create_album', '{\'status\': \'success\', \'message\': \'Record was saved correctly\', \'location_id\': 1, \'album_name\': \'album 23\', \'album_date\': \'2024-11-05\'}', 'success', 1, 'album'),
(6, '2024-11-05 20:22:39', 'CREATE', 'http://127.0.0.1:5000/pictures/upload_picture', '{\'status\': \'success\', \'message\': \'Record was saved correctly\', \'picture_id\': \'75729c015cf3670c901467f3845d72276b8518d73a13239574c1a8465afd5bba\', \'filepath\': \'D:\\\\proyectos react\\\\picture_classification\\\\src\\\\app\\\\..\\\\pictures\\\\75729c015cf3670c901467f3845d72276b8518d73a13239574c1a8465afd5bba.jpg\', \'album_id\': 1, \'category_id\': 1}', 'success', 1, 'picture'),
(7, '2024-11-05 20:23:10', 'CREATE', 'http://127.0.0.1:5000/tag_system/create_category', '{\'status\': \'success\', \'message\': \'Record was saved correctly\', \'category_name\': \'categoria 1\'}', 'success', 1, 'category'),
(8, '2024-11-05 20:23:16', 'CREATE', 'http://127.0.0.1:5000/tag_system/create_tag', '{\'status\': \'error\', \'message\': \'Object of type Status is not JSON serializable\'}', 'error', 1, 'tag'),
(9, '2024-11-05 20:23:18', 'CREATE', 'http://127.0.0.1:5000/tag_system/create_tag', '{\'status\': \'error\', \'message\': \'Object of type Status is not JSON serializable\'}', 'error', 1, 'tag'),
(10, '2024-11-05 20:23:20', 'CREATE', 'http://127.0.0.1:5000/tag_system/create_tag', '{\'status\': \'error\', \'message\': \'Object of type Status is not JSON serializable\'}', 'error', 1, 'tag'),
(11, '2024-11-05 20:24:50', 'CREATE', 'http://127.0.0.1:5000/tag_system/create_tag', '{\'status\': \'error\', \'message\': \'Object of type Status is not JSON serializable\'}', 'error', 1, 'tag'),
(12, '2024-11-05 20:31:38', 'CREATE', 'http://127.0.0.1:5000/tag_system/create_tag', '{\'status\': \'error\', \'message\': \'Object of type Status is not JSON serializable\'}', 'error', 1, 'tag'),
(13, '2024-11-05 20:47:22', 'CREATE', 'http://127.0.0.1:5000/tag_system/create_tag', '{\'status\': \'success\', \'message\': \'Status.SUCCESSFULLY_CREATED\', \'tag_name\': \'hrthtrdhyhye2\', \'category_id\': 2}', 'success', 1, 'tag'),
(14, '2024-11-05 20:48:22', 'CREATE', 'http://127.0.0.1:5000/tag_system/create_category', '{\'status\': \'success\', \'message\': \'Record was saved correctly\', \'category_name\': \'categoria 2\'}', 'success', 1, 'category'),
(15, '2024-11-05 21:08:23', 'OTHERS', 'http://127.0.0.1:5000/users/login', '{\'status\': \'success\', \'message\': \'Successful login\', \'token\': \'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MzA5MDU3MDN9.uTygzjzj6rkRXNwgioqCOjVELWLEF20iO0Usg8yrlVg\'}', 'success', 1, 'user'),
(16, '2024-11-05 21:29:19', 'CREATE', 'http://127.0.0.1:5000/ratings/create_rating', '{\'status\': \'success\', \'message\': \'The rating was recorded correctly\', \'picture_id\': \'75729c015cf3670c901467f3845d72276b8518d73a13239574c1a8465afd5bba\', \'user_id\': 1, \'score\': 2.0, \'date\': \'2024-11-05\', \'tag_id\': 6, \'rating_id\': 2}', 'success', 1, 'rating'),
(17, '2024-11-05 21:29:19', 'CREATE', 'http://127.0.0.1:5000/ratings/create_rating', '{\'status\': \'success\', \'message\': \'The rating was recorded correctly\', \'picture_id\': \'75729c015cf3670c901467f3845d72276b8518d73a13239574c1a8465afd5bba\', \'user_id\': 1, \'score\': 0.0, \'date\': \'2024-11-05\', \'tag_id\': 4, \'rating_id\': 1}', 'success', 1, 'rating'),
(18, '2024-11-05 21:29:24', 'DELETE', 'http://127.0.0.1:5000/ratings/delete_rating', '{\'status\': \'success\', \'message\': \'Correctly deleted\'}', 'success', 1, 'rating'),
(19, '2024-11-05 21:29:24', 'DELETE', 'http://127.0.0.1:5000/ratings/delete_rating', '{\'status\': \'success\', \'message\': \'Correctly deleted\'}', 'success', 1, 'rating'),
(20, '2024-11-05 21:29:34', 'DELETE', 'http://127.0.0.1:5000/ratings/delete_rating', '{\'status\': \'success\', \'message\': \'Correctly deleted\'}', 'success', 1, 'rating'),
(21, '2024-11-05 21:29:34', 'DELETE', 'http://127.0.0.1:5000/ratings/delete_rating', '{\'status\': \'success\', \'message\': \'Correctly deleted\'}', 'success', 1, 'rating'),
(22, '2024-11-05 21:29:48', 'DELETE', 'http://127.0.0.1:5000/ratings/delete_rating', '{\'status\': \'success\', \'message\': \'Correctly deleted\'}', 'success', 1, 'rating'),
(23, '2024-11-05 21:29:48', 'DELETE', 'http://127.0.0.1:5000/ratings/delete_rating', '{\'status\': \'success\', \'message\': \'Correctly deleted\'}', 'success', 1, 'rating'),
(24, '2024-11-05 21:31:17', 'UPDATE', 'http://127.0.0.1:5000/ratings/update_rating', '{\'status\': \'success\', \'message\': \'Successfully updated\'}', 'success', 1, 'rating'),
(25, '2024-11-05 21:31:21', 'UPDATE', 'http://127.0.0.1:5000/ratings/update_rating', '{\'status\': \'success\', \'message\': \'Successfully updated\'}', 'success', 1, 'rating'),
(26, '2024-11-05 21:34:58', 'CREATE', 'http://127.0.0.1:5000/ratings/create_rating', '{\'status\': \'success\', \'message\': \'The rating was recorded correctly\', \'picture_id\': \'75729c015cf3670c901467f3845d72276b8518d73a13239574c1a8465afd5bba\', \'user_id\': 1, \'score\': 0.0, \'date\': \'2024-11-05\', \'tag_id\': 3, \'rating_id\': 3}', 'success', 1, 'rating'),
(27, '2024-11-05 21:34:58', 'CREATE', 'http://127.0.0.1:5000/ratings/create_rating', '{\'status\': \'success\', \'message\': \'The rating was recorded correctly\', \'picture_id\': \'75729c015cf3670c901467f3845d72276b8518d73a13239574c1a8465afd5bba\', \'user_id\': 1, \'score\': 0.0, \'date\': \'2024-11-05\', \'tag_id\': 6, \'rating_id\': 4}', 'success', 1, 'rating'),
(28, '2024-11-05 21:34:58', 'CREATE', 'http://127.0.0.1:5000/ratings/create_rating', '{\'status\': \'success\', \'message\': \'The rating was recorded correctly\', \'picture_id\': \'75729c015cf3670c901467f3845d72276b8518d73a13239574c1a8465afd5bba\', \'user_id\': 1, \'score\': 0.0, \'date\': \'2024-11-05\', \'tag_id\': 4, \'rating_id\': 5}', 'success', 1, 'rating'),
(29, '2024-11-05 21:35:04', 'UPDATE', 'http://127.0.0.1:5000/ratings/update_rating', '{\'status\': \'success\', \'message\': \'Successfully updated\'}', 'success', 1, 'rating'),
(30, '2024-11-05 21:35:04', 'UPDATE', 'http://127.0.0.1:5000/ratings/update_rating', '{\'status\': \'success\', \'message\': \'Successfully updated\'}', 'success', 1, 'rating'),
(31, '2024-11-05 21:35:04', 'UPDATE', 'http://127.0.0.1:5000/ratings/update_rating', '{\'status\': \'success\', \'message\': \'Successfully updated\'}', 'success', 1, 'rating'),
(32, '2024-11-05 21:35:18', 'CREATE', 'http://127.0.0.1:5000/tag_system/create_tag', '{\'status\': \'success\', \'message\': \'Status.SUCCESSFULLY_CREATED\', \'tag_name\': \'etiqueta categora 21\', \'category_id\': 3}', 'success', 1, 'tag'),
(33, '2024-11-05 21:35:32', 'CREATE', 'http://127.0.0.1:5000/ratings/create_rating', '{\'status\': \'success\', \'message\': \'The rating was recorded correctly\', \'picture_id\': \'75729c015cf3670c901467f3845d72276b8518d73a13239574c1a8465afd5bba\', \'user_id\': 1, \'score\': 1.5, \'date\': \'2024-11-05\', \'tag_id\': 8, \'rating_id\': 6}', 'success', 1, 'rating'),
(34, '2024-11-05 21:39:02', 'UPDATE', 'http://127.0.0.1:5000/ratings/update_rating', '{\'status\': \'success\', \'message\': \'Successfully updated\'}', 'success', 1, 'rating');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `category`
--

CREATE TABLE `category` (
  `category_id` int(11) NOT NULL,
  `name` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `category`
--

INSERT INTO `category` (`category_id`, `name`) VALUES
(1, 'Not defined'),
(2, 'categoria 1'),
(3, 'categoria 2');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `location`
--

CREATE TABLE `location` (
  `location_id` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `coordinates` varchar(50) NOT NULL,
  `project_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `location`
--

INSERT INTO `location` (`location_id`, `name`, `coordinates`, `project_id`) VALUES
(1, 'punto 20', '1231231232131, 121213213123', 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `picture`
--

CREATE TABLE `picture` (
  `picture_id` char(64) NOT NULL,
  `path` varchar(255) NOT NULL,
  `date` date NOT NULL DEFAULT curdate(),
  `album_id` int(11) NOT NULL,
  `category_id` int(11) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `picture`
--

INSERT INTO `picture` (`picture_id`, `path`, `date`, `album_id`, `category_id`) VALUES
('75729c015cf3670c901467f3845d72276b8518d73a13239574c1a8465afd5bba', 'D:\\proyectos react\\picture_classification\\src\\app\\..\\pictures\\75729c015cf3670c901467f3845d72276b8518d73a13239574c1a8465afd5bba.jpg', '2024-11-05', 1, 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `project`
--

CREATE TABLE `project` (
  `project_id` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `description` varchar(100) NOT NULL,
  `date` date NOT NULL DEFAULT curdate()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `project`
--

INSERT INTO `project` (`project_id`, `name`, `description`, `date`) VALUES
(1, 'proyecto 1', 'swwdsfeswfewfewf', '2024-11-05');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `rating`
--

CREATE TABLE `rating` (
  `date` date NOT NULL DEFAULT curdate(),
  `score` decimal(5,2) NOT NULL,
  `picture_id` char(64) NOT NULL,
  `tag_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `rating_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `rating`
--

INSERT INTO `rating` (`date`, `score`, `picture_id`, `tag_id`, `user_id`, `rating_id`) VALUES
('2024-11-05', 1.00, '75729c015cf3670c901467f3845d72276b8518d73a13239574c1a8465afd5bba', 3, 1, 3),
('2024-11-05', 2.00, '75729c015cf3670c901467f3845d72276b8518d73a13239574c1a8465afd5bba', 6, 1, 4),
('2024-11-05', 1.50, '75729c015cf3670c901467f3845d72276b8518d73a13239574c1a8465afd5bba', 4, 1, 5),
('2024-11-05', 1.50, '75729c015cf3670c901467f3845d72276b8518d73a13239574c1a8465afd5bba', 8, 1, 6);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `tag`
--

CREATE TABLE `tag` (
  `tag_id` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `category_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `tag`
--

INSERT INTO `tag` (`tag_id`, `name`, `category_id`) VALUES
(1, 'Not defined', 1),
(2, 'etiqueta 1', 2),
(3, 'etiqueta 12', 2),
(4, 'etiqueta 122', 2),
(5, 'etiqueta nueva', 2),
(6, 'hrthtrdhyhye', 2),
(7, 'hrthtrdhyhye2', 2),
(8, 'etiqueta categora 21', 3);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `user`
--

CREATE TABLE `user` (
  `user_id` int(11) NOT NULL,
  `email` varchar(50) NOT NULL,
  `name` varchar(50) NOT NULL,
  `password` char(60) NOT NULL,
  `confirmed_on` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `user`
--

INSERT INTO `user` (`user_id`, `email`, `name`, `password`, `confirmed_on`) VALUES
(1, 'humer-merlin@hotmail.com', 'rafael', '$2b$12$dukDr57Pl7xlMajHVCcbOOCKyUNqd8yJsTSXUTQ0s5WNHfDLo7tIO', NULL);

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `album`
--
ALTER TABLE `album`
  ADD PRIMARY KEY (`album_id`),
  ADD UNIQUE KEY `name` (`name`),
  ADD KEY `location_id` (`location_id`);

--
-- Indices de la tabla `audit`
--
ALTER TABLE `audit`
  ADD PRIMARY KEY (`audit_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indices de la tabla `category`
--
ALTER TABLE `category`
  ADD PRIMARY KEY (`category_id`);

--
-- Indices de la tabla `location`
--
ALTER TABLE `location`
  ADD PRIMARY KEY (`location_id`),
  ADD UNIQUE KEY `name` (`name`),
  ADD KEY `project_id` (`project_id`);

--
-- Indices de la tabla `picture`
--
ALTER TABLE `picture`
  ADD PRIMARY KEY (`picture_id`);

--
-- Indices de la tabla `project`
--
ALTER TABLE `project`
  ADD PRIMARY KEY (`project_id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indices de la tabla `rating`
--
ALTER TABLE `rating`
  ADD PRIMARY KEY (`rating_id`);

--
-- Indices de la tabla `tag`
--
ALTER TABLE `tag`
  ADD PRIMARY KEY (`tag_id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indices de la tabla `user`
--
ALTER TABLE `user`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `email` (`email`),
  ADD UNIQUE KEY `name` (`name`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `album`
--
ALTER TABLE `album`
  MODIFY `album_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de la tabla `audit`
--
ALTER TABLE `audit`
  MODIFY `audit_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=35;

--
-- AUTO_INCREMENT de la tabla `category`
--
ALTER TABLE `category`
  MODIFY `category_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `location`
--
ALTER TABLE `location`
  MODIFY `location_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de la tabla `project`
--
ALTER TABLE `project`
  MODIFY `project_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de la tabla `rating`
--
ALTER TABLE `rating`
  MODIFY `rating_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT de la tabla `tag`
--
ALTER TABLE `tag`
  MODIFY `tag_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT de la tabla `user`
--
ALTER TABLE `user`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `album`
--
ALTER TABLE `album`
  ADD CONSTRAINT `album_ibfk_1` FOREIGN KEY (`location_id`) REFERENCES `location` (`location_id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `audit`
--
ALTER TABLE `audit`
  ADD CONSTRAINT `audit_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`);

--
-- Filtros para la tabla `location`
--
ALTER TABLE `location`
  ADD CONSTRAINT `location_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `project` (`project_id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
