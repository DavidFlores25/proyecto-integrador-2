CREATE DATABASE IF NOT EXISTS restaurante;
USE restaurante;

CREATE TABLE IF NOT EXISTS vendedores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    contrasena VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS reservas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    personas INT NOT NULL,
    dia VARCHAR(20) NOT NULL,
    inicio_str VARCHAR(10) NOT NULL,
    fin_str VARCHAR(10) NOT NULL,
    inicio_min INT NOT NULL,
    fin_min INT NOT NULL,
    estado VARCHAR(50) DEFAULT 'Pendiente'
);

CREATE TABLE IF NOT EXISTS reserva_mesas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_reserva INT NOT NULL,
    numero_mesa INT NOT NULL,
    FOREIGN KEY (id_reserva) REFERENCES reservas(id)
);

INSERT INTO vendedores (nombre, contrasena) VALUES ('Eliezer', 'Romero');
INSERT INTO vendedores (nombre, contrasena) VALUES ('Darwin', 'Eduardo');


USE restaurante;
SELECT r.id, r.nombre, r.personas, r.dia, r.inicio_str, r.fin_str, r.estado, m.numero_mesa
FROM reservas r
LEFT JOIN reserva_mesas m ON r.id = m.id_reserva;
