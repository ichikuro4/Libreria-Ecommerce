from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv(override=True)

# Variables de entorno
DB_DIALECT = os.getenv('DB_DIALECT')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# URL de conexión
URL_CONNECTION = f'{DB_DIALECT}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'

# Engine asíncrono (como tu proyecto)
async_engine = create_async_engine(
    URL_CONNECTION, 
    connect_args={'ssl': 'require'}, 
    echo=DEBUG
)

# Alias para mantener compatibilidad
engine = async_engine