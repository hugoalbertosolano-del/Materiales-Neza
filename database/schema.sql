-- ==========================================================================
-- NezaMateriales — Esquema DDL para MySQL 8.0
-- ==========================================================================
-- Ejecutar con:
--   mysql -u root -p < database/schema.sql
-- ==========================================================================

CREATE DATABASE IF NOT EXISTS neza_materiales
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE neza_materiales;

-- --------------------------------------------------------------------------
-- Tabla: products — Catálogo de materiales de construcción
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(200)    NOT NULL,
    description TEXT            NULL,
    unit        VARCHAR(20)     NOT NULL COMMENT 'pza, bulto, m³, kg, varilla',
    price       DECIMAL(10, 2)  NOT NULL COMMENT 'Precio unitario en MXN',
    category    VARCHAR(100)    NULL,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_products_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- --------------------------------------------------------------------------
-- Tabla: quotes — Cotizaciones generadas
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS quotes (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    folio             CHAR(36)        NOT NULL COMMENT 'UUID público no adivinable; usar en vez de id en URLs/API',
    client_name       VARCHAR(200)    NOT NULL,
    client_phone      VARCHAR(30)     NULL,
    delivery_method   VARCHAR(30)     NULL,
    delivery_address  VARCHAR(500)    NULL,
    description       TEXT            NULL,
    total             DECIMAL(12, 2)  NOT NULL DEFAULT 0.00,
    created_at        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uq_quotes_folio (folio),
    INDEX idx_quotes_client_phone (client_phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- --------------------------------------------------------------------------
-- Tabla: whatsapp_sessions — estado del bot conversacional por número
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS whatsapp_sessions (
    phone_number  VARCHAR(30)   PRIMARY KEY,
    state         VARCHAR(50)   NOT NULL DEFAULT 'menu',
    context       TEXT          NULL COMMENT 'JSON con datos parciales del flujo actual',
    updated_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- --------------------------------------------------------------------------
-- Tabla: quote_items — Ítems individuales de una cotización
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS quote_items (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    quote_id    INT             NOT NULL,
    product_id  INT             NOT NULL,
    quantity    DECIMAL(10, 4)  NOT NULL,
    unit_price  DECIMAL(10, 2)  NOT NULL,
    subtotal    DECIMAL(12, 2)  NOT NULL,

    CONSTRAINT fk_quote_items_quote
        FOREIGN KEY (quote_id)  REFERENCES quotes(id)   ON DELETE CASCADE,
    CONSTRAINT fk_quote_items_product
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT,

    INDEX idx_quote_items_quote (quote_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ==========================================================================
-- SEMILLAS — 5 productos reales, precios orientativos zona Nezahualcóyotl
-- ==========================================================================
INSERT INTO products (name, description, unit, price, category) VALUES
(
    'Cemento Tolteca 50 kg',
    'Cemento Portland Compuesto CPC 30R, bulto de 50 kg. Uso general en obra civil.',
    'bulto',
    235.00,
    'Cementantes'
),
(
    'Tabique rojo 6×12×24 cm',
    'Tabique rojo recocido estándar para muros, medidas nominales 6×12×24 cm.',
    'pieza',
    3.50,
    'Mampostería'
),
(
    'Varilla corrugada 3/8" (9.5 mm)',
    'Varilla de acero corrugado grado 42, diámetro 3/8" (9.5 mm), longitud 12 m.',
    'pieza',
    125.00,
    'Acero'
),
(
    'Arena de río',
    'Arena de río cribada, granulometría estándar para morteros y concretos. Precio por metro cúbico.',
    'm³',
    650.00,
    'Agregados'
),
(
    'Grava triturada 3/4"',
    'Grava triturada tamaño máximo 3/4" (19 mm) para concreto estructural. Precio por metro cúbico.',
    'm³',
    750.00,
    'Agregados'
),
(
    'Mortero Premezclado 25 kg',
    'Mortero cementante premezclado listo para usar, bulto de 25 kg. Ideal para reparaciones, resanes y aplanados menores.',
    'bulto',
    95.00,
    'Cementantes'
),
(
    'Block hueco de concreto 15×20×40 cm',
    'Block de concreto estándar para muros de carga, bardas y cubos de escalera.',
    'pieza',
    14.50,
    'Mampostería'
),
(
    'Adoquín de concreto tipo tráfico',
    'Adoquín de concreto vibroprensado para pisos, andadores y cocheras.',
    'pieza',
    8.50,
    'Mampostería'
),
(
    'Varilla corrugada 1/2" (12.7 mm)',
    'Varilla de acero grado 42 tramo de 12 metros, para columnas, trabes y losas estructurales.',
    'pieza',
    210.00,
    'Acero'
),
(
    'Malla electrosoldada 6×6-10/10',
    'Malla de refuerzo electrosoldada en hoja de 6×2.35 m para losas de piso y firmes de concreto.',
    'hoja',
    680.00,
    'Acero'
),
(
    'Pintura vinílica 19 L',
    'Pintura vinílica lavable para interior y exterior, cubeta de 19 litros.',
    'cubeta',
    780.00,
    'Acabados'
),
(
    'Impermeabilizante acrílico 19 L',
    'Recubrimiento acrílico elastomérico para azoteas y losas, cubeta de 19 litros, garantía de 5 años.',
    'cubeta',
    890.00,
    'Impermeabilizantes'
),
(
    'Tubo PVC hidráulico 4" cédula 40',
    'Tubo de PVC hidráulico para agua fría a presión, tramo de 6 metros.',
    'tramo',
    320.00,
    'Plomería'
),
(
    'Conexión de cobre 1/2" (coples)',
    'Conexión roscada de cobre tipo M para instalaciones hidráulicas.',
    'pieza',
    45.00,
    'Plomería'
),
(
    'Cable eléctrico THW cal. 12 (rollo 100 m)',
    'Cable de cobre THW calibre 12 AWG, 600V, rollo de 100 metros para circuitos derivados.',
    'rollo',
    890.00,
    'Eléctrico'
),
(
    'Carretilla de obra 6 pies³',
    'Carretilla metálica de uso rudo, capacidad de 6 pies³ (170 litros), para acarreo de mezcla y escombro.',
    'pieza',
    890.00,
    'Herramientas'
),
(
    'Cuchara de albañil 8"',
    'Cuchara/llana de albañil de acero templado de 8 pulgadas, para pega de tabique/block y aplanados.',
    'pieza',
    145.00,
    'Herramientas'
),
(
    'Pala recta de punta',
    'Pala recta de punta con cabo de madera, uso rudo para excavación y mezclado manual.',
    'pieza',
    210.00,
    'Herramientas'
);
