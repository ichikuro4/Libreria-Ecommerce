"""
Modelos relacionados con pedidos y detalles de pedidos
"""

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from .base import OrderStatus

# Orders
class Order(SQLModel, table=True):
    __tablename__ = "pedidos"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    numero_pedido: Optional[str] = Field(default=None, max_length=50, unique=True)
    usuario_id: int = Field(foreign_key="usuarios.id")
    fecha: Optional[datetime] = Field(default_factory=datetime.now)
    subtotal: Decimal = Field(decimal_places=2)
    descuento_total: Decimal = Field(default=0, decimal_places=2)
    costo_envio: Decimal = Field(default=0, decimal_places=2)
    impuestos: Decimal = Field(default=0, decimal_places=2)
    total: Decimal = Field(decimal_places=2)
    estado: OrderStatus = Field(default=OrderStatus.PENDING_PAYMENT)
    
    # Dirección de envío (JSON string)
    direccion_envio_json: Optional[str] = Field(default=None)
    
    # Información de pago
    payment_gateway: Optional[str] = Field(default=None, max_length=50)
    gateway_payment_id: Optional[str] = Field(default=None, max_length=255, unique=True)
    payment_status: Optional[str] = Field(default="pending", max_length=50)
    
    # Información de envío
    codigo_seguimiento: Optional[str] = Field(default=None, max_length=100)
    fecha_envio: Optional[datetime] = Field(default=None)
    fecha_entrega_estimada: Optional[datetime] = Field(default=None)
    fecha_entrega_real: Optional[datetime] = Field(default=None)
    
    # Cupón aplicado
    cupon_aplicado: Optional[str] = Field(default=None, max_length=50)
    descuento_cupon: Decimal = Field(default=0, decimal_places=2)
    
    notas: Optional[str] = Field(default=None)
    
    # Relationships
    usuario: "User" = Relationship(back_populates="pedidos")
    detalles: List["OrderDetail"] = Relationship(back_populates="pedido")

class OrderCreate(SQLModel):
    subtotal: Decimal
    descuento_total: Decimal = 0
    costo_envio: Decimal = 0
    impuestos: Decimal = 0
    total: Decimal
    direccion_envio_json: Optional[str] = None
    cupon_aplicado: Optional[str] = None
    descuento_cupon: Decimal = 0
    notas: Optional[str] = None

class OrderRead(SQLModel):
    id: int
    numero_pedido: Optional[str]
    usuario_id: int
    fecha: Optional[datetime]
    subtotal: Decimal
    descuento_total: Decimal
    costo_envio: Decimal
    impuestos: Decimal
    total: Decimal
    estado: OrderStatus
    payment_status: Optional[str]
    codigo_seguimiento: Optional[str]
    fecha_envio: Optional[datetime]
    fecha_entrega_estimada: Optional[datetime]
    cupon_aplicado: Optional[str]
    descuento_cupon: Decimal

class OrderUpdate(SQLModel):
    estado: Optional[OrderStatus] = None
    codigo_seguimiento: Optional[str] = None
    fecha_envio: Optional[datetime] = None
    fecha_entrega_estimada: Optional[datetime] = None
    fecha_entrega_real: Optional[datetime] = None
    notas: Optional[str] = None

# Order Details
class OrderDetail(SQLModel, table=True):
    __tablename__ = "detalle_pedidos"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    pedido_id: int = Field(foreign_key="pedidos.id")
    libro_id: int = Field(foreign_key="libros.id")
    cantidad: int = Field(gt=0)
    precio_unitario: Decimal = Field(decimal_places=2)
    
    # Información del libro al momento de la compra
    titulo_libro: str = Field(max_length=255)
    sku_libro: Optional[str] = Field(default=None, max_length=100)
    isbn_libro: Optional[str] = Field(default=None, max_length=13)
    
    # Relationships
    pedido: "Order" = Relationship(back_populates="detalles")

class OrderDetailCreate(SQLModel):
    libro_id: int
    cantidad: int
    precio_unitario: Decimal
    titulo_libro: str
    sku_libro: Optional[str] = None
    isbn_libro: Optional[str] = None

class OrderDetailRead(SQLModel):
    id: int
    pedido_id: int
    libro_id: int
    cantidad: int
    precio_unitario: Decimal
    titulo_libro: str
    sku_libro: Optional[str]
    isbn_libro: Optional[str]