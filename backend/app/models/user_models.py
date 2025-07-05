"""
Modelos relacionados con usuarios y direcciones
"""

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional,List
from datetime import datetime, date
from .base import UserRole, TipoDocumento, Genero

# ===== USUARIOS =====
class User(SQLModel, table=True):
    __tablename__ = "usuarios"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Información personal básica
    nombre: str = Field(max_length=100)
    apellido: str = Field(max_length=100)
    email: str = Field(max_length=255, unique=True, index=True)
    hashed_password: str = Field(max_length=255)
    telefono: Optional[str] = Field(default=None, max_length=20)
    
    # ✅ NUEVOS CAMPOS PERUANOS
    tipo_documento: TipoDocumento = Field(default=TipoDocumento.DNI)
    numero_documento: str = Field(max_length=20, unique=True, index=True)
    fecha_nacimiento: Optional[date] = Field(default=None)
    genero: Genero = Field(default=Genero.NO_ESPECIFICADO)
    
    # Configuración de cuenta
    rol: UserRole = Field(default=UserRole.CUSTOMER)
    acepta_marketing: bool = Field(default=False)
    fecha_ultima_actividad: Optional[datetime] = Field(default=None)
    esta_activo: bool = Field(default=True)
    fecha_verificacion_email: Optional[datetime] = Field(default=None)
    fecha_creacion: Optional[datetime] = Field(default_factory=datetime.now)
    
    # ✅ TODAS LAS RELACIONES
    pedidos: List["Order"] = Relationship(back_populates="usuario")
    direcciones: List["Address"] = Relationship(back_populates="usuario")
    resenas: List["Review"] = Relationship(back_populates="usuario")
    lista_deseos: List["WishList"] = Relationship(back_populates="usuario")

class UserCreate(SQLModel):
    nombre: str
    apellido: str
    email: str
    password: str = Field(min_length=8)
    telefono: Optional[str] = None
    # ✅ NUEVOS CAMPOS OBLIGATORIOS
    tipo_documento: TipoDocumento
    numero_documento: str = Field(min_length=8, max_length=20)
    fecha_nacimiento: Optional[date] = None
    genero: Genero = Genero.NO_ESPECIFICADO
    acepta_marketing: bool = False

class UserRead(SQLModel):
    id: int
    nombre: str
    apellido: str
    email: str
    telefono: Optional[str]
    # ✅ INCLUIR NUEVOS CAMPOS EN RESPUESTA
    tipo_documento: TipoDocumento
    numero_documento: str
    fecha_nacimiento: Optional[date]
    genero: Genero
    rol: UserRole
    acepta_marketing: bool
    esta_activo: bool
    fecha_creacion: Optional[datetime]
    fecha_verificacion_email: Optional[datetime]

class UserUpdate(SQLModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    telefono: Optional[str] = None
    # ✅ PERMITIR ACTUALIZAR NUEVOS CAMPOS
    fecha_nacimiento: Optional[date] = None
    genero: Optional[Genero] = None
    acepta_marketing: Optional[bool] = None

# Modelo para cambio de contraseña
class UserChangePassword(SQLModel):
    current_password: str
    new_password: str = Field(min_length=8)

# Modelo para registro público (sin algunos campos sensibles)
class UserRegister(SQLModel):
    nombre: str
    apellido: str
    email: str
    password: str = Field(min_length=8)
    telefono: Optional[str] = None
    tipo_documento: TipoDocumento
    numero_documento: str = Field(min_length=8, max_length=20)
    fecha_nacimiento: Optional[date] = None
    genero: Genero = Genero.NO_ESPECIFICADO
    acepta_marketing: bool = False

# Modelo para login
class UserLogin(SQLModel):
    email: str
    password: str

# ===== DIRECCIONES =====
class Address(SQLModel, table=True):
    __tablename__ = "direcciones"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuarios.id")
    nombre_contacto: str = Field(max_length=100)
    telefono: Optional[str] = Field(default=None, max_length=20)
    direccion_linea1: str = Field(max_length=255)
    direccion_linea2: Optional[str] = Field(default=None, max_length=255)
    ciudad: str = Field(max_length=100)
    provincia: str = Field(max_length=100)
    codigo_postal: str = Field(max_length=20)
    pais: str = Field(default="Perú", max_length=100)
    es_predeterminada: bool = Field(default=False)
    tipo: str = Field(default="envio", max_length=50)  # 'envio', 'facturacion'
    
    # Relationships
    usuario: "User" = Relationship(back_populates="direcciones")

class AddressCreate(SQLModel):
    nombre_contacto: str
    telefono: Optional[str] = None
    direccion_linea1: str
    direccion_linea2: Optional[str] = None
    ciudad: str
    provincia: str
    codigo_postal: str
    pais: str = "Perú"
    es_predeterminada: bool = False
    tipo: str = "envio"

class AddressRead(SQLModel):
    id: int
    usuario_id: int
    nombre_contacto: str
    telefono: Optional[str]
    direccion_linea1: str
    direccion_linea2: Optional[str]
    ciudad: str
    provincia: str
    codigo_postal: str
    pais: str
    es_predeterminada: bool
    tipo: str

class AddressUpdate(SQLModel):
    nombre_contacto: Optional[str] = None
    telefono: Optional[str] = None
    direccion_linea1: Optional[str] = None
    direccion_linea2: Optional[str] = None
    ciudad: Optional[str] = None
    provincia: Optional[str] = None
    codigo_postal: Optional[str] = None
    es_predeterminada: Optional[bool] = None
    tipo: Optional[str] = None

# Modelo para respuesta de login
class TokenResponse(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos
    user: UserRead

# Modelo para refresh token
class RefreshTokenRequest(SQLModel):
    refresh_token: str

# Modelo para cambio de contraseña
class ChangePasswordRequest(SQLModel):
    current_password: str
    new_password: str = Field(min_length=8)