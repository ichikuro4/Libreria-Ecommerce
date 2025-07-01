from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_session
from app.models import Author, AuthorCreate, AuthorRead, AuthorUpdate
from app.models import Book, BookRead, BookAuthor

router = APIRouter()

@router.get("/", response_model=List[AuthorRead])
async def get_authors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(True),
    session: AsyncSession = Depends(get_session)
):
    """Obtener todos los autores"""
    try:
        query = select(Author)
        if active_only:
            query = query.where(Author.esta_activo == True)
        
        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        authors = result.scalars().all()
        return authors
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{author_id}", response_model=AuthorRead)
async def get_author(author_id: int, session: AsyncSession = Depends(get_session)):
    """Obtener un autor específico"""
    try:
        result = await session.execute(select(Author).where(Author.id == author_id))
        author = result.scalar_one_or_none()
        
        if not author:
            raise HTTPException(status_code=404, detail="Autor no encontrado")
        
        return author
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=AuthorRead)
async def create_author(author_data: AuthorCreate, session: AsyncSession = Depends(get_session)):
    """Crear un nuevo autor"""
    try:
        author = Author(**author_data.dict(exclude_unset=True))
        session.add(author)
        await session.commit()
        await session.refresh(author)
        return author
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{author_id}", response_model=AuthorRead)
async def update_author(
    author_id: int, 
    author_data: AuthorUpdate, 
    session: AsyncSession = Depends(get_session)
):
    """Actualizar un autor"""
    try:
        result = await session.execute(select(Author).where(Author.id == author_id))
        author = result.scalar_one_or_none()
        
        if not author:
            raise HTTPException(status_code=404, detail="Autor no encontrado")
        
        update_data = author_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(author, field, value)
        
        await session.commit()
        await session.refresh(author)
        return author
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{author_id}")
async def delete_author(author_id: int, session: AsyncSession = Depends(get_session)):
    """Eliminar un autor (soft delete)"""
    try:
        result = await session.execute(select(Author).where(Author.id == author_id))
        author = result.scalar_one_or_none()
        
        if not author:
            raise HTTPException(status_code=404, detail="Autor no encontrado")
        
        author.esta_activo = False
        await session.commit()
        return {"message": "Autor eliminado exitosamente", "id": author_id}
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Agregar este endpoint al final del archivo authors.py

@router.get("/{author_id}/books", response_model=List[BookRead])
async def get_author_books(
    author_id: int, 
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """Obtener todos los libros de un autor"""
    try:
        # Verificar que el autor existe
        author_result = await session.execute(select(Author).where(Author.id == author_id))
        author = author_result.scalar_one_or_none()
        if not author:
            raise HTTPException(status_code=404, detail="Autor no encontrado")
        
        # Obtener libros del autor
        result = await session.execute(
            select(Book)
            .join(BookAuthor)
            .where(BookAuthor.autor_id == author_id)
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