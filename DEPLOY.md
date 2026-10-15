# Despliegue de NezaMateriales — Cloud Run + Cloud SQL + Firebase Hosting

Documento de referencia con los comandos exactos para desplegar de verdad.
**Ninguno de estos comandos se ha ejecutado todavía** — créditos de GCP,
provisión de infraestructura y cambios en producción requieren tu OK explícito
en el momento de correrlos.

Proyecto GCP/Firebase: `neza-materiales-2026` (ver `.firebaserc`).
Región usada en todo el documento: `us-central1` (ajústala si prefieres otra).

## 0. Requisitos previos

```bash
gcloud auth login
gcloud config set project neza-materiales-2026
gcloud services enable run.googleapis.com sqladmin.googleapis.com \
  artifactregistry.googleapis.com secretmanager.googleapis.com \
  cloudbuild.googleapis.com
```

## 1. Base de datos — Cloud SQL para MySQL 8.0

```bash
# Crear la instancia (nivel más económico: db-f1-micro; súbelo si esperas más tráfico)
gcloud sql instances create neza-mysql \
  --database-version=MYSQL_8_0 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --root-password=ELIGE_UNA_PASSWORD_FUERTE

# Crear la base de datos y el usuario de la aplicación (no uses root en runtime)
gcloud sql databases create neza_materiales --instance=neza-mysql
gcloud sql users create neza_app --instance=neza-mysql --password=OTRA_PASSWORD_FUERTE

# Cargar el esquema + semillas (requiere el cliente `mysql` y el Cloud SQL Auth Proxy,
# o usar Cloud Shell que ya lo trae instalado)
gcloud sql connect neza-mysql --user=root < database/schema.sql

# Anotar el "connection name" para Cloud Run:
gcloud sql instances describe neza-mysql --format='value(connectionName)'
# → algo como: neza-materiales-2026:us-central1:neza-mysql
```

Después de cargar `schema.sql`, marca el baseline de Alembic (desde tu máquina,
apuntando a esta instancia vía Cloud SQL Auth Proxy o IP pública temporal):

```bash
alembic stamp head
```

## 2. Secretos (Secret Manager)

```bash
printf 'OTRA_PASSWORD_FUERTE' | gcloud secrets create db-password --data-file=-
printf 'TU_WHATSAPP_APP_SECRET' | gcloud secrets create whatsapp-app-secret --data-file=-
printf 'TU_WHATSAPP_ACCESS_TOKEN' | gcloud secrets create whatsapp-access-token --data-file=-
```

## 3. Construir y subir la imagen del backend

```bash
gcloud artifacts repositories create neza \
  --repository-format=docker --location=us-central1

gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_IMAGE=us-central1-docker.pkg.dev/neza-materiales-2026/neza/neza-backend-api
```

## 4. Desplegar a Cloud Run

```bash
gcloud run deploy neza-backend-api \
  --image=us-central1-docker.pkg.dev/neza-materiales-2026/neza/neza-backend-api \
  --region=us-central1 \
  --platform=managed \
  --no-allow-unauthenticated=false \
  --add-cloudsql-instances=neza-materiales-2026:us-central1:neza-mysql \
  --set-env-vars="APP_ENV=production,DB_USER=neza_app,DB_NAME=neza_materiales,INSTANCE_UNIX_SOCKET=/cloudsql/neza-materiales-2026:us-central1:neza-mysql,ALLOWED_ORIGINS=https://neza-materiales-2026.web.app,https://neza-materiales-2026.firebaseapp.com,WHATSAPP_VERIFY_TOKEN=elige_un_token,WHATSAPP_PHONE_NUMBER_ID=tu_phone_number_id" \
  --set-secrets="DB_PASSWORD=db-password:latest,WHATSAPP_APP_SECRET=whatsapp-app-secret:latest,WHATSAPP_ACCESS_TOKEN=whatsapp-access-token:latest"
```

Nota: el servicio debe permitir invocaciones no autenticadas (`--allow-unauthenticated`)
porque tanto el navegador (vía el rewrite de Firebase) como Meta (webhook) le
llegan sin credenciales de GCP.

```bash
gcloud run services add-iam-policy-binding neza-backend-api \
  --region=us-central1 --member="allUsers" --role="roles/run.invoker"
```

## 5. Conectar el rewrite de Firebase Hosting

`firebase.json` ya tiene el rewrite `/api/** -> run(neza-backend-api, us-central1)`
(ver este repo). Solo falta desplegar hosting:

```bash
firebase deploy --only hosting --project neza-materiales-2026
```

A partir de aquí, `https://neza-materiales-2026.web.app/api/*` llega al backend
en Cloud Run como si fuera el mismo origen (sin problemas de CORS).

## 6. Conectar el bot de WhatsApp (Meta Cloud API)

1. En [Meta for Developers](https://developers.facebook.com/), crea/usa tu app
   con el producto WhatsApp habilitado.
2. Copia `Phone Number ID` y genera un token de acceso permanente (System User)
   → actualiza el secreto `whatsapp-access-token` y el env var `WHATSAPP_PHONE_NUMBER_ID`.
3. Copia el `App Secret` → actualiza el secreto `whatsapp-app-secret`.
4. En la configuración del webhook, pon:
   - URL: `https://neza-materiales-2026.web.app/api/whatsapp/webhook`
   - Verify token: el mismo valor que pusiste en `WHATSAPP_VERIFY_TOKEN`.
   - Suscríbete al campo `messages`.
5. Manda un mensaje de prueba al número de WhatsApp Business y confirma que
   el bot responde y que la cotización queda en `SELECT * FROM quotes` de Cloud SQL.

## 7. Futuras actualizaciones

```bash
# Nuevo build + deploy del backend tras cambios de código
gcloud builds submit --config cloudbuild.yaml --substitutions=_IMAGE=...
gcloud run deploy neza-backend-api --image=... --region=us-central1

# Nueva migración de esquema
alembic revision --autogenerate -m "descripcion"
alembic upgrade head   # contra la instancia real, vía Cloud SQL Auth Proxy

# Nuevo despliegue del frontend
firebase deploy --only hosting --project neza-materiales-2026
```
