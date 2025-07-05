# backend/app/api/routes/orders.py
"""
Rutas para gestión de pedidos y detalles
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

from app.db.session import get_session
from app.models import (
    Order, OrderCreate, OrderRead, OrderUpdate,
    OrderDetail, OrderDetailCreate, OrderDetailRead,
    User, Book, OrderStatus
)
from app.core.deps import get_current_user, require_admin, require_admin_or_owner

router = APIRouter()

@router.get("/", response_model=List[OrderRead])
async def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[OrderStatus] = Query(None, description="Filtrar por estado"),
    user_id: Optional[int] = Query(None, description="Filtrar por usuario (solo admin)"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Obtener pedidos - Admin ve todos, usuarios solo los suyos"""
    try:
        query = select(Order)
        
        # Si no es admin, solo puede ver sus propios pedidos
        if current_user.rol != "admin":
            query = query.where(Order.usuario_id == current_user.id)
        else:
            # Admin puede filtrar por usuario específico
            if user_id:
                query = query.where(Order.usuario_id == user_id)
        
        # Filtrar por estado si se especifica
        if status:
            query = query.where(Order.estado == status)
        
        # Ordenar por fecha descendente y paginar
        query = query.order_by(Order.fecha.desc()).offset(skip).limit(limit)
        
        result = await session.execute(query)
        orders = result.scalars().all()
        return orders
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin_or_owner)
):
    """Obtener pedido específico"""
    try:
        result = await session.execute(
            select(Order)
            .options(selectinload(Order.detalles))
            .where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
        # Verificar que el usuario puede acceder a este pedido
        if current_user.rol != "admin" and order.usuario_id != current_user.id:
            raise HTTPException(status_code=403, detail="No tienes permisos para ver este pedido")
        
        return order
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=OrderRead)
async def create_order(
    order_data: OrderCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Crear nuevo pedido"""
    try:
        # Crear pedido
        order_dict = order_data.dict()
        order_dict["usuario_id"] = current_user.id
        
        order = Order(**order_dict)
        session.add(order)
        await session.commit()
        await session.refresh(order)
        
        return order
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{order_id}", response_model=OrderRead)
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Actualizar pedido (solo admin)"""
    try:
        result = await session.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
        # Actualizar campos
        update_data = order_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(order, field, value)
        
        await session.commit()
        await session.refresh(order)
        return order
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: int,
    new_status: OrderStatus = Query(..., description="Nuevo estado del pedido"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Actualizar solo el estado del pedido"""
    try:
        result = await session.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
        old_status = order.estado
        order.estado = new_status
        
        # Actualizar fechas según el estado
        if new_status == OrderStatus.SHIPPED:
            order.fecha_envio = datetime.now()
        elif new_status == OrderStatus.DELIVERED:
            order.fecha_entrega_real = datetime.now()
        
        await session.commit()
        
        return {
            "message": "Estado actualizado exitosamente",
            "order_id": order_id,
            "estado_anterior": old_status,
            "estado_nuevo": new_status,
            "numero_pedido": order.numero_pedido
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{order_id}/details", response_model=List[OrderDetailRead])
async def get_order_details(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Obtener detalles de un pedido"""
    try:
        # Verificar que el pedido existe y el usuario tiene acceso
        order_result = await session.execute(select(Order).where(Order.id == order_id))
        order = order_result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
        if current_user.rol != "admin" and order.usuario_id != current_user.id:
            raise HTTPException(status_code=403, detail="No tienes permisos para ver este pedido")
        
        # Obtener detalles
        result = await session.execute(
            select(OrderDetail).where(OrderDetail.pedido_id == order_id)
        )
        details = result.scalars().all()
        return details
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{order_id}/details", response_model=OrderDetailRead)
async def add_order_detail(
    order_id: int,
    detail_data: OrderDetailCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Agregar detalle a un pedido (solo admin)"""
    try:
        # Verificar que el pedido existe
        order_result = await session.execute(select(Order).where(Order.id == order_id))
        order = order_result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
        # Verificar que el libro existe
        book_result = await session.execute(select(Book).where(Book.id == detail_data.libro_id))
        book = book_result.scalar_one_or_none()
        
        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        
        # Crear detalle
        detail_dict = detail_data.dict()
        detail_dict["pedido_id"] = order_id
        
        detail = OrderDetail(**detail_dict)
        session.add(detail)
        await session.commit()
        await session.refresh(detail)
        
        return detail
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}/orders", response_model=List[OrderRead])
async def get_user_orders(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Obtener pedidos de un usuario específico"""
    try:
        # Verificar permisos
        if current_user.rol != "admin" and current_user.id != user_id:
            raise HTTPException(status_code=403, detail="No tienes permisos para ver estos pedidos")
        
        result = await session.execute(
            select(Order)
            .where(Order.usuario_id == user_id)
            .order_by(Order.fecha.desc())
            .offset(skip)
            .limit(limit)
        )
        orders = result.scalars().all()
        return orders
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary")
async def get_orders_stats(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Estadísticas de pedidos (solo admin)"""
    try:
        # Total de pedidos
        total_result = await session.execute(select(func.count(Order.id)))
        total_orders = total_result.scalar()
        
        # Pedidos por estado
        status_result = await session.execute(
            select(Order.estado, func.count(Order.id))
            .group_by(Order.estado)
        )
        orders_by_status = {status: count for status, count in status_result.all()}
        
        # Ventas totales
        sales_result = await session.execute(select(func.sum(Order.total)))
        total_sales = sales_result.scalar() or 0
        
        # Pedidos del mes actual
        current_month = datetime.now().month
        current_year = datetime.now().year
        month_result = await session.execute(
            select(func.count(Order.id))
            .where(
                and_(
                    func.extract('month', Order.fecha) == current_month,
                    func.extract('year', Order.fecha) == current_year
                )
            )
        )
        orders_this_month = month_result.scalar()
        
        return {
            "total_pedidos": total_orders,
            "pedidos_por_estado": orders_by_status,
            "ventas_totales": float(total_sales),
            "pedidos_este_mes": orders_this_month
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))