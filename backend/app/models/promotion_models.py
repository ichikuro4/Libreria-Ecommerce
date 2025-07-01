"""
Modelos relacionados con promociones y cupones
"""

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from .base import DiscountType

# Promotions
class Promotion(SQLModel, table=True):
    __tablename__ = "promociones"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=255)
    descripcion: Optional[str] = Field(default=None)
    tipo_descuento: DiscountType
    valor: Decimal = Field(decimal_places=2)
    monto_minimo_compra: Decimal = Field(default=0, decimal_places=2)
    fecha_inicio: Optional[datetime] = Field(default_factory=datetime.now)
    fecha_fin: Optional[datetime] = Field(default=None)
    es_activa: bool = Field(default=True)
    uso_maximo: Optional[int] = Field(default=None)
    uso_actual: int = Field(default=0)
    
    # Relationships
    cupones: List["Coupon"] = Relationship(back_populates="promocion")
    libros: List["PromotionBook"] = Relationship(back_populates="promocion")
    categorias: List["PromotionCategory"] = Relationship(back_populates="promocion")

class PromotionCreate(SQLModel):
    nombre: str
    descripcion: Optional[str] = None
    tipo_descuento: DiscountType
    valor: Decimal
    monto_minimo_compra: Decimal = 0
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    uso_maximo: Optional[int] = None

class PromotionRead(SQLModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    tipo_descuento: DiscountType
    valor: Decimal
    monto_minimo_compra: Decimal
    fecha_inicio: Optional[datetime]
    fecha_fin: Optional[datetime]
    es_activa: bool
    uso_maximo: Optional[int]
    uso_actual: int

class PromotionUpdate(SQLModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    valor: Optional[Decimal] = None
    monto_minimo_compra: Optional[Decimal] = None
    fecha_fin: Optional[datetime] = None
    es_activa: Optional[bool] = None

# Coupons
class Coupon(SQLModel, table=True):
    __tablename__ = "cupones"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(max_length=50, unique=True)
    promocion_id: int = Field(foreign_key="promociones.id")
    fecha_expiracion: Optional[datetime] = Field(default=None)
    limite_usos: Optional[int] = Field(default=None)
    usos_actuales: int = Field(default=0)
    es_activo: bool = Field(default=True)
    solo_primer_compra: bool = Field(default=False)
    
    # Relationships
    promocion: "Promotion" = Relationship(back_populates="cupones")

class CouponCreate(SQLModel):
    codigo: str
    promocion_id: int
    fecha_expiracion: Optional[datetime] = None
    limite_usos: Optional[int] = None
    solo_primer_compra: bool = False

class CouponRead(SQLModel):
    id: int
    codigo: str
    promocion_id: int
    fecha_expiracion: Optional[datetime]
    limite_usos: Optional[int]
    usos_actuales: int
    es_activo: bool
    solo_primer_compra: bool

class CouponUpdate(SQLModel):
    fecha_expiracion: Optional[datetime] = None
    limite_usos: Optional[int] = None
    es_activo: Optional[bool] = None

# Junction Tables
class PromotionBook(SQLModel, table=True):
    __tablename__ = "promocion_libros"
    
    promocion_id: int = Field(foreign_key="promociones.id", primary_key=True)
    libro_id: int = Field(foreign_key="libros.id", primary_key=True)
    
    # Relationships
    promocion: "Promotion" = Relationship(back_populates="libros")
    libro: "Book" = Relationship(back_populates="promociones")

class PromotionCategory(SQLModel, table=True):
    __tablename__ = "promocion_categorias"
    
    promocion_id: int = Field(foreign_key="promociones.id", primary_key=True)
    categoria_id: int = Field(foreign_key="categorias.id", primary_key=True)
    
    # Relationships
    promocion: "Promotion" = Relationship(back_populates="categorias")
    categoria: "Category" = Relationship(back_populates="promociones")