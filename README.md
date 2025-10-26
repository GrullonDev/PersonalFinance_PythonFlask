# Personal Finance API

Servicio backend en FastAPI para gestionar finanzas personales (perfiles, categorías, transacciones, presupuestos y metas) autenticado mediante Firebase.

## Stack principal

- Python 3.11
- FastAPI + Pydantic v2
- SQLAlchemy 2.0 (ORM sincrono)
- Firebase Admin SDK
- SQLite por defecto (configurable para PostgreSQL)

## Requisitos

- Python ≥ 3.11
- Cuenta de servicio de Firebase (archivo JSON)
- Opcional: Docker

## Configuración local

1. Clonar el repositorio y crear entorno virtual:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

2. Instalar dependencias (añade las de desarrollo si vas a ejecutar pruebas):

   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. Crear un archivo `.env` basado en `.env.example` y ajustar valores:

   - `DATABASE_URL`: `sqlite:///./personal_finance.db` para desarrollo o URL de PostgreSQL (`postgresql+psycopg://user:pass@host:5432/db`).
   - `FIREBASE_CREDENTIALS_PATH`: ruta absoluta al JSON del service account.
   - `ALLOW_TEST_TOKENS=true` permite usar tokens ficticios (el valor del token se toma como UID) cuando no haya credenciales válidas. Desactívalo en producción.

4. Ejecutar las migraciones (en entornos no productivos la aplicación las ejecuta automáticamente al iniciar, pero es útil correrlas manualmente en scripting o CI/CD):

   ```bash
   alembic upgrade head
   ```

5. Ejecutar el servidor:

   ```bash
   uvicorn app.main:app --reload
   ```

6. Endpoints disponibles en `http://localhost:8000/api/v1/`. La documentación interactiva (`/docs`) se expone únicamente fuera de producción.

## Docker

```bash
docker build -t personal-finance-api .
docker run --rm -p 8000:8000 --env-file .env personal-finance-api
```

## Autenticación

- Cada petición debe incluir `Authorization: Bearer <token Firebase>`.
- Se validan los tokens mediante Firebase Admin. En desarrollo se puede habilitar `ALLOW_TEST_TOKENS=true` para omitir la verificación (se crea un perfil automático con el UID indicado).
- También están disponibles endpoints de autenticación local (contraseña hasheada con `bcrypt`):
  - `POST /api/v1/auth/register`: registra nombres, apellidos, fecha de nacimiento, usuario, email y contraseña (con doble confirmación) y devuelve la ficha del usuario creado.
  - `POST /api/v1/auth/login`: acepta usuario o email más contraseña y retorna la información del usuario.
  - `POST /api/v1/auth/recover-password`: genera un token de recuperación (almacenado en base de datos) usando usuario o email sin revelar si la cuenta existe.
  - Recuerda ejecutar las migraciones (`alembic upgrade head`) para crear las tablas `local_credentials` y `password_reset_tokens`.
  - Para ejecutar los endpoints locales es necesario instalar la dependencia `passlib[bcrypt]` incluida en `requirements.txt`.
  - Configura un servicio SMTP si deseas enviar correos reales (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, `EMAIL_SENDER`) y, opcionalmente, la URL base que consume el frontend (`PASSWORD_RESET_URL`). Si no se configuran, la app registrará en logs el token de recuperación.

## Pruebas automatizadas

```bash
pytest
```

Las pruebas usan SQLite y crean una base de datos temporal (`test_personal_finance.db`). Asegúrate de exportar `ALLOW_TEST_TOKENS=true` y `ENVIRONMENT=test` si lanzas los tests fuera del entorno provisto.

## CI/CD

El pipeline de GitHub Actions (`.github/workflows/ci.yml`) instala dependencias, aplica migraciones con Alembic y ejecuta `pytest` en cada push a `main`/`develop` y en los pull requests.

## Próximos pasos sugeridos

- Automatizar despliegues a los entornos objetivo tras la validación del pipeline.
- Definir límites de cuota y monitorización (OpenTelemetry, Prometheus, Sentry).
- Incorporar pruebas de integración/end-to-end con datos más realistas.
