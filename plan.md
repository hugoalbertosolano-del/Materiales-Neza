# Paso 3 — API REST y Frontend Interactivo NezaMateriales
Desarrollo de los endpoints del backend en FastAPI y la interfaz pública en HTML5/JS/CSS según las especificaciones del cliente.

Requerimientos de Diseño y Funcionalidad
1. Paleta de Colores e Identidad Visual
Colores primarios: Tonos de naranja terracota (#e65100, #f57c00), rojo ladrillo (#d32f2f, #b71c1c) y matices cálidos de construcción.
Estilo: Profesional, limpio, organizado y moderno. Dark mode cálido con acentos en fuego/ladrillo y bordes suaves.
2. Estructura de Navegación y Vistas Frontend
Pestaña 1: Inicio y Catálogo por Categorías
Sección Bienvenida: Presentación institucional de NezaMateriales, su presencia en Nezahualcóyotl y oferta de servicio para obra civil y residencial.
Sección Categorías de Materiales: Clasificación limpia (Cementantes, Mampostería, Acero, Agregados).
Modal de Detalle del Material (al seleccionar un producto):
Galería de fotos reales e imágenes promocionales.
Reproductor de video demostrativo/técnico del uso del material en obra.
Descripción técnica detallada.
Ficha de Rendimiento en Obra (ej. bultos requeridos por m³, piezas de tabique por m²).
Precio unitario visible en MXN.
Selector de cantidad deseada con botón "Agregar al Carrito".
Pestaña 2: Calculadora / Cotizador de Obra (IA & Motor Técnico)
Formulario intuitivo donde el usuario ingresa:
Elemento a construir (Muro, Losa/Piso de Concreto).
Medidas de la obra (largo, alto, ancho, espesor).
Resistencia deseada (F'c 150 u 200 kg/cm² para losa) o tipo de junta.
Asistente Inteligente de Estimación: Ejecuta el motor técnico de cálculo de insumos e integra una explicación/resumen automatizado con precios actualizados y desglose exacto de materiales + botón para transferir todos los insumos calculados al carrito.
Pestaña 3: Carrito de Compras y Confirmación de Pedido
Listado de materiales agregados con control de cantidades.
Desglose de subtotal y cálculo de envío.
Selección del Método de Entrega:
🚚 Envío a domicilio en Nezahualcóyotl / Zona Oriente (Flete directo a obra).
🏪 Recolección en Tienda / Almacén Neza.
Formulario de datos de contacto y confirmación con generación de número de folio de pedido.
Archivos Backend y Frontend a Generar/Modificar

backend/
├── main.py                           # [MODIFY] Montaje de rutas, CORS y archivos estáticos
└── app/
    ├── schemas/
    │   ├── products.py               # [NEW] Esquemas Pydantic de productos
    │   └── quotes.py                 # [NEW] Esquemas Pydantic de cotizaciones
    └── routers/
        ├── __init__.py               # [NEW]
        ├── products.py               # [NEW] GET /api/products
        ├── calculator.py             # [NEW] POST /api/calculator/wall y /slab
        └── quotes.py                 # [NEW] POST /api/quotes
frontend/
├── index.html                        # [NEW] Estructura SPA (Inicio, Cotizador, Carrito, Modales)
├── css/
│   └── styles.css                    # [NEW] Tema Naranja/Rojo Cálido, layouts y componentes
└── js/
    ├── api.js                        # [NEW] Cliente Fetch para comunicación con backend
    ├── catalog.js                    # [NEW] Lógica de tarjetas, categorías y modal de detalle
    ├── calculator.js                 # [NEW] Cotizador asistido de obra
    ├── cart.js                       # [NEW] Carrito de compras, métodos de entrega y checkout
    └── app.js                        # [NEW] Inicializador y navegación por pestañas
Generación de Recursos Visuales Demostrativos
Se generarán imágenes fotorrealistas para los productos semilla (cemento, tabique rojo, varilla, arena y grava) mediante la herramienta de generación de imágenes para integrarlas en el modal de detalle del material.

Plan de Verificación
Pruebas backend:
bash

py -3 -m pytest tests/test_calculator.py -v
Pruebas de API REST e interfaz:
Iniciar servidor FastAPI y estáticos.
Probar navegación por pestañas (Inicio -> Cotizador -> Carrito).
Verificar apertura de modal de detalle de producto con fotos/video/rendimiento y precio.
Probar cotización en tiempo real de muro y losa y adición al carrito.
Probar selección de método de entrega (flete Neza / tienda) y checkout.