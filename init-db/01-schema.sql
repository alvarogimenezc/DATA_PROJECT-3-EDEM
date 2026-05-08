-- Tabla de Usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    usuario_id INT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    telefono VARCHAR(20),
    direccion TEXT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Artículos
CREATE TABLE IF NOT EXISTS articulos (
    articulo_id INT PRIMARY KEY,
    nombre VARCHAR(50),
    descripcion TEXT,
    estado VARCHAR(20),
    genero VARCHAR(20),
    categoria VARCHAR(50),
    unidad_medida VARCHAR(10),
    precio_unitario NUMERIC(12, 2)
);

-- Tabla de Transacciones
CREATE TABLE IF NOT EXISTS transacciones (
    transaccion_id INT PRIMARY KEY,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_id INT REFERENCES usuarios(usuario_id),
    articulo_id INT REFERENCES articulos(articulo_id),
    cantidad NUMERIC(12, 3) NOT NULL,
    tipo_movimiento VARCHAR(20),
    coste_total NUMERIC(12, 2)
);