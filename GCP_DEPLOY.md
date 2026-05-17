# Guía de despliegue en GCP — Retro&Street

Arquitectura objetivo en GCP:

```
Internet
   │
   ├── Cloud Run (frontend Nginx) ──► Cloud Run (backend FastAPI)
   │                                        │
   │                                   Cloud SQL (PostgreSQL 15)
   │                                        │
   └──────────────────────────── Secret Manager (credenciales)
```

Servicios utilizados: **Cloud Run · Cloud SQL · Artifact Registry · Secret Manager**

---

## Requisitos previos

- [gcloud CLI](https://cloud.google.com/sdk/docs/install) instalado y autenticado
- Docker instalado
- Proyecto GCP creado

```bash
gcloud auth login
gcloud auth configure-docker   # configura Docker para usar GCP
```

---

## 0. Variables de entorno del despliegue

Define estas variables en tu terminal antes de ejecutar los comandos. Sustitúyelas por tus valores reales.

```bash
export PROJECT_ID="tu-project-id"
export REGION="europe-west1"
export REPO="retro-street"                          # nombre del repositorio en Artifact Registry
export SQL_INSTANCE="retro-street-db"               # nombre de la instancia Cloud SQL
export DB_NAME="tienda"
export DB_USER="retro_user"
export BACKEND_SERVICE="retro-street-backend"
export FRONTEND_SERVICE="retro-street-frontend"

# Imagen completa en Artifact Registry
export BACKEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/backend"
export FRONTEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/frontend"

# Connection name de Cloud SQL (se obtiene en el paso 3)
export SQL_CONNECTION="${PROJECT_ID}:${REGION}:${SQL_INSTANCE}"
```

---

## 1. Activar APIs de GCP

```bash
gcloud config set project $PROJECT_ID

gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com
```

---

## 2. Crear repositorio en Artifact Registry

```bash
gcloud artifacts repositories create $REPO \
  --repository-format=docker \
  --location=$REGION \
  --description="Imágenes Docker de Retro&Street"

# Configurar Docker para este registro
gcloud auth configure-docker ${REGION}-docker.pkg.dev
```

---

## 3. Crear instancia Cloud SQL (PostgreSQL 15)

> Tarda entre 3 y 5 minutos.

```bash
gcloud sql instances create $SQL_INSTANCE \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=$REGION \
  --storage-type=SSD \
  --storage-size=10GB \
  --backup-start-time=03:00

# Crear la base de datos
gcloud sql databases create $DB_NAME --instance=$SQL_INSTANCE

# Crear el usuario de la aplicación
gcloud sql users create $DB_USER \
  --instance=$SQL_INSTANCE \
  --password="CAMBIA_ESTA_PASSWORD"
```

### 3.1 Cargar el esquema inicial

```bash
# Opción A: desde Cloud Shell (recomendado si no tienes IP pública en la instancia)
gcloud sql connect $SQL_INSTANCE --user=$DB_USER --database=$DB_NAME < init-db/01-schema.sql

# Opción B: usando Cloud SQL Auth Proxy en local
#   1. Descarga el proxy: https://cloud.google.com/sql/docs/postgres/sql-proxy
#   2. Ejecútalo:
#      ./cloud-sql-proxy ${SQL_CONNECTION} &
#   3. Conéctate:
#      psql -h 127.0.0.1 -U $DB_USER -d $DB_NAME < init-db/01-schema.sql
```

---

## 4. Configurar Secret Manager

Almacena los secretos de la aplicación en Secret Manager en lugar de variables de entorno planas.

```bash
# Contraseña de la base de datos
echo -n "CAMBIA_ESTA_PASSWORD" | \
  gcloud secrets create DB_PASSWORD --data-file=- --replication-policy=automatic

# Clave secreta JWT (genera una aleatoria)
python3 -c "import secrets; print(secrets.token_hex(32))" | \
  gcloud secrets create SECRET_KEY --data-file=- --replication-policy=automatic
```

### 4.1 Dar permisos al service account de Cloud Run

```bash
# Obtener el service account por defecto de Cloud Run
export SA="${PROJECT_ID}@appspot.gserviceaccount.com"
# O si usas el SA de Compute Engine por defecto:
# export SA="$(gcloud iam service-accounts list --filter='displayName:Compute Engine' --format='value(email)')"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA}" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA}" \
  --role="roles/cloudsql.client"
```

---

## 5. Construir y publicar las imágenes Docker

### 5.1 Backend (FastAPI)

```bash
cd server

docker build -t ${BACKEND_IMAGE}:latest .
docker push ${BACKEND_IMAGE}:latest

cd ..
```

### 5.2 Frontend (React + Nginx)

La URL del backend se inyecta en tiempo de build mediante `VITE_API_URL`.
Sustitúyela por la URL de Cloud Run del backend **después de desplegarlo** (paso 6),
o usa un dominio personalizado si ya lo tienes configurado.

```bash
cd frontend

# Si ya tienes la URL del backend (obtenida en el paso 6):
BACKEND_URL="https://retro-street-backend-XXXX-ew.a.run.app"

docker build \
  --build-arg VITE_API_URL=${BACKEND_URL} \
  -t ${FRONTEND_IMAGE}:latest .
docker push ${FRONTEND_IMAGE}:latest

cd ..
```

> Si aún no tienes la URL del backend, despliega primero el backend (paso 6),
> copia la URL y vuelve aquí para construir el frontend.

---

## 6. Desplegar el backend en Cloud Run

```bash
gcloud run deploy $BACKEND_SERVICE \
  --image=${BACKEND_IMAGE}:latest \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --add-cloudsql-instances=${SQL_CONNECTION} \
  --set-env-vars="DB_HOST=/cloudsql/${SQL_CONNECTION},DB_NAME=${DB_NAME},DB_USER=${DB_USER},DB_PORT=5432" \
  --set-secrets="DB_PASSWORD=DB_PASSWORD:latest,SECRET_KEY=SECRET_KEY:latest" \
  --min-instances=0 \
  --max-instances=5 \
  --memory=512Mi \
  --port=8000
```

Anota la URL que devuelve el comando (la necesitas para el paso 5.2 y para el CORS):

```bash
export BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE \
  --platform=managed --region=$REGION \
  --format='value(status.url)')
echo "Backend URL: $BACKEND_URL"
```

---

## 7. Desplegar el frontend en Cloud Run

Primero construye la imagen con la URL real del backend (paso 5.2) y luego despliega:

```bash
gcloud run deploy $FRONTEND_SERVICE \
  --image=${FRONTEND_IMAGE}:latest \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --min-instances=0 \
  --max-instances=3 \
  --memory=256Mi \
  --port=80
```

Anota la URL del frontend:

```bash
export FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE \
  --platform=managed --region=$REGION \
  --format='value(status.url)')
echo "Frontend URL: $FRONTEND_URL"
```

---

## 8. Actualizar CORS en el backend

Con la URL real del frontend, actualiza el backend para restringir el CORS:

```bash
gcloud run services update $BACKEND_SERVICE \
  --platform=managed \
  --region=$REGION \
  --update-env-vars="CORS_ORIGINS=${FRONTEND_URL}"
```

---

## 9. Verificar el despliegue

```bash
# Health check del backend
curl ${BACKEND_URL}/ping-pong
# Esperado: {"message":"pong"}

# Catálogo de artículos
curl ${BACKEND_URL}/getArticulos

# Abrir el frontend en el navegador
echo "Abre: $FRONTEND_URL"
```

---

## Variables de entorno — resumen

| Variable | Dónde | Valor en producción |
|----------|-------|---------------------|
| `DB_HOST` | Cloud Run backend | `/cloudsql/PROJECT:REGION:INSTANCE` |
| `DB_NAME` | Cloud Run backend | `tienda` |
| `DB_USER` | Cloud Run backend | `retro_user` |
| `DB_PORT` | Cloud Run backend | `5432` |
| `DB_PASSWORD` | Secret Manager | password real |
| `SECRET_KEY` | Secret Manager | token hex aleatorio |
| `CORS_ORIGINS` | Cloud Run backend | URL de Cloud Run frontend |
| `VITE_API_URL` | Build-time frontend | URL de Cloud Run backend |

---

## Troubleshooting

**El backend no conecta con Cloud SQL**
```bash
# Verificar que el SA tiene rol cloudsql.client
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.role:roles/cloudsql.client"

# Ver logs del backend
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=${BACKEND_SERVICE}" \
  --limit=50 --format="table(timestamp,textPayload)"
```

**El frontend muestra pantalla en blanco o errores de red**
- Verificar que `VITE_API_URL` en el build apunta a la URL correcta del backend
- Abrir las DevTools del navegador → Network → ver si hay errores CORS o 404
- Confirmar que `CORS_ORIGINS` en el backend coincide exactamente con la URL del frontend (sin `/` final)

**Error 500 en el backend**
```bash
gcloud run services describe $BACKEND_SERVICE \
  --platform=managed --region=$REGION
# Revisar los logs de Cloud Run en la consola GCP
```

---

## Limpieza (borrar todos los recursos)

```bash
gcloud run services delete $BACKEND_SERVICE --region=$REGION --quiet
gcloud run services delete $FRONTEND_SERVICE --region=$REGION --quiet
gcloud sql instances delete $SQL_INSTANCE --quiet
gcloud artifacts repositories delete $REPO --location=$REGION --quiet
gcloud secrets delete DB_PASSWORD --quiet
gcloud secrets delete SECRET_KEY --quiet
```
