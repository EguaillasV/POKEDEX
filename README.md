# 🦁 Animal Recognition

Una aplicación web educativa para reconocimiento de animales en tiempo real usando la cámara.
Diseñada para turistas, zoológicos y niños para aprendizaje interactivo.

## 📋 Características

- ✅ Reconocimiento de animales en tiempo real con la cámara
- ✅ Información detallada sobre cada animal detectado
- ✅ Galería de descubrimientos personales
- ✅ Datos sobre estado de conservación
- ✅ Arquitectura hexagonal (Clean Architecture)
- ✅ WebSocket para streaming en tiempo real
- ✅ API REST para acceso a datos

## 🏗️ Arquitectura Hexagonal

```
src/
├── domain/           # 💎 Núcleo del negocio (Entidades, Value Objects, Ports)
├── application/      # 🔄 Casos de uso (Orquestación de lógica)
├── infrastructure/   # 🔌 Adaptadores (DB, ML, Storage)
└── interfaces/       # 🌐 Puertos de entrada (API, WebSocket, Web)
```

## 🚀 Instalación

### Prerrequisitos

- Python 3.10+
- PostgreSQL (opcional, puede usar SQLite para desarrollo)
- Redis (opcional para desarrollo)

### Paso 1: Clonar y configurar entorno

```bash
cd C:\Projects\animal_recognition

# Crear entorno virtual
python -m venv venv

# Activar entorno (Windows)
.\venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 2: Configurar variables de entorno

```bash
# Copiar archivo de ejemplo
copy .env.example .env

# Editar .env con tus configuraciones
```

Para desarrollo rápido sin PostgreSQL/Redis:
```env
DEBUG=True
USE_SQLITE=True
USE_LOCAL_CACHE=True
```

### Paso 3: Ejecutar migraciones

```bash
python manage.py makemigrations src.infrastructure
python manage.py migrate
```

### Paso 4: Cargar datos iniciales

```bash
python scripts/seed_animals.py
```

### Paso 5: Ejecutar servidor

```bash
# Con Daphne (recomendado para WebSocket)
daphne -b 127.0.0.1 -p 8000 config.asgi:application

# O con Django (solo para desarrollo básico)
python manage.py runserver
```

### Paso 6: Abrir en el navegador

```
http://127.0.0.1:8000
```

## 📡 API Endpoints

### Animales
- `GET /api/animals/` - Listar todos los animales
- `GET /api/animals/<id>/` - Detalle de un animal
- `GET /api/animals/search/?q=<query>` - Buscar animales
- `GET /api/animals/class/<class>/` - Animales por clase
- `GET /api/animals/endangered/` - Animales en peligro

### Sesiones
- `POST /api/sessions/start/` - Iniciar sesión
- `POST /api/sessions/<id>/end/` - Terminar sesión
- `GET /api/sessions/<id>/discoveries/` - Obtener descubrimientos

### WebSocket
- `ws://localhost:8000/ws/recognition/` - Stream de reconocimiento

## 🧪 Tests

```bash
pytest
```

## 🐳 Docker (Producción)

```bash
docker-compose up -d
```

## 📁 Estructura del Proyecto

```
animal_recognition/
├── config/                 # Configuración Django
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── src/
│   ├── domain/            # Capa de Dominio
│   │   ├── entities.py    # Entidades del dominio
│   │   ├── value_objects.py
│   │   ├── ports.py       # Interfaces (contratos)
│   │   ├── services.py    # Servicios de dominio
│   │   └── exceptions.py
│   ├── application/       # Capa de Aplicación
│   │   └── use_cases/     # Casos de uso
│   ├── infrastructure/    # Capa de Infraestructura
│   │   ├── persistence/   # Repositorios Django ORM
│   │   ├── ml/            # Servicios de ML
│   │   └── storage/       # Almacenamiento de archivos
│   └── interfaces/        # Capa de Interfaces
│       ├── api/           # REST API
│       ├── websocket/     # WebSocket consumers
│       └── web/           # Vistas web
├── templates/             # Templates HTML
├── static/                # Archivos estáticos
├── media/                 # Archivos subidos
├── ml_models/             # Modelos de ML
├── scripts/               # Scripts utilitarios
├── manage.py
├── requirements.txt
└── README.md
```

## 🔧 Configuración para Producción

### AWS

1. Configurar EC2 con GPU (opcional para mejor rendimiento)
2. Configurar RDS PostgreSQL
3. Configurar ElastiCache Redis
4. Configurar S3 para almacenamiento de imágenes
5. Configurar CloudFront como CDN

### Variables de entorno producción

```env
DEBUG=False
SECRET_KEY=<tu-secret-key-segura>
ALLOWED_HOSTS=tu-dominio.com
DATABASE_URL=postgres://...
REDIS_URL=redis://...
USE_S3_STORAGE=True
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=...
```

## 📝 Licencia

MIT License

## 👥 Contribuir

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/nueva-caracteristica`)
3. Commit tus cambios (`git commit -am 'Añadir nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crea un Pull Request
