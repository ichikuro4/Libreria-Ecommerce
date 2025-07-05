from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload  # Para eager loading
from typing import List, Optional
from app.core.deps import require_admin

from app.db.session import get_session
from app.models import (
    Book, BookCreate, BookRead, BookUpdate,
    Author, Category, Publisher,
    BookAuthor, BookCategory
)

router = APIRouter()

@router.get("/", response_model=List[BookRead])
async def get_books(session: AsyncSession = Depends(get_session)):
    """Obtener todos los libros"""
    try:
        result = await session.execute(select(Book))
        books = result.scalars().all()
        return books
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{book_id}", response_model=BookRead)
async def get_book(book_id: int, session: AsyncSession = Depends(get_session)):
    """Obtener un libro específico"""
    try:
        result = await session.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()
        
        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        
        return book
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=BookRead)
async def create_book(book_data: BookCreate, session: AsyncSession = Depends(get_session)):
    """Crear un nuevo libro"""
    try:
        book = Book(**book_data.dict())
        session.add(book)
        await session.commit()
        await session.refresh(book)
        return book
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{book_id}", response_model=BookRead)
async def update_book(
    book_id: int, 
    book_data: BookUpdate, 
    session: AsyncSession = Depends(get_session)
):
    """Actualizar un libro"""
    try:
        result = await session.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()
        
        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        
        # Actualizar solo los campos proporcionados
        for field, value in book_data.dict(exclude_unset=True).items():
            setattr(book, field, value)
        
        await session.commit()
        await session.refresh(book)
        return book
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{book_id}")
async def delete_book(book_id: int, session: AsyncSession = Depends(get_session)):
    """Eliminar un libro (soft delete)"""
    try:
        result = await session.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()
        
        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        
        book.esta_activo = False
        await session.commit()
        return {"message": "Libro eliminado exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENDPOINTS INTELIGENTES (AGREGAR AL FINAL DEL ARCHIVO) =====

@router.get("/", response_model=List[BookRead])
async def get_books(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(True),
    # ✅ NUEVOS FILTROS INTELIGENTES
    category_id: Optional[int] = Query(None, description="Filtrar por categoría"),
    author_id: Optional[int] = Query(None, description="Filtrar por autor"),
    publisher_id: Optional[int] = Query(None, description="Filtrar por editorial"),
    featured: Optional[bool] = Query(None, description="Solo libros destacados"),
    bestseller: Optional[bool] = Query(None, description="Solo bestsellers"),
    new_books: Optional[bool] = Query(None, description="Solo libros nuevos"),
    min_price: Optional[float] = Query(None, ge=0, description="Precio mínimo"),
    max_price: Optional[float] = Query(None, ge=0, description="Precio máximo"),
    in_stock: Optional[bool] = Query(None, description="Solo libros en stock"),
    search: Optional[str] = Query(None, description="Buscar en título, ISBN o descripción"),
    session: AsyncSession = Depends(get_session)
):
    """Obtener libros con filtros inteligentes"""
    try:
        query = select(Book)
        
        # Filtros básicos
        if active_only:
            query = query.where(Book.esta_activo == True)
        
        # ✅ FILTRO POR CATEGORÍA
        if category_id:
            query = query.join(BookCategory).where(BookCategory.categoria_id == category_id)
        
        # ✅ FILTRO POR AUTOR
        if author_id:
            query = query.join(BookAuthor).where(BookAuthor.autor_id == author_id)
        
        # ✅ FILTRO POR EDITORIAL
        if publisher_id:
            query = query.where(Book.editorial_id == publisher_id)
        
        # ✅ FILTROS DE ESTADO
        if featured is not None:
            query = query.where(Book.es_destacado == featured)
        
        if bestseller is not None:
            query = query.where(Book.es_bestseller == bestseller)
        
        if new_books is not None:
            query = query.where(Book.es_nuevo == new_books)
        
        # ✅ FILTROS DE PRECIO
        if min_price is not None:
            query = query.where(Book.precio >= min_price)
        
        if max_price is not None:
            query = query.where(Book.precio <= max_price)
        
        # ✅ FILTRO DE STOCK
        if in_stock is not None:
            if in_stock:
                query = query.where(Book.stock > 0)
            else:
                query = query.where(Book.stock == 0)
        
        # ✅ BÚSQUEDA DE TEXTO
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Book.titulo.ilike(search_term)) |
                (Book.isbn.ilike(search_term)) |
                (Book.descripcion.ilike(search_term))
            )
        
        # Paginación
        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        books = result.scalars().all()
        return books
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# ===== ENDPOINTS DE RELACIONES =====

@router.post("/{book_id}/authors/{author_id}")
async def assign_author_to_book(
    book_id: int, 
    author_id: int, 
    orden: int = Query(1, description="Orden del autor (para múltiples autores)"),
    session: AsyncSession = Depends(get_session)
):
    """Asignar un autor a un libro"""
    try:
        # Verificar que el libro existe
        book_result = await session.execute(select(Book).where(Book.id == book_id))
        book = book_result.scalar_one_or_none()
        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        
        # Verificar que el autor existe
        author_result = await session.execute(select(Author).where(Author.id == author_id))
        author = author_result.scalar_one_or_none()
        if not author:
            raise HTTPException(status_code=404, detail="Autor no encontrado")
        
        # Verificar si ya existe la relación
        existing = await session.execute(
            select(BookAuthor).where(
                and_(BookAuthor.libro_id == book_id, BookAuthor.autor_id == author_id)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="El autor ya está asignado a este libro")
        
        # Crear la relación
        book_author = BookAuthor(libro_id=book_id, autor_id=author_id, orden=orden)
        session.add(book_author)
        await session.commit()
        
        return {
            "message": "Autor asignado al libro exitosamente",
            "book_id": book_id,
            "author_id": author_id,
            "orden": orden
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{book_id}/authors/{author_id}")
async def remove_author_from_book(
    book_id: int, 
    author_id: int, 
    session: AsyncSession = Depends(get_session)
):
    """Remover un autor de un libro"""
    try:
        # Buscar la relación
        result = await session.execute(
            select(BookAuthor).where(
                and_(BookAuthor.libro_id == book_id, BookAuthor.autor_id == author_id)
            )
        )
        book_author = result.scalar_one_or_none()
        
        if not book_author:
            raise HTTPException(status_code=404, detail="Relación autor-libro no encontrada")
        
        await session.delete(book_author)
        await session.commit()
        
        return {
            "message": "Autor removido del libro exitosamente",
            "book_id": book_id,
            "author_id": author_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{book_id}/categories/{category_id}")
async def assign_category_to_book(
    book_id: int, 
    category_id: int, 
    session: AsyncSession = Depends(get_session)
):
    """Asignar una categoría a un libro"""
    try:
        # Verificar que el libro existe
        book_result = await session.execute(select(Book).where(Book.id == book_id))
        book = book_result.scalar_one_or_none()
        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        
        # Verificar que la categoría existe
        category_result = await session.execute(select(Category).where(Category.id == category_id))
        category = category_result.scalar_one_or_none()
        if not category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        
        # Verificar si ya existe la relación
        existing = await session.execute(
            select(BookCategory).where(
                and_(BookCategory.libro_id == book_id, BookCategory.categoria_id == category_id)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="La categoría ya está asignada a este libro")
        
        # Crear la relación
        book_category = BookCategory(libro_id=book_id, categoria_id=category_id)
        session.add(book_category)
        await session.commit()
        
        return {
            "message": "Categoría asignada al libro exitosamente",
            "book_id": book_id,
            "category_id": category_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{book_id}/categories/{category_id}")
async def remove_category_from_book(
    book_id: int, 
    category_id: int, 
    session: AsyncSession = Depends(get_session)
):
    """Remover una categoría de un libro"""
    try:
        # Buscar la relación
        result = await session.execute(
            select(BookCategory).where(
                and_(BookCategory.libro_id == book_id, BookCategory.categoria_id == category_id)
            )
        )
        book_category = result.scalar_one_or_none()
        
        if not book_category:
            raise HTTPException(status_code=404, detail="Relación categoría-libro no encontrada")
        
        await session.delete(book_category)
        await session.commit()
        
        return {
            "message": "Categoría removida del libro exitosamente",
            "book_id": book_id,
            "category_id": category_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{book_id}/authors", response_model=List[dict])
async def get_book_authors(book_id: int, session: AsyncSession = Depends(get_session)):
    """Obtener todos los autores de un libro"""
    try:
        result = await session.execute(
            select(Author, BookAuthor.orden)
            .join(BookAuthor)
            .where(BookAuthor.libro_id == book_id)
            .order_by(BookAuthor.orden)
        )
        authors = result.all()
        
        return [
            {
                "id": author.id,
                "nombre_completo": author.nombre_completo,
                "biografia": author.biografia,
                "url_imagen": author.url_imagen,
                "orden": orden
            }
            for author, orden in authors
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{book_id}/categories", response_model=List[dict])
async def get_book_categories(book_id: int, session: AsyncSession = Depends(get_session)):
    """Obtener todas las categorías de un libro"""
    try:
        result = await session.execute(
            select(Category)
            .join(BookCategory)
            .where(BookCategory.libro_id == book_id)
        )
        categories = result.scalars().all()
        
        return [
            {
                "id": category.id,
                "nombre": category.nombre,
                "descripcion": category.descripcion,
                "url_imagen": category.url_imagen
            }
            for category in categories
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{book_id}/stock")
async def update_stock(
    book_id: int, 
    new_stock: int = Query(..., ge=0, description="Nuevo stock del libro"),
    session: AsyncSession = Depends(get_session)
):
    """Actualizar solo el stock de un libro"""
    try:
        result = await session.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()
        
        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        
        # Guardar stock anterior para el log
        old_stock = book.stock
        
        # Actualizar stock
        book.stock = new_stock
        await session.commit()
        
        return {
            "message": "Stock actualizado exitosamente",
            "book_id": book_id,
            "libro_titulo": book.titulo,
            "stock_anterior": old_stock,
            "stock_nuevo": new_stock,
            "diferencia": new_stock - old_stock
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENDPOINT ADICIONAL ÚTIL: Actualizar stock múltiple =====

@router.patch("/bulk-update-stock")
async def bulk_update_stock(
    stock_updates: List[dict],  # [{"book_id": 1, "new_stock": 50}, {"book_id": 2, "new_stock": 30}]
    session: AsyncSession = Depends(get_session)
):
    """Actualizar stock de múltiples libros a la vez"""
    try:
        updated_books = []
        
        for update in stock_updates:
            book_id = update.get("book_id")
            new_stock = update.get("new_stock")
            
            if book_id is None or new_stock is None:
                continue
                
            if new_stock < 0:
                continue
            
            # Buscar el libro
            result = await session.execute(select(Book).where(Book.id == book_id))
            book = result.scalar_one_or_none()
            
            if book:
                old_stock = book.stock
                book.stock = new_stock
                updated_books.append({
                    "book_id": book_id,
                    "titulo": book.titulo,
                    "stock_anterior": old_stock,
                    "stock_nuevo": new_stock
                })
        
        await session.commit()
        
        return {
            "message": f"Stock actualizado para {len(updated_books)} libros",
            "libros_actualizados": updated_books
        }
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENDPOINT ADICIONAL: Alertas de stock bajo =====

@router.get("/low-stock-alerts")
async def get_low_stock_alerts(
    threshold: int = Query(None, description="Umbral personalizado, si no se proporciona usa stock_minimo"),
    session: AsyncSession = Depends(get_session)
):
    """Obtener libros con stock bajo"""
    try:
        if threshold is not None:
            # Usar umbral personalizado
            query = select(Book).where(
                and_(
                    Book.esta_activo == True,
                    Book.stock <= threshold
                )
            )
        else:
            # Usar stock_minimo de cada libro
            query = select(Book).where(
                and_(
                    Book.esta_activo == True,
                    Book.stock <= Book.stock_minimo
                )
            )
        
        result = await session.execute(query)
        low_stock_books = result.scalars().all()
        
        alerts = []
        for book in low_stock_books:
            alerts.append({
                "book_id": book.id,
                "titulo": book.titulo,
                "sku": book.sku,
                "stock_actual": book.stock,
                "stock_minimo": book.stock_minimo,
                "necesita_restock": book.stock_minimo - book.stock,
                "estado_critico": book.stock == 0
            })
        
        return {
            "total_alertas": len(alerts),
            "libros_sin_stock": len([a for a in alerts if a["estado_critico"]]),
            "libros_stock_bajo": len([a for a in alerts if not a["estado_critico"]]),
            "alertas": alerts
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))