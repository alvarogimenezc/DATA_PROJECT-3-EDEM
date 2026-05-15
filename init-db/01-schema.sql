CREATE TABLE IF NOT EXISTS usuarios (
    usuario_id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    telefono VARCHAR(20),
    direccion TEXT,
    password_hash VARCHAR(255) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS articulos (
    articulo_id SERIAL PRIMARY KEY,
    nombre VARCHAR(50),
    descripcion TEXT,
    estado VARCHAR(20),
    categoria VARCHAR(50),
    unidad_medida VARCHAR(10),
    precio_unitario NUMERIC(12, 2),
    url_imagen VARCHAR(255),
    talla VARCHAR(5),
    es_drop BOOLEAN DEFAULT FALSE,
    es_destacado BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS transacciones (
    transaccion_id SERIAL PRIMARY KEY,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_id INT REFERENCES usuarios(usuario_id),
    articulo_id INT REFERENCES articulos(articulo_id),
    cantidad NUMERIC(12, 3) NOT NULL,
    tipo_movimiento VARCHAR(20),
    coste_total NUMERIC(12, 2)
);

INSERT INTO articulos
    (nombre, descripcion, estado, categoria, unidad_medida, precio_unitario, url_imagen, talla, es_drop, es_destacado)
VALUES
    (
        'Camiseta vintage negra',
        'Camiseta negra oversize con corte vintage.',
        'nuevo',
        'camisetas',
        'ud',
        24.99,
        '/images/camiseta-vintage-negra.png',
        'L',
        FALSE,
        TRUE
    ),
    (
        'Camiseta streetwear blanca',
        'Camiseta blanca de algodon con estilo urbano.',
        'nuevo',
        'camisetas',
        'ud',
        22.50,
        '/images/camiseta-streetwear-blanca.png',
        'M',
        TRUE,
        FALSE
    ),
    (
        'Camiseta retro azul',
        'Camiseta azul con inspiracion retro y fit relajado.',
        'segunda mano',
        'camisetas',
        'ud',
        18.00,
        '/images/camiseta-retro-azul.png',
        'S',
        FALSE,
        FALSE
    ),
    (
        'Camiseta grafica roja',
        'Camiseta roja con estampado grafico frontal.',
        'nuevo',
        'camisetas',
        'ud',
        27.99,
        '/images/camiseta-grafica-roja.png',
        'XL',
        TRUE,
        FALSE
    )
ON CONFLICT DO NOTHING;
