from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_session
from app.models import Publisher, PublisherCreate, PublisherRead, PublisherUpdate
from app.models import Book, BookRead

router = APIRouter()

@router.get("/", response_model=List[PublisherRead])
async def get_publishers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(True),
    session: AsyncSession = Depends(get_session)
):
    """Obtener todas las editoriales"""
    try:
        query = select(Publisher)
        if active_only:
            query = query.where(Publisher.esta_activa == True)
        
        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        publishers = result.scalars().all()
        return publishers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{publisher_id}", response_model=PublisherRead)
async def get_publisher(publisher_id: int, session: AsyncSession = Depends(get_session)):
    """Obtener una editorial específica"""
    try:
        result = await session.execute(select(Publisher).where(Publisher.id == publisher_id))
        publisher = result.scalar_one_or_none()
        
        if not publisher:
            raise HTTPException(status_code=404, detail="Editorial no encontrada")
        
        return publisher
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=PublisherRead)
async def create_publisher(publisher_data: PublisherCreate, session: AsyncSession = Depends(get_session)):
    """Crear una nueva editorial"""
    try:
        # Verificar si ya existe una editorial con el mismo nombre
        existing = await session.execute(
            select(Publisher).where(Publisher.nombre == publisher_data.nombre)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Ya existe una editorial con este nombre")
        
        publisher = Publisher(**publisher_data.dict(exclude_unset=True))
        session.add(publisher)
        await session.commit()
        await session.refresh(publisher)
        return publisher
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{publisher_id}", response_model=PublisherRead)
async def update_publisher(
    publisher_id: int, 
    publisher_data: PublisherUpdate, 
    session: AsyncSession = Depends(get_session)
):
    """Actualizar una editorial"""
    try:
        result = await session.execute(select(Publisher).where(Publisher.id == publisher_id))
        publisher = result.scalar_one_or_none()
        
        if not publisher:
            raise HTTPException(status_code=404, detail="Editorial no encontrada")
        
        update_data = publisher_data.dict(exclude_unset=True)
        
        # Verificar nombre único si se está actualizando
        if "nombre" in update_data:
            existing = await session.execute(
                select(Publisher).where(
                    Publisher.nombre == update_data["nombre"],
                    Publisher.id != publisher_id
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Ya existe una editorial con este nombre")
        
        for field, value in update_data.items():
            setattr(publisher, field, value)
        
        await session.commit()
        await session.refresh(publisher)
        return publisher
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{publisher_id}")
async def delete_publisher(publisher_id: int, session: AsyncSession = Depends(get_session)):
    """Eliminar una editorial (soft delete)"""
    try:
        result = await session.execute(select(Publisher).where(Publisher.id == publisher_id))
        publisher = result.scalar_one_or_none()
        
        if not publisher:
            raise HTTPException(status_code=404, detail="Editorial no encontrada")
        
        publisher.esta_activa = False
        await session.commit()
        return {"message": "Editorial eliminada exitosamente", "id": publisher_id}
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{publisher_id}/books", response_model=List[BookRead])
async def get_publisher_books(
    publisher_id: int, 
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """Obtener todos los libros de una editorial"""
    try:
        # Verificar que la editorial existe
        publisher_result = await session.execute(select(Publisher).where(Publisher.id == publisher_id))
        publisher = publisher_result.scalar_one_or_none()
        if not publisher:
            raise HTTPException(status_code=404, detail="Editorial no encontrada")
        
        # Obtener libros de la editorial
        result = await session.execute(
            select(Book)
            .where(Book.editorial_id == publisher_id)
            .where(Book.esta_activo == True)
            .offset(skip)
            .limit(limit)
        )
        books = result.scalars().all()
        return books
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))