"""
Modelos relacionados con libros, autores, categorías y editoriales
"""

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

# Authors
class Author(SQLModel, table=True):
    __tablename__ = "autores"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre_completo: str = Field(max_length=200)
    biografia: Optional[str] = Field(default=None)
    url_imagen: Optional[str] = Field(default=None, max_length=255)
    fecha_nacimiento: Optional[date] = Field(default=None)
    nacionalidad: Optional[str] = Field(default=None, max_length=100)
    sitio_web: Optional[str] = Field(default=None, max_length=255)
    esta_activo: bool = Field(default=True)
    
    # Relationships
    libros: List["BookAuthor"] = Relationship(back_populates="autor")

class AuthorCreate(SQLModel):
    nombre_completo: str
    biografia: Optional[str] = None
    url_imagen: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    nacionalidad: Optional[str] = None
    sitio_web: Optional[str] = None

class AuthorRead(SQLModel):
    id: int
    nombre_completo: str
    biografia: Optional[str]
    url_imagen: Optional[str]
    fecha_nacimiento: Optional[date]
    nacionalidad: Optional[str]
    sitio_web: Optional[str]
    esta_activo: bool

class AuthorUpdate(SQLModel):
    nombre_completo: Optional[str] = None
    biografia: Optional[str] = None
    url_imagen: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    nacionalidad: Optional[str] = None
    sitio_web: Optional[str] = None

# Publishers
class Publisher(SQLModel, table=True):
    __tablename__ = "editoriales"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=150, unique=True)
    descripcion: Optional[str] = Field(default=None)
    url_logo: Optional[str] = Field(default=None, max_length=255)
    sitio_web: Optional[str] = Field(default=None, max_length=255)
    pais: Optional[str] = Field(default=None, max_length=100)
    esta_activa: bool = Field(default=True)
    
    # Relationships
    libros: List["Book"] = Relationship(back_populates="editorial")

class PublisherCreate(SQLModel):
    nombre: str
    descripcion: Optional[str] = None
    url_logo: Optional[str] = None
    sitio_web: Optional[str] = None
    pais: Optional[str] = None

class PublisherRead(SQLModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    url_logo: Optional[str]
    sitio_web: Optional[str]
    pais: Optional[str]
    esta_activa: bool

class PublisherUpdate(SQLModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    url_logo: Optional[str] = None
    sitio_web: Optional[str] = None
    pais: Optional[str] = None

# Categories
class Category(SQLModel, table=True):
    __tablename__ = "categorias"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100, unique=True)
    url_imagen: Optional[str] = Field(default=None, max_length=255)
    descripcion: Optional[str] = Field(default=None)
    categoria_padre_id: Optional[int] = Field(default=None, foreign_key="categorias.id")
    orden_display: int = Field(default=0)
    esta_activa: bool = Field(default=True)
    
    # Relationships
    categoria_padre: Optional["Category"] = Relationship(
        back_populates="subcategorias",
        sa_relationship_kwargs={"remote_side": "Category.id"}
    )
    subcategorias: List["Category"] = Relationship(back_populates="categoria_padre")
    libros: List["BookCategory"] = Relationship(back_populates="categoria")
    promociones: List["PromotionCategory"] = Relationship(back_populates="categoria")

class CategoryCreate(SQLModel):
    nombre: str
    url_imagen: Optional[str] = None
    descripcion: Optional[str] = None
    categoria_padre_id: Optional[int] = None
    orden_display: int = 0

class CategoryRead(SQLModel):
    id: int
    nombre: str
    url_imagen: Optional[str]
    descripcion: Optional[str]
    categoria_padre_id: Optional[int]
    orden_display: int
    esta_activa: bool

class CategoryUpdate(SQLModel):
    nombre: Optional[str] = None
    url_imagen: Optional[str] = None
    descripcion: Optional[str] = None
    categoria_padre_id: Optional[int] = None
    orden_display: Optional[int] = None

# Books
class Book(SQLModel, table=True):
    __tablename__ = "libros"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    sku: Optional[str] = Field(default=None, max_length=100, unique=True)
    titulo: str = Field(max_length=255)
    isbn: Optional[str] = Field(default=None, max_length=13, unique=True)
    descripcion: Optional[str] = Field(default=None)
    precio: Decimal = Field(ge=0, decimal_places=2)
    precio_original: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    stock: int = Field(default=0, ge=0)
    stock_minimo: int = Field(default=5)
    url_portada: Optional[str] = Field(default=None, max_length=255)
    imagenes_adicionales: Optional[str] = Field(default=None)  # JSON string
    editorial_id: Optional[int] = Field(default=None, foreign_key="editoriales.id")
    fecha_publicacion: Optional[date] = Field(default=None)
    numero_paginas: Optional[int] = Field(default=None)
    idioma: str = Field(default="español", max_length=50)
    peso_kg: Optional[Decimal] = Field(default=None, decimal_places=3)
    dimensiones: Optional[str] = Field(default=None, max_length=50)
    formato: Optional[str] = Field(default=None, max_length=50)
    esta_activo: bool = Field(default=True)
    es_destacado: bool = Field(default=False)
    es_nuevo: bool = Field(default=False)
    es_bestseller: bool = Field(default=False)
    fecha_creacion: Optional[datetime] = Field(default_factory=datetime.now)
    fecha_actualizacion: Optional[datetime] = Field(default_factory=datetime.now)
    vistas: int = Field(default=0)
    ventas_totales: int = Field(default=0)
    
    # Relationships
    editorial: Optional["Publisher"] = Relationship(back_populates="libros")
    autores: List["BookAuthor"] = Relationship(back_populates="libro")
    categorias: List["BookCategory"] = Relationship(back_populates="libro")
    resenas: List["Review"] = Relationship(back_populates="libro")
    lista_deseos: List["WishList"] = Relationship(back_populates="libro")
    promociones: List["PromotionBook"] = Relationship(back_populates="libro")

class BookCreate(SQLModel):
    sku: Optional[str] = None
    titulo: str
    isbn: Optional[str] = None
    descripcion: Optional[str] = None
    precio: Decimal
    precio_original: Optional[Decimal] = None
    stock: int = 0
    stock_minimo: int = 5
    url_portada: Optional[str] = None
    editorial_id: Optional[int] = None
    fecha_publicacion: Optional[date] = None
    numero_paginas: Optional[int] = None
    idioma: str = "español"
    peso_kg: Optional[Decimal] = None
    dimensiones: Optional[str] = None
    formato: Optional[str] = None

class BookRead(SQLModel):
    id: int
    sku: Optional[str]
    titulo: str
    isbn: Optional[str]
    descripcion: Optional[str]
    precio: Decimal
    precio_original: Optional[Decimal]
    stock: int
    stock_minimo: int
    url_portada: Optional[str]
    editorial_id: Optional[int]
    fecha_publicacion: Optional[date]
    numero_paginas: Optional[int]
    idioma: str
    peso_kg: Optional[Decimal]
    dimensiones: Optional[str]
    formato: Optional[str]
    esta_activo: bool
    es_destacado: bool
    es_nuevo: bool
    es_bestseller: bool
    fecha_creacion: Optional[datetime]
    vistas: int
    ventas_totales: int

class BookUpdate(SQLModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    precio: Optional[Decimal] = None
    precio_original: Optional[Decimal] = None
    stock: Optional[int] = None
    url_portada: Optional[str] = None
    editorial_id: Optional[int] = None
    es_destacado: Optional[bool] = None
    es_nuevo: Optional[bool] = None
    es_bestseller: Optional[bool] = None

# Junction Tables
class BookAuthor(SQLModel, table=True):
    __tablename__ = "libro_autor"
    
    libro_id: int = Field(foreign_key="libros.id", primary_key=True)
    autor_id: int = Field(foreign_key="autores.id", primary_key=True)
    orden: int = Field(default=1)
    
    # Relationships
    libro: "Book" = Relationship(back_populates="autores")
    autor: "Author" = Relationship(back_populates="libros")

class BookCategory(SQLModel, table=True):
    __tablename__ = "libro_categoria"
    
    libro_id: int = Field(foreign_key="libros.id", primary_key=True)
    categoria_id: int = Field(foreign_key="categorias.id", primary_key=True)
    
    # Relationships
    libro: "Book" = Relationship(back_populates="categorias")
    categoria: "Category" = Relationship(back_populates="libros")