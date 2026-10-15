# Informe de Seguridad — NezaMateriales

Fecha: 2026-09-01
Alcance revisado: `frontend/`, `backend/` (FastAPI + SQLAlchemy), `database/schema.sql`, `firebase.json`/`.firebaserc`, `.env.example`, `.gitignore`, `tests/`.

Contexto importante: hoy el sitio publicado en Firebase Hosting es **100% estático** (`frontend/js/api.js` tiene `USE_REMOTE_API = false`), es decir, el backend FastAPI **no está conectado** al sitio en producción. Los hallazgos marcados con 🔌 solo son explotables el día que se active `USE_REMOTE_API` o se despliegue `backend/` en algún servidor. Se incluyen igual porque conviene corregirlos *antes* de conectar el backend, no después.

---

## 🔴 Críticos

### 1. Manipulación de precios (price tampering) 🔌
**Dónde:** `backend/app/routers/quotes.py:28-37`, `backend/app/schemas/quotes.py:11-14`

El endpoint `POST /api/quotes` calcula el subtotal con el `unit_price` que manda el propio cliente en el JSON, sin comparar contra el precio real del producto en la tabla `products`:

```python
subtotal = Decimal(str(item_in.quantity)) * Decimal(str(item_in.unit_price))
```

Cualquier persona con `curl` puede mandar `unit_price: 0.01` para un cemento de $235 y el pedido se guarda tal cual, sin ninguna validación.

**Solución:** ignorar `unit_price` del request. En el backend, buscar el producto por `product_id` en la BD y usar `product.price` como fuente de verdad para calcular subtotal y total. Si el producto no existe, rechazar con 404.

### 2. IDOR — lectura de cotizaciones ajenas 🔌
**Dónde:** `backend/app/routers/quotes.py:115-141`

`GET /api/quotes/{quote_id}` no verifica quién hace la petición. Los IDs son autoincrementales (1, 2, 3…), así que cualquiera puede recorrerlos y leer nombre, teléfono y dirección de **todos los clientes** que hayan cotizado.

**Solución:** como no hay sistema de cuentas, lo mínimo viable es devolver un token/folio no adivinable (UUID) en vez del ID numérico y exigirlo para consultar la cotización, en vez de exponer el ID secuencial. Si en el futuro hay login de clientes, restringir por dueño del pedido.

---

## 🟠 Altos

### 3. CORS abierto a cualquier origen 🔌
**Dónde:** `backend/main.py:28-34`

```python
allow_origins=["*"],
allow_credentials=True,
```

Permite que **cualquier sitio web** (no solo el tuyo) llame a tu API desde el navegador de un visitante. Además, `allow_origins="*"` junto con `allow_credentials=True` es una combinación inválida según la spec de CORS (los navegadores la rechazan o exponen datos si algún día se agregan cookies/sesión).

**Solución:** restringir `allow_origins` a la lista real de dominios del sitio (ej. `https://neza-materiales-2026.web.app`, tu dominio propio) y quitar `allow_credentials` si no usas cookies/sesión.

### 4. Sin límite de peticiones (rate limiting) ni CAPTCHA 🔌
**Dónde:** todos los endpoints de `backend/app/routers/`

`POST /api/quotes` no tiene ningún control de abuso. Un script puede generar miles de cotizaciones falsas por minuto, saturando la base de datos y tu buzón de pedidos.

**Solución:** agregar un middleware de rate limiting (ej. `slowapi`) por IP, y considerar un captcha simple (hCaptcha/Turnstile) en el formulario público antes de conectar el backend real.

### 5. Los errores se ocultan y se responde "éxito" falso 🔌
**Dónde:** `backend/app/routers/quotes.py:90-112`

```python
except Exception as e:
    db.rollback()
    ...
    return QuoteOut(id=fake_id, ...)  # responde 201 como si se hubiera guardado
```

Cualquier excepción —desde un error de conexión a MySQL hasta un intento de ataque que rompa una query— se traga en silencio y el cliente recibe una respuesta de "pedido creado" con un ID inventado que **no existe en la base de datos**. Esto es grave por dos razones: (a) pedidos reales se pierden sin que nadie se entere, y (b) no queda ningún rastro para detectar que alguien está atacando el endpoint.

**Solución:** no simular una respuesta exitosa cuando falla el guardado. Responder un error 500/503 real, y registrar la excepción con `logging` (incluyendo traceback) para poder auditar después.

---

## 🟡 Medios

### 6. Credenciales de BD con valores por defecto inseguros 🔌
**Dónde:** `backend/app/database.py:20-21`

```python
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
```

Si por error se despliega sin `.env`, la app intenta conectar como `root` con contraseña vacía en vez de fallar de forma clara.

**Solución:** quitar los defaults para `DB_USER`/`DB_PASSWORD` y lanzar un error explícito al arrancar si no están definidos.

### 7. Sin headers de seguridad HTTP
**Dónde:** `backend/main.py` (no hay middleware de headers) y `firebase.json` (no define `headers` de seguridad más allá de cache-control)

Falta `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy` y `Strict-Transport-Security`.

**Solución:** agregar un bloque `headers` en `firebase.json` para estos valores en `**/*.html`, y un middleware equivalente en FastAPI si el backend se expone directamente.

### 8. Cero logging/auditoría
Todos los `except Exception: pass` (en `products.py` y `quotes.py`) descartan el error sin registrar nada. No hay forma de saber, después de un incidente, qué pasó.

**Solución:** usar el módulo `logging` de Python para registrar cualquier excepción atrapada (nivel `warning`/`error`), incluso si se decide devolver un fallback al usuario.

### 9. Campos de texto libre sin sanitizar (riesgo futuro de XSS almacenado) 🔌
**Dónde:** `backend/app/schemas/quotes.py` (`delivery_method`, `description`, `delivery_address` sin `max_length` ni validación de formato)

Hoy el frontend muestra estos campos con `innerText` (seguro), pero si en el futuro se construye un panel de administración que los renderice con `innerHTML`, un cliente podría guardar `<script>` en su dirección de entrega y ejecutarse en el navegador de quien administre los pedidos.

**Solución:** limitar longitud (`max_length`) y, sobre todo, cuando se muestre este texto en cualquier panel nuevo, usar `textContent`/`innerText` o una librería de sanitización — nunca `innerHTML` con datos de usuario.

### 10. Dependencias sin versión fija ni auditoría
**Dónde:** `requirements.txt`

Rangos abiertos (`fastapi>=0.110,<1.0`, etc.) sin lockfile — no es reproducible y no hay proceso para detectar CVEs en las versiones instaladas.

**Solución:** generar un lockfile (`pip freeze` a `requirements.lock.txt` o usar `poetry`/`pip-tools`) y correr `pip-audit` periódicamente. El frontend ya está en buena forma en este punto: no tiene dependencias npm (`package.json` sin `dependencies`), lo cual reduce mucho el riesgo de cadena de suministro.

---

## 🟢 Bajos / buenas prácticas a reforzar

- **Carrito en `localStorage`** (`frontend/js/cart.js`): el usuario puede editar precios en su propio navegador vía DevTools antes de "confirmar pedido". Hoy el impacto es bajo porque el pedido final se negocia por WhatsApp con revisión humana y no hay cobro automático. Si algún día se conecta un pago en línea, el precio **debe** recalcularse en servidor (ver hallazgo #1) y nunca confiar en lo que llega del cliente.
- **Sin CSRF**: no aplica hoy porque no hay cookies de sesión; si se agrega login, revisar en ese momento.
- Revisé el repo completo buscando llaves/API keys/contraseñas hardcodeadas (`grep` de patrones típicos) y no encontré ninguna. `.env` está correctamente en `.gitignore` y no hay archivo `.env` real en el repositorio.

---

## Lo que ya está bien hecho (para contexto)

- Uso consistente de **SQLAlchemy ORM** con queries parametrizadas — no hay concatenación de SQL, por lo que **no hay inyección SQL** en el código revisado.
- **Pydantic** valida tipos y rangos en las entradas (`gt=0`, `min_length`, etc.), lo que bloquea buena parte de payloads malformados antes de llegar a la base de datos.
- `.env` está en `.gitignore` y no hay secretos filtrados en el repo.
- El sitio en Firebase Hosting sirve todo por HTTPS automáticamente y ya tiene `Cache-Control` diferenciado para imágenes/JS/CSS.
- El frontend no tiene dependencias de npm, lo que reduce mucho el riesgo de un ataque de cadena de suministro (paquete malicioso en `node_modules`).

---

## Prioridad recomendada si en algún momento conectas el backend

1. Arreglar #1 (precio) y #2 (IDOR) — son los únicos que exponen datos de clientes o permiten fraude directo.
2. Cerrar CORS (#3) y agregar logging real (#5, #8) antes de exponer el backend a internet.
3. Rate limiting (#4) y headers de seguridad (#7) antes de anunciar la API públicamente.
4. El resto (#6, #9, #10) son mejoras de higiene que no urgen pero conviene resolver junto con lo anterior, ya que son cambios pequeños.
