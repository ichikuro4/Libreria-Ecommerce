# backend/app/api/routes/promotions.py
"""
Rutas para gestión de promociones y cupones
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from app.db.session import get_session
from app.models import (
    Promotion, PromotionCreate, PromotionRead, PromotionUpdate,
    Coupon, CouponCreate, CouponRead, CouponUpdate,
    Book, Category, PromotionBook, PromotionCategory,
    User, DiscountType
)
from app.core.deps import get_current_user, require_admin

router = APIRouter()

# ===== PROMOCIONES =====

@router.get("/", response_model=List[PromotionRead])
async def get_promotions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(True, description="Solo promociones activas"),
    session: AsyncSession = Depends(get_session)
):
    """Obtener todas las promociones"""
    try:
        query = select(Promotion)
        
        if active_only:
            now = datetime.now()
            query = query.where(
                and_(
                    Promotion.es_activa == True,
                    or_(
                        Promotion.fecha_fin.is_(None),
                        Promotion.fecha_fin >= now
                    ),
                    Promotion.fecha_inicio <= now
                )
            )
        
        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        promotions = result.scalars().all()
        return promotions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{promotion_id}", response_model=PromotionRead)
async def get_promotion(
    promotion_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Obtener promoción específica"""
    try:
        result = await session.execute(select(Promotion).where(Promotion.id == promotion_id))
        promotion = result.scalar_one_or_none()
        
        if not promotion:
            raise HTTPException(status_code=404, detail="Promoción no encontrada")
        
        return promotion
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=PromotionRead)
async def create_promotion(
    promotion_data: PromotionCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Crear nueva promoción (solo admin)"""
    try:
        promotion = Promotion(**promotion_data.dict())
        session.add(promotion)
        await session.commit()
        await session.refresh(promotion)
        return promotion
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{promotion_id}", response_model=PromotionRead)
async def update_promotion(
    promotion_id: int,
    promotion_data: PromotionUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Actualizar promoción (solo admin)"""
    try:
        result = await session.execute(select(Promotion).where(Promotion.id == promotion_id))
        promotion = result.scalar_one_or_none()
        
        if not promotion:
            raise HTTPException(status_code=404, detail="Promoción no encontrada")
        
        update_data = promotion_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(promotion, field, value)
        
        await session.commit()
        await session.refresh(promotion)
        return promotion
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{promotion_id}")
async def deactivate_promotion(
    promotion_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Desactivar promoción (solo admin)"""
    try:
        result = await session.execute(select(Promotion).where(Promotion.id == promotion_id))
        promotion = result.scalar_one_or_none()
        
        if not promotion:
            raise HTTPException(status_code=404, detail="Promoción no encontrada")
        
        promotion.es_activa = False
        await session.commit()
        
        return {"message": "Promoción desactivada exitosamente", "id": promotion_id}
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ===== ASIGNACIONES DE PROMOCIONES =====

@router.post("/{promotion_id}/books/{book_id}")
async def assign_promotion_to_book(
    promotion_id: int,
    book_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Asignar promoción a un libro específico"""
    try:
        # Verificar que la promoción existe
        promo_result = await session.execute(select(Promotion).where(Promotion.id == promotion_id))
        promotion = promo_result.scalar_one_or_none()
        if not promotion:
            raise HTTPException(status_code=404, detail="Promoción no encontrada")
        
        # Verificar que el libro existe
        book_result = await session.execute(select(Book).where(Book.id == book_id))
        book = book_result.scalar_one_or_none()
        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        
        # Verificar si ya existe la relación
        existing = await session.execute(
            select(PromotionBook).where(
                and_(PromotionBook.promocion_id == promotion_id, PromotionBook.libro_id == book_id)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="La promoción ya está asignada a este libro")
        
        # Crear relación
        promo_book = PromotionBook(promocion_id=promotion_id, libro_id=book_id)
        session.add(promo_book)
        await session.commit()
        
        return {"message": "Promoción asignada al libro exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{promotion_id}/categories/{category_id}")
async def assign_promotion_to_category(
    promotion_id: int,
    category_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Asignar promoción a una categoría"""
    try:
        # Verificaciones similares...
        promo_result = await session.execute(select(Promotion).where(Promotion.id == promotion_id))
        promotion = promo_result.scalar_one_or_none()
        if not promotion:
            raise HTTPException(status_code=404, detail="Promoción no encontrada")
        
        cat_result = await session.execute(select(Category).where(Category.id == category_id))
        category = cat_result.scalar_one_or_none()
        if not category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        
        existing = await session.execute(
            select(PromotionCategory).where(
                and_(PromotionCategory.promocion_id == promotion_id, PromotionCategory.categoria_id == category_id)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="La promoción ya está asignada a esta categoría")
        
        promo_cat = PromotionCategory(promocion_id=promotion_id, categoria_id=category_id)
        session.add(promo_cat)
        await session.commit()
        
        return {"message": "Promoción asignada a la categoría exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ===== CUPONES =====

@router.get("/coupons/", response_model=List[CouponRead])
async def get_coupons(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(True, description="Solo cupones activos"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Obtener todos los cupones (solo admin)"""
    try:
        query = select(Coupon)
        
        if active_only:
            now = datetime.now()
            query = query.where(
                and_(
                    Coupon.es_activo == True,
                    or_(
                        Coupon.fecha_expiracion.is_(None),
                        Coupon.fecha_expiracion >= now
                    )
                )
            )
        
        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        coupons = result.scalars().all()
        return coupons
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/coupons/", response_model=CouponRead)
async def create_coupon(
    coupon_data: CouponCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Crear nuevo cupón (solo admin)"""
    try:
        # Verificar que el código no existe
        existing = await session.execute(
            select(Coupon).where(Coupon.codigo == coupon_data.codigo)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Ya existe un cupón con este código")
        
        # Verificar que la promoción existe
        promo_result = await session.execute(select(Promotion).where(Promotion.id == coupon_data.promocion_id))
        if not promo_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Promoción no encontrada")
        
        coupon = Coupon(**coupon_data.dict())
        session.add(coupon)
        await session.commit()
        await session.refresh(coupon)
        return coupon
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/coupons/{coupon_code}/validate")
async def validate_coupon(
    coupon_code: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Validar cupón para usar en checkout"""
    try:
        # Buscar cupón por código
        result = await session.execute(
            select(Coupon, Promotion)
            .join(Promotion)
            .where(Coupon.codigo == coupon_code)
        )
        coupon_promo = result.first()
        
        if not coupon_promo:
            raise HTTPException(status_code=404, detail="Cupón no encontrado")
        
        coupon, promotion = coupon_promo
        
        # Validaciones
        now = datetime.now()
        
        if not coupon.es_activo:
            return {"valid": False, "error": "Cupón inactivo"}
        
        if coupon.fecha_expiracion and coupon.fecha_expiracion < now:
            return {"valid": False, "error": "Cupón expirado"}
        
        if coupon.limite_usos and coupon.usos_actuales >= coupon.limite_usos:
            return {"valid": False, "error": "Cupón agotado"}
        
        if not promotion.es_activa:
            return {"valid": False, "error": "Promoción inactiva"}
        
        if promotion.fecha_fin and promotion.fecha_fin < now:
            return {"valid": False, "error": "Promoción expirada"}
        
        if promotion.fecha_inicio > now:
            return {"valid": False, "error": "Promoción aún no vigente"}
        
        # TODO: Verificar si es solo para primera compra
        
        return {
            "valid": True,
            "coupon": CouponRead.from_orm(coupon),
            "promotion": PromotionRead.from_orm(promotion),
            "discount_type": promotion.tipo_descuento,
            "discount_value": promotion.valor
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/coupons/{coupon_code}/use")
async def use_coupon(
    coupon_code: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Marcar cupón como usado (incrementar contador)"""
    try:
        result = await session.execute(select(Coupon).where(Coupon.codigo == coupon_code))
        coupon = result.scalar_one_or_none()
        
        if not coupon:
            raise HTTPException(status_code=404, detail="Cupón no encontrado")
        
        coupon.usos_actuales += 1
        await session.commit()
        
        return {"message": "Cupón usado exitosamente", "usos_restantes": coupon.limite_usos - coupon.usos_actuales if coupon.limite_usos else None}
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/coupons/{coupon_id}", response_model=CouponRead)
async def update_coupon(
    coupon_id: int,
    coupon_data: CouponUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Actualizar cupón (solo admin)"""
    try:
        result = await session.execute(select(Coupon).where(Coupon.id == coupon_id))
        coupon = result.scalar_one_or_none()
        
        if not coupon:
            raise HTTPException(status_code=404, detail="Cupón no encontrado")
        
        update_data = coupon_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(coupon, field, value)
        
        await session.commit()
        await session.refresh(coupon)
        return coupon
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ===== CÁLCULOS DE DESCUENTOS =====

@router.post("/calculate-discount")
async def calculate_discount(
    cart_items: List[dict],  # [{"book_id": 1, "quantity": 2, "price": 25.99}, ...]
    coupon_code: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Calcular descuentos aplicables a un carrito"""
    try:
        total_items = Decimal('0')
        applicable_items = []
        
        # Calcular total del carrito
        for item in cart_items:
            book_id = item.get("book_id")
            quantity = item.get("quantity", 1)
            price = Decimal(str(item.get("price", 0)))
            
            item_total = price * quantity
            total_items += item_total
            
            applicable_items.append({
                "book_id": book_id,
                "quantity": quantity,
                "price": price,
                "total": item_total
            })
        
        discount_amount = Decimal('0')
        applied_promotion = None
        
        # Si hay cupón, calcular descuento
        if coupon_code:
            coupon_result = await session.execute(
                select(Coupon, Promotion)
                .join(Promotion)
                .where(Coupon.codigo == coupon_code)
            )
            coupon_promo = coupon_result.first()
            
            if coupon_promo:
                coupon, promotion = coupon_promo
                
                # Verificar validez del cupón (mismas validaciones que validate_coupon)
                now = datetime.now()
                is_valid = (
                    coupon.es_activo and
                    promotion.es_activa and
                    (not coupon.fecha_expiracion or coupon.fecha_expiracion >= now) and
                    (not promotion.fecha_fin or promotion.fecha_fin >= now) and
                    promotion.fecha_inicio <= now and
                    (not coupon.limite_usos or coupon.usos_actuales < coupon.limite_usos)
                )
                
                if is_valid:
                    # Verificar si cumple monto mínimo
                    if total_items >= promotion.monto_minimo_compra:
                        # Calcular descuento
                        if promotion.tipo_descuento == DiscountType.PERCENTAGE:
                            discount_amount = (total_items * promotion.valor) / 100
                        elif promotion.tipo_descuento == DiscountType.FIXED_AMOUNT:
                            discount_amount = min(promotion.valor, total_items)
                        
                        applied_promotion = {
                            "id": promotion.id,
                            "nombre": promotion.nombre,
                            "tipo_descuento": promotion.tipo_descuento,
                            "valor": promotion.valor,
                            "coupon_code": coupon_code
                        }
        
        final_total = total_items - discount_amount
        
        return {
            "subtotal": float(total_items),
            "descuento": float(discount_amount),
            "total_final": float(final_total),
            "promocion_aplicada": applied_promotion,
            "items": applicable_items
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))