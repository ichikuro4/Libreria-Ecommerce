from fastapi import APIRouter
from sqlalchemy import text
from app.db.connection import engine

router = APIRouter()

@router.get('/')
async def root():
    return {
        "message": "¡Bienvenido a la API de Librería E-commerce!",
        "version": "1.0.0",
        "docs": "/docs"
    }

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Librería E-commerce API"}

@router.get("/check-tables")
async def check_tables():
    """Endpoint para verificar tablas creadas en la base de datos"""
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            ))
            tables = [row[0] for row in result.fetchall()]
            return {
                "status": "success",
                "tables_created": tables,
                "total_tables": len(tables)
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}