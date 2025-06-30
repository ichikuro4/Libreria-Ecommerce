# 📚 Librería E-commerce

E-commerce moderno para librería construido con React + TypeScript en el frontend y FastAPI + SQLModel en el backend.

## 🛠️ Tecnologías

### Frontend
- React 18 con TypeScript
- React Router DOM
- Axios para HTTP requests

### Backend
- FastAPI
- SQLModel (SQLAlchemy)
- Pydantic
- Uvicorn
- PostgreSQL (Neon)

## 📋 Requisitos previos

- Node.js 16+ y npm
- Python 3.9+
- Git

## 🚀 Instalación y configuración

### 1. Clonar el repositorio
```bash
git clone <url-del-repositorio>
cd libreria-ecommerce
```

### 2. Configurar el Backend (FastAPI)

```bash
# Navegar al directorio backend
cd backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

#### Configurar variables de entorno
Crear archivo `.env` en la carpeta `backend/`:
```env
DATABASE_URL=postgresql://usuario:password@host:puerto/nombre_db
SECRET_KEY=tu_clave_secreta_aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Configurar el Frontend (React)

```bash
# Navegar al directorio frontend
cd frontend

# Instalar dependencias
npm install
```

#### Configurar variables de entorno
Crear archivo `.env` en la carpeta `frontend/`:
```env
REACT_APP_API_URL=http://localhost:8000
```

## 🏃‍♂️ Ejecutar el proyecto

### Ejecutar Backend
```bash
cd backend

# Activar entorno virtual si no está activo
source venv/bin/activate  # macOS/Linux
# o
venv\Scripts\activate     # Windows

# Ejecutar servidor de desarrollo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

El backend estará disponible en: `http://localhost:8000`
- API docs (Swagger): `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Ejecutar Frontend
```bash
cd frontend

# Ejecutar servidor de desarrollo
npm start
```

El frontend estará disponible en: `http://localhost:3000`

## 📁 Estructura del proyecto

```
libreria-ecommerce/
├── frontend/                 # React + TypeScript
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── types/
│   │   └── utils/
│   ├── package.json
│   └── .env
├── backend/                  # FastAPI
│   ├── app/
│   │   ├── api/              # Rutas/endpoints
│   │   ├── core/             # Configuración
│   │   ├── models/           # SQLModel models
│   │   ├── database.py
│   │   └── main.py
│   ├── venv/
│   ├── requirements.txt
│   └── .env
├── docs/
├── .gitignore
└── README.md
```

## 🗄️ Base de datos

Este proyecto utiliza PostgreSQL hospedado en Neon. Para configurar:

1. Crear cuenta en [neon.tech](https://neon.tech)
2. Crear nueva base de datos
3. Copiar la connection string al archivo `.env` del backend

## 🚀 Deploy

### Backend (Railway/Render/Heroku)
1. Crear `Procfile` en la raíz del backend:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Frontend (Vercel/Netlify)
1. Build del proyecto:
```bash
cd frontend
npm run build
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📝 Comandos útiles

### Backend
```bash
# Crear nuevas migraciones
alembic revision --autogenerate -m "descripción"

# Aplicar migraciones
alembic upgrade head

# Ejecutar tests
pytest

# Formatear código
black app/
```

### Frontend
```bash
# Ejecutar tests
npm test

# Build para producción
npm run build

# Analizar bundle
npm run build && npx serve -s build
```

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 👥 Autores

- Ichikuro

## 🙏 Agradecimientos

- FastAPI por su excelente framework
- React team por la increíble librería
- Neon por el hosting de PostgreSQL