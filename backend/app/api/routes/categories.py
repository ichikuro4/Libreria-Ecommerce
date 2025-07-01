from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.db.session import get_session
from app.models import Category, CategoryCreate, CategoryRead, CategoryUpdate
from app.models import Book, BookRead, BookCategory

router = APIRouter()

@router.get("/", response_model=List[CategoryRead])
async def get_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(True),
    parent_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_session)
):
    """Obtener todas las categorías"""
    try:
        query = select(Category)
        if active_only:
            query = query.where(Category.esta_activa == True)
        
        if parent_id is not None:
            query = query.where(Category.categoria_padre_id == parent_id)
        
        query = query.order_by(Category.orden_display).offset(skip).limit(limit)
        result = await session.execute(query)
        categories = result.scalars().all()
        return categories
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(category_id: int, session: AsyncSession = Depends(get_session)):
    """Obtener una categoría específica"""
    try:
        result = await session.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        
        if not category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        
        return category
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=CategoryRead)
async def create_category(category_data: CategoryCreate, session: AsyncSession = Depends(get_session)):
    """Crear una nueva categoría"""
    try:
        # Verificar si ya existe una categoría con el mismo nombre
        existing = await session.execute(
            select(Category).where(Category.nombre == category_data.nombre)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Ya existe una categoría con este nombre")
        
        # Verificar que la categoría padre existe si se especifica
        if category_data.categoria_padre_id:
            parent = await session.execute(
                select(Category).where(Category.id == category_data.categoria_padre_id)
            )
            if not parent.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="La categoría padre no existe")
        
        category = Category(**category_data.dict(exclude_unset=True))
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: int, 
    category_data: CategoryUpdate, 
    session: AsyncSession = Depends(get_session)
):
    """Actualizar una categoría"""
    try:
        result = await session.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        
        if not category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        
        update_data = category_data.dict(exclude_unset=True)
        
        # Verificar nombre único si se está actualizando
        if "nombre" in update_data:
            existing = await session.execute(
                select(Category).where(
                    Category.nombre == update_data["nombre"],
                    Category.id != category_id
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Ya existe una categoría con este nombre")
        
        for field, value in update_data.items():
            setattr(category, field, value)
        
        await session.commit()
        await session.refresh(category)
        return category
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{category_id}")
async def delete_category(category_id: int, session: AsyncSession = Depends(get_session)):
    """Eliminar una categoría (soft delete)"""
    try:
        result = await session.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        
        if not category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        
        category.esta_activa = False
        await session.commit()
        return {"message": "Categoría eliminada exitosamente", "id": category_id}
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Agregar este endpoint al final del archivo categories.py

@router.get("/{category_id}/books", response_model=List[BookRead])
async def get_category_books(
    category_id: int, 
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """Obtener todos los libros de una categoría"""
    try:
        # Verificar que la categoría existe
        category_result = await session.execute(select(Category).where(Category.id == category_id))
        category = category_result.scalar_one_or_none()
        if not category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        
        # Obtener libros de la categoría
        result = await session.execute(
            select(Book)
            .join(BookCategory)
            .where(BookCategory.categoria_id == category_id)
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