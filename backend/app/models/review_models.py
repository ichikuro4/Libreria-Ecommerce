"""
Modelos relacionados con reseñas y lista de deseos
"""

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime

# Reviews
class Review(SQLModel, table=True):
    __tablename__ = "resenas"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    libro_id: int = Field(foreign_key="libros.id")
    usuario_id: int = Field(foreign_key="usuarios.id")
    puntuacion: int = Field(ge=1, le=5)
    titulo: Optional[str] = Field(default=None, max_length=255)
    comentario: Optional[str] = Field(default=None)
    fecha: Optional[datetime] = Field(default_factory=datetime.now)
    es_verificada: bool = Field(default=False)
    util_positivo: int = Field(default=0)
    util_negativo: int = Field(default=0)
    
    # Relationships
    libro: "Book" = Relationship(back_populates="resenas")
    usuario: "User" = Relationship(back_populates="resenas")

class ReviewCreate(SQLModel):
    libro_id: int
    puntuacion: int
    titulo: Optional[str] = None
    comentario: Optional[str] = None

class ReviewRead(SQLModel):
    id: int
    libro_id: int
    usuario_id: int
    puntuacion: int
    titulo: Optional[str]
    comentario: Optional[str]
    fecha: Optional[datetime]
    es_verificada: bool
    util_positivo: int
    util_negativo: int

class ReviewUpdate(SQLModel):
    puntuacion: Optional[int] = None
    titulo: Optional[str] = None
    comentario: Optional[str] = None

# WishList
class WishList(SQLModel, table=True):
    __tablename__ = "lista_deseos"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuarios.id")
    libro_id: int = Field(foreign_key="libros.id")
    fecha_agregado: Optional[datetime] = Field(default_factory=datetime.now)
    
    # Relationships
    usuario: "User" = Relationship(back_populates="lista_deseos")
    libro: "Book" = Relationship(back_populates="lista_deseos")

class WishListCreate(SQLModel):
    libro_id: int

class WishListRead(SQLModel):
    id: int
    usuario_id: int
    libro_id: int
    fecha_agregado: Optional[datetime]