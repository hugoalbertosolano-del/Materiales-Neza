# NezaMateriales

Plataforma web Full Stack para la venta y gestión de materiales de construcción, diseñada para optimizar los procesos comerciales a nivel local en Ciudad Nezahualcóyotl.

## Descripción del Proyecto

NezaMateriales es un sistema e-commerce integral que permite la visualización, selección y gestión de inventario de materiales de construcción. La aplicación está diseñada con una arquitectura cliente-servidor que garantiza un rendimiento eficiente, seguridad en el manejo de datos y una experiencia de usuario fluida.

## Arquitectura y Tecnologías

El proyecto fue desarrollado utilizando las siguientes tecnologías:

*   **Backend:** FastAPI (Python)
*   **Base de Datos:** MySQL
*   **Frontend:** JavaScript, HTML5, CSS3
*   **Despliegue y Hosting:** Firebase Hosting

## Características Principales

*   **API RESTful:** Desarrollo de endpoints eficientes con FastAPI para la comunicación entre el cliente y el servidor.
*   **Gestión de Datos:** Diseño e implementación de esquemas relacionales en MySQL para el control de inventario y transacciones.
*   **Interfaz de Usuario:** Interfaz responsiva y dinámica construida con JavaScript puro para un rendimiento óptimo.
*   **Despliegue en la Nube:** Configuración y publicación del entorno de producción utilizando Firebase Hosting.

## Instalación y Configuración Local

Para ejecutar este proyecto en un entorno local, sigue los siguientes pasos:

1. Clona este repositorio:
   git clone https://github.com/[TuUsuario]/[NombreDelRepo].git

2. Configura el entorno virtual e instala las dependencias del backend:
   pip install -r requirements.txt

3. Configura las credenciales de la base de datos MySQL en el archivo de entorno (.env).

4. Inicia el servidor de desarrollo de FastAPI:
   uvicorn main:app --reload

## Estado del Proyecto

Versión inicial - Desplegado en producción.
