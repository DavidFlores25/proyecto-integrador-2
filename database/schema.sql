CREATE DATABASE IF NOT EXISTS restaurante;
USE restaurante;

RENAME TABLE vendedores TO vendedores_old,
             reservas TO reservas_old,
             reserva_mesas TO reserva_mesas_old;

CREATE TABLE roles (
    id_rol INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE estados (
    id_estado INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE mesas (
    numero_mesa INT PRIMARY KEY
);

INSERT INTO roles (nombre) VALUES ('Vendedor'), ('Consultar reservas');

INSERT INTO estados (nombre) VALUES
    ('Pendiente'), ('Aceptada'), ('Rechazada'), ('Rechazada - Horario en conflicto');

INSERT INTO mesas (numero_mesa) VALUES (1), (2), (3), (4), (5), (6), (7), (8), (9), (10);

CREATE TABLE vendedores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    contrasena VARCHAR(50) NOT NULL,
    id_rol INT NOT NULL DEFAULT 1,
    CONSTRAINT fk_vendedor_rol FOREIGN KEY (id_rol) REFERENCES roles(id_rol)
);

CREATE TABLE clientes (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    correo VARCHAR(100) NOT NULL UNIQUE,
    telefono VARCHAR(20) NULL
);

CREATE TABLE reservas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    id_cliente INT NOT NULL,
    personas INT NOT NULL,
    fecha DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    id_estado INT NOT NULL DEFAULT 1,
    CONSTRAINT fk_reserva_cliente FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
    CONSTRAINT fk_reserva_estado FOREIGN KEY (id_estado) REFERENCES estados(id_estado),
    CONSTRAINT chk_reserva_horas CHECK (hora_inicio < hora_fin)
);

CREATE TABLE reserva_mesas (
    id_reserva INT NOT NULL,
    numero_mesa INT NOT NULL,
    PRIMARY KEY (id_reserva, numero_mesa),
    CONSTRAINT fk_rm_reserva FOREIGN KEY (id_reserva) REFERENCES reservas(id),
    CONSTRAINT fk_rm_mesa FOREIGN KEY (numero_mesa) REFERENCES mesas(numero_mesa)
);

