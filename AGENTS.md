# NezaMateriales

Plataforma web para la compra, cotización y cálculo automatizado de materiales de construcción, optimizada para clientes y obra civil en el municipio de Nezahualcóyotl.

## Stack
- Lenguaje: Python 3.11+ (Backend) y JavaScript ES6+ (Frontend)
- Framework / runtime: FastAPI (Backend API) + HTML5/JS ES Modules (Frontend)
- Base de datos: MySQL 8.0 con SQLAlchemy ORM y Alembic para migraciones
- Tests: Pytest (Python) y Jest (JavaScript)

## Comandos
- `uvicorn backend.main:app --reload` — arranca el servidor API backend en modo desarrollo local
- `npm run dev` — arranca el servidor local de archivos estáticos y frontend
- `pytest && npm test` — ejecuta las pruebas backend y frontend (deben pasar antes de cada commit)
- `flake8 backend/ && npx eslint frontend/` — revisa el estilo del código en Python y JavaScript
- `docker-compose up --build` — empaquetado y arranque del contenedor completo para producción

## Estructura del proyecto
- `backend/` — API REST en Python (rutas de productos, carritos, algoritmo de cotización y motor de cálculo de rendimiento)
- `frontend/` — Interfaz pública en JS/HTML/CSS (catálogo, vistas dinámicas del carrito y la calculadora de materiales)
- `database/` — Esquemas SQL iniciales de MySQL, semillas de precios locales y scripts de migración de datos
- `tests/` — Pruebas unitarias e integración del flujo de cotización, persistencia en MySQL y fórmulas constructivas

## Convenciones
- Estilo de nombres: `snake_case` para variables, funciones y archivos en Python; `camelCase` para JS; `PascalCase` para clases y componentes.
- Ubicación de tests: Centralizados en la carpeta `tests/` divididos por módulo (`test_calculator.py`, `test_cart.js`).
- Manejo de errores: Excepciones personalizadas en `backend/app/errors.py` que retornen JSON consistente (`{ "status": "error", "message": "string" }`).
- Patrón a seguir: Validar y desinfectar toda entrada del usuario (medidas de obra, entradas del carrito) con Pydantic antes de procesarla o consultar MySQL.

## No hagas
- Límite duro: No realizar consultas SQL directamente mediante concatenación de texto; utilizar ORM o consultas preparadas para evitar inyección SQL.
- Zona prohibida: No subir credenciales de MySQL ni llaves de entorno al repositorio; mantener la configuración en `.env` (incluido en `.gitignore`).
- Regla de seguridad: No modificar las fórmulas matemáticas de cálculo de rendimiento de materiales sin previa confirmación de parámetros técnicos de construcción.
- Antipatrón: No agregar dependencias de Python (`requirements.txt`) o JavaScript (`package.json`) sin justificar su necesidad.

## Flujo de trabajo
- Antes de una tarea no trivial, propón un plan y espera mi OK.
- Una tarea a la vez; al terminar, dime qué cambiaste para que lo revise.
- Si no estás seguro al 80%, pregunta. No inventes.

## Documentación
- Tablas de rendimiento de materiales por m² y m³ específicas para muros, losas y cimentaciones.
- Guía de arquitectura de API REST para la calculadora de insumos y carrito de compras.
- Configuración del túnel o servidor para exponer la URL pública de la aplicación en red externa.