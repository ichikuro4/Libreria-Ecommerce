from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from enum import Enum

if TYPE_CHECKING:
    from .user import User

class BookStatus(str, Enum):
    AVAILABLE = "available"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"

# Tabla de asociación para autores y libros (many-to-many)
class BookAuthor(SQLModel, table=True):
    book_id: int = Field(foreign_key="book.id", primary_key=True)
    author_id: int = Field(foreign_key="author.id", primary_key=True)

# Modelo de Categoría
class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    description: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relaciones
    books: List["Book"] = Relationship(back_populates="category")

# Modelo de Autor
class Author(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200)
    biography: Optional[str] = Field(default=None)
    birth_date: Optional[datetime] = Field(default=None)
    nationality: Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relaciones many-to-many con libros
    books: List["Book"] = Relationship(back_populates="authors", link_model=BookAuthor)

# Modelo de Editorial
class Publisher(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200, unique=True)
    address: Optional[str] = Field(default=None)
    website: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relaciones
    books: List["Book"] = Relationship(back_populates="publisher")

# Modelo principal de Libro
class Book(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=300)
    isbn: Optional[str] = Field(default=None, max_length=13, unique=True)
    description: Optional[str] = Field(default=None)
    price: Decimal = Field(decimal_places=2, max_digits=10)
    pages: Optional[int] = Field(default=None, gt=0)
    publication_date: Optional[datetime] = Field(default=None)
    language: str = Field(default="Español", max_length=50)
    stock_quantity: int = Field(default=0, ge=0)
    status: BookStatus = Field(default=BookStatus.AVAILABLE)
    cover_image_url: Optional[str] = Field(default=None)
    weight: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=5)  # en gramos
    dimensions: Optional[str] = Field(default=None, max_length=100)  # ej: "20x15x2 cm"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Foreign keys
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")
    publisher_id: Optional[int] = Field(default=None, foreign_key="publisher.id")
    
    # Relaciones
    category: Optional[Category] = Relationship(back_populates="books")
    publisher: Optional[Publisher] = Relationship(back_populates="books")
    authors: List[Author] = Relationship(back_populates="books", link_model=BookAuthor)
    
    # Propiedades calculadas
    @property
    def is_available(self) -> bool:
        return self.status == BookStatus.AVAILABLE and self.stock_quantity > 0