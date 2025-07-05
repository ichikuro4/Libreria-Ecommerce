# backend/app/api/routes/reviews.py
"""
Rutas para gestión de reseñas y lista de deseos
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from decimal import Decimal

from app.db.session import get_session
from app.models import (
    Review, ReviewCreate, ReviewRead, ReviewUpdate,
    WishList, WishListCreate, WishListRead,
    User, Book
)
from app.core.deps import get_current_user, require_admin

router = APIRouter()

# ===== RESEÑAS =====

@router.get("/", response_model=List[ReviewRead])
async def get_reviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    book_id: Optional[int] = Query(None, description="Filtrar por libro"),
    user_id: Optional[int] = Query(None, description="Filtrar por usuario"),
    min_rating: Optional[int] = Query(None, ge=1, le=5, description="Calificación mínima"),
    verified_only: Optional[bool] = Query(None, description="Solo reseñas verificadas"),
    session: AsyncSession = Depends(get_session)
):
    """Obtener reseñas con filtros"""
    try:
        query = select(Review)
        
        # Aplicar filtros
        if book_id:
            query = query.where(Review.libro_id == book_id)
        
        if user_id:
            query = query.where(Review.usuario_id == user_id)
        
        if min_rating:
            query = query.where(Review.puntuacion >= min_rating)
        
        if verified_only is not None:
            query = query.where(Review.es_verificada == verified_only)
        
        # Ordenar por fecha descendente y paginar
        query = query.order_by(Review.fecha.desc()).offset(skip).limit(limit)
        
        result = await session.execute(query)
        reviews = result.scalars().all()
        return reviews
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{review_id}", response_model=ReviewRead)
async def get_review(
    review_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Obtener reseña específica"""
    try:
        result = await session.execute(select(Review).where(Review.id == review_id))
        review = result.scalar_one_or_none()
        
        if not review:
            raise HTTPException(status_code=404, detail="Reseña no encontrada")
        
        return review
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=ReviewRead)
async def create_review(
    review_data: ReviewCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Crear nueva reseña"""
    try:
        # Verificar que el libro existe
        book_result = await session.execute(select(Book).where(Book.id == review_data.libro_id))
        book = book_result.scalar_one_or_none()
        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        
        # Verificar que el usuario no haya reseñado ya este libro
        existing_review = await session.execute(
            select(Review).where(
                and_(
                    Review.libro_id == review_data.libro_id,
                    Review.usuario_id == current_user.id
                )
            )
        )
        if existing_review.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Ya has reseñado este libro")
        
        # Crear reseña
        review_dict = review_data.dict()
        review_dict["usuario_id"] = current_user.id
        
        review = Review(**review_dict)
        session.add(review)
        await session.commit()
        await session.refresh(review)
        
        return review
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{review_id}", response_model=ReviewRead)
async def update_review(
    review_id: int,
    review_data: ReviewUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Actualizar reseña (solo el autor de la reseña)"""
    try:
        result = await session.execute(select(Review).where(Review.id == review_id))
        review = result.scalar_one_or_none()
        
        if not review:
            raise HTTPException(status_code=404, detail="Reseña no encontrada")
        
        # Verificar que el usuario es el autor de la reseña o admin
        if review.usuario_id != current_user.id and current_user.rol != "admin":
            raise HTTPException(status_code=403, detail="No tienes permisos para editar esta reseña")
        
        # Actualizar campos
        update_data = review_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(review, field, value)
        
        await session.commit()
        await session.refresh(review)
        return review
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{review_id}")
async def delete_review(
    review_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Eliminar reseña (solo el autor o admin)"""
    try:
        result = await session.execute(select(Review).where(Review.id == review_id))
        review = result.scalar_one_or_none()
        
        if not review:
            raise HTTPException(status_code=404, detail="Reseña no encontrada")
        
        # Verificar permisos
        if review.usuario_id != current_user.id and current_user.rol != "admin":
            raise HTTPException(status_code=403, detail="No tienes permisos para eliminar esta reseña")
        
        await session.delete(review)
        await session.commit()
        
        return {"message": "Reseña eliminada exitosamente", "id": review_id}
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{review_id}/helpful")
async def mark_review_helpful(
    review_id: int,
    helpful: bool = Query(..., description="True para útil, False para no útil"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Marcar reseña como útil o no útil"""
    try:
        result = await session.execute(select(Review).where(Review.id == review_id))
        review = result.scalar_one_or_none()
        
        if not review:
            raise HTTPException(status_code=404, detail="Reseña no encontrada")
        
        # No puedes votar tu propia reseña
        if review.usuario_id == current_user.id:
            raise HTTPException(status_code=400, detail="No puedes votar tu propia reseña")
        
        # Actualizar contador
        if helpful:
            review.util_positivo += 1
        else:
            review.util_negativo += 1
        
        await session.commit()
        
        return {
            "message": f"Reseña marcada como {'útil' if helpful else 'no útil'}",
            "util_positivo": review.util_positivo,
            "util_negativo": review.util_negativo
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/book/{book_id}/stats")
async def get_book_review_stats(
    book_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Obtener estadísticas de reseñas de un libro"""
    try:
        # Verificar que el libro existe
        book_result = await session.execute(select(Book).where(Book.id == book_id))
        if not book_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        
        # Estadísticas generales
        stats_result = await session.execute(
            select(
                func.count(Review.id).label('total_reviews'),
                func.avg(Review.puntuacion).label('promedio_puntuacion'),
                func.count(Review.id).filter(Review.puntuacion == 5).label('cinco_estrellas'),
                func.count(Review.id).filter(Review.puntuacion == 4).label('cuatro_estrellas'),
                func.count(Review.id).filter(Review.puntuacion == 3).label('tres_estrellas'),
                func.count(Review.id).filter(Review.puntuacion == 2).label('dos_estrellas'),
                func.count(Review.id).filter(Review.puntuacion == 1).label('una_estrella')
            ).where(Review.libro_id == book_id)
        )
        
        stats = stats_result.first()
        
        return {
            "libro_id": book_id,
            "total_resenas": stats.total_reviews,
            "promedio_puntuacion": float(stats.promedio_puntuacion) if stats.promedio_puntuacion else 0,
            "distribucion_estrellas": {
                "5": stats.cinco_estrellas,
                "4": stats.cuatro_estrellas,
                "3": stats.tres_estrellas,
                "2": stats.dos_estrellas,
                "1": stats.una_estrella
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== LISTA DE DESEOS =====

@router.get("/wishlist/", response_model=List[WishListRead])
async def get_my_wishlist(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Obtener mi lista de deseos"""
    try:
        result = await session.execute(
            select(WishList)
            .where(WishList.usuario_id == current_user.id)
            .order_by(WishList.fecha_agregado.desc())
        )
        wishlist = result.scalars().all()
        return wishlist
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/wishlist/", response_model=WishListRead)
async def add_to_wishlist(
    wishlist_data: WishListCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Agregar libro a lista de deseos"""
    try:
        # Verificar que el libro existe
        book_result = await session.execute(select(Book).where(Book.id == wishlist_data.libro_id))
        if not book_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        
        # Verificar que no esté ya en la lista
        existing = await session.execute(
            select(WishList).where(
                and_(
                    WishList.usuario_id == current_user.id,
                    WishList.libro_id == wishlist_data.libro_id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="El libro ya está en tu lista de deseos")
        
        # Agregar a lista de deseos
        wishlist_item = WishList(
            usuario_id=current_user.id,
            libro_id=wishlist_data.libro_id
        )
        session.add(wishlist_item)
        await session.commit()
        await session.refresh(wishlist_item)
        
        return wishlist_item
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/wishlist/{book_id}")
async def remove_from_wishlist(
    book_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Remover libro de lista de deseos"""
    try:
        result = await session.execute(
            select(WishList).where(
                and_(
                    WishList.usuario_id == current_user.id,
                    WishList.libro_id == book_id
                )
            )
        )
        wishlist_item = result.scalar_one_or_none()
        
        if not wishlist_item:
            raise HTTPException(status_code=404, detail="El libro no está en tu lista de deseos")
        
        await session.delete(wishlist_item)
        await session.commit()
        
        return {"message": "Libro removido de lista de deseos exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/wishlist/check/{book_id}")
async def check_in_wishlist(
    book_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Verificar si un libro está en la lista de deseos"""
    try:
        result = await session.execute(
            select(WishList).where(
                and_(
                    WishList.usuario_id == current_user.id,
                    WishList.libro_id == book_id
                )
            )
        )
        is_in_wishlist = result.scalar_one_or_none() is not None
        
        return {"book_id": book_id, "in_wishlist": is_in_wishlist}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))