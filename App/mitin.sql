CREATE DATABASE apuntes_db
USE apuntes_db

CREATE TABLE Curso(
    id INT AUTO_INCREMENT PRIMARY KEY,
    anio INT NOT NULL,
    division VARCHAR(10) NOT NULL,
    id_creador INT,
    FOREIGN KEY (id_creador) REFERENCES Usuario(id)
);

CREATE TABLE Profesor(
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100)
);

CREATE TABLE Materia (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    id_profesor INT,
    id_curso INT,
    FOREIGN KEY (id_profesor) REFERENCES Profesor(id),
    FOREIGN KEY (id_curso) REFERENCES Curso(id)
);

CREATE TABLE Usuario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    contrasena VARCHAR(255) NOT NULL,
    rol ENUM('alumno', 'admin', 'moderador') DEFAULT 'alumno',
    id_curso INT,
    FOREIGN KEY (id_curso) REFERENCES Curso(id)
);

CREATE TABLE Apunte (
    id INT AUTO_INCREMENT PRIMARY KEY,
    descripcion TEXT,
    id_usuario_creador INT,
    id_curso INT,
    id_materia INT,
    FOREIGN KEY (id_usuario_creador) REFERENCES Usuario(id),
    FOREIGN KEY (id_curso) REFERENCES Curso(id),
    FOREIGN KEY (id_materia) REFERENCES Materia(id)
);

CREATE TABLE Archivo_Apunte (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ruta VARCHAR(255) NOT NULL,
    tipo VARCHAR(50),
    id_apunte INT,
    FOREIGN KEY (id_apunte) REFERENCES Apunte(id)
);

CREATE TABLE Guardado (
    id_alumno INT,
    id_apunte INT,
    PRIMARY KEY (id_alumno, id_apunte),
    FOREIGN KEY (id_alumno) REFERENCES Usuario(id),
    FOREIGN KEY (id_apunte) REFERENCES Apunte(id)
);

CREATE TABLE Calificacion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    comentario TEXT,
    calificacion INT CHECK (calificacion BETWEEN 1 AND 5),
    id_alumno INT,
    id_apunte INT,
    UNIQUE (id_alumno, id_apunte),
    FOREIGN KEY (id_alumno) REFERENCES Usuario(id),
    FOREIGN KEY (id_apunte) REFERENCES Apunte(id)
);
