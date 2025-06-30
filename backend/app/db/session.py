from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.db.connection import engine

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Obtener sesión asíncrona de base de datos"""
    async_session = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()