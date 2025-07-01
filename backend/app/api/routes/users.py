# backend/app/api/routes/users.py - COMPLETO
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from passlib.context import CryptContext
from datetime import date

from app.db.session import get_session
from app.models import (
    User, UserCreate, UserRead, UserUpdate, UserRegister, UserLogin,
    TipoDocumento, Genero
)

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ===== FUNCIONES DE VALIDACIÓN =====
def hash_password(password: str) -> str:
    """Hash de contraseña"""
    return pwd_context.hash(password)

def validate_documento_peruano(tipo: TipoDocumento, numero: str) -> bool:
    """Validar formato de documentos peruanos"""
    numero = numero.replace("-", "").replace(" ", "")  # Limpiar formato
    
    if tipo == TipoDocumento.DNI:
        # DNI: 8 dígitos exactos
        return len(numero) == 8 and numero.isdigit()
    
    elif tipo == TipoDocumento.RUC:
        # RUC: 11 dígitos, empieza con 10, 15, 17, 20
        if len(numero) != 11 or not numero.isdigit():
            return False
        return numero.startswith(('10', '15', '17', '20'))
    
    elif tipo == TipoDocumento.CE:
        # CE: 9 dígitos (formato simplificado)
        return len(numero) == 9 and numero.isdigit()
    
    return False

def calculate_age(fecha_nacimiento: date) -> int:
    """Calcular edad desde fecha de nacimiento"""
    today = date.today()
    return today.year - fecha_nacimiento.year - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))

# ===== ENDPOINTS EXISTENTES (ACTUALIZADOS) =====

@router.get("/", response_model=List[UserRead])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(True),
    session: AsyncSession = Depends(get_session)
):
    """Obtener todos los usuarios (solo admin)"""
    try:
        query = select(User)
        if active_only:
            query = query.where(User.esta_activo == True)
        
        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        users = result.scalars().all()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, session: AsyncSession = Depends(get_session)):
    """Obtener un usuario específico"""
    try:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=UserRead)
async def create_user(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    """Crear un nuevo usuario (admin)"""
    try:
        # ✅ VALIDAR EMAIL ÚNICO
        existing_email = await session.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing_email.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Ya existe un usuario con este email")
        
        # ✅ VALIDAR DOCUMENTO ÚNICO
        existing_doc = await session.execute(
            select(User).where(User.numero_documento == user_data.numero_documento)
        )
        if existing_doc.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Ya existe un usuario con este número de documento")
        
        # ✅ VALIDAR FORMATO DE DOCUMENTO
        if not validate_documento_peruano(user_data.tipo_documento, user_data.numero_documento):
            raise HTTPException(status_code=400, detail=f"Formato de {user_data.tipo_documento} inválido")
        
        # ✅ VALIDAR EDAD MÍNIMA (opcional)
        if user_data.fecha_nacimiento:
            age = calculate_age(user_data.fecha_nacimiento)
            if age < 13:  # Edad mínima para registrarse
                raise HTTPException(status_code=400, detail="Debe ser mayor de 13 años para registrarse")
        
        # Crear usuario con contraseña hasheada
        user_dict = user_data.dict(exclude={"password"})
        user_dict["hashed_password"] = hash_password(user_data.password)
        
        user = User(**user_dict)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int, 
    user_data: UserUpdate, 
    session: AsyncSession = Depends(get_session)
):
    """Actualizar un usuario"""
    try:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await session.commit()
        await session.refresh(user)
        return user
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}")
async def delete_user(user_id: int, session: AsyncSession = Depends(get_session)):
    """Eliminar un usuario (soft delete)"""
    try:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        user.esta_activo = False
        await session.commit()
        return {"message": "Usuario eliminado exitosamente", "id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/email/{email}", response_model=UserRead)
async def get_user_by_email(email: str, session: AsyncSession = Depends(get_session)):
    """Obtener usuario por email"""
    try:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== NUEVOS ENDPOINTS =====

@router.post("/register", response_model=UserRead)
async def register_user(user_data: UserRegister, session: AsyncSession = Depends(get_session)):
    """Registro público de usuarios"""
    try:
        # Mismas validaciones que create_user
        existing_email = await session.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing_email.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Ya existe un usuario con este email")
        
        existing_doc = await session.execute(
            select(User).where(User.numero_documento == user_data.numero_documento)
        )
        if existing_doc.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Ya existe un usuario con este número de documento")
        
        if not validate_documento_peruano(user_data.tipo_documento, user_data.numero_documento):
            raise HTTPException(status_code=400, detail=f"Formato de {user_data.tipo_documento} inválido")
        
        if user_data.fecha_nacimiento:
            age = calculate_age(user_data.fecha_nacimiento)
            if age < 13:
                raise HTTPException(status_code=400, detail="Debe ser mayor de 13 años para registrarse")
        
        # Crear usuario (siempre rol cliente en registro público)
        user_dict = user_data.dict(exclude={"password"})
        user_dict["hashed_password"] = hash_password(user_data.password)
        user_dict["rol"] = "cliente"  # Forzar rol cliente
        
        user = User(**user_dict)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/document")
async def search_user_by_document(
    numero_documento: str = Query(..., description="Número de documento a buscar"),
    session: AsyncSession = Depends(get_session)
):
    """Buscar usuario por número de documento"""
    try:
        result = await session.execute(
            select(User).where(User.numero_documento == numero_documento)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return {
            "id": user.id,
            "nombre_completo": f"{user.nombre} {user.apellido}",
            "email": user.email,
            "tipo_documento": user.tipo_documento,
            "numero_documento": user.numero_documento,
            "esta_activo": user.esta_activo
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/demographics")
async def get_user_demographics(session: AsyncSession = Depends(get_session)):
    """Obtener estadísticas demográficas de usuarios"""
    try:
        # Total de usuarios activos
        total_result = await session.execute(
            select(User).where(User.esta_activo == True)
        )
        total_users = len(total_result.scalars().all())
        
        # Usuarios por género
        genero_result = await session.execute(
            select(User.genero, User.id).where(User.esta_activo == True)
        )
        users_by_gender = {}
        for user in genero_result.all():
            genero = user[0]
            if genero in users_by_gender:
                users_by_gender[genero] += 1
            else:
                users_by_gender[genero] = 1
        
        # Usuarios por tipo de documento
        doc_result = await session.execute(
            select(User.tipo_documento, User.id).where(User.esta_activo == True)
        )
        users_by_doc_type = {}
        for user in doc_result.all():
            doc_type = user[0]
            if doc_type in users_by_doc_type:
                users_by_doc_type[doc_type] += 1
            else:
                users_by_doc_type[doc_type] = 1
        
        return {
            "total_usuarios_activos": total_users,
            "por_genero": users_by_gender,
            "por_tipo_documento": users_by_doc_type
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validate/document")
async def validate_document_format(
    tipo_documento: TipoDocumento = Query(..., description="Tipo de documento"),
    numero_documento: str = Query(..., description="Número de documento")
):
    """Validar formato de documento peruano"""
    try:
        is_valid = validate_documento_peruano(tipo_documento, numero_documento)
        
        return {
            "tipo_documento": tipo_documento,
            "numero_documento": numero_documento,
            "es_valido": is_valid,
            "mensaje": "Formato válido" if is_valid else f"Formato de {tipo_documento} inválido"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/advanced")
async def advanced_user_search(
    nombre: Optional[str] = Query(None, description="Buscar por nombre"),
    apellido: Optional[str] = Query(None, description="Buscar por apellido"),
    email: Optional[str] = Query(None, description="Buscar por email"),
    tipo_documento: Optional[TipoDocumento] = Query(None, description="Filtrar por tipo de documento"),
    genero: Optional[Genero] = Query(None, description="Filtrar por género"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """Búsqueda avanzada de usuarios"""
    try:
        query = select(User).where(User.esta_activo == True)
        
        if nombre:
            query = query.where(User.nombre.ilike(f"%{nombre}%"))
        
        if apellido:
            query = query.where(User.apellido.ilike(f"%{apellido}%"))
        
        if email:
            query = query.where(User.email.ilike(f"%{email}%"))
        
        if tipo_documento:
            query = query.where(User.tipo_documento == tipo_documento)
        
        if genero:
            query = query.where(User.genero == genero)
        
        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        users = result.scalars().all()
        
        return [
            {
                "id": user.id,
                "nombre_completo": f"{user.nombre} {user.apellido}",
                "email": user.email,
                "tipo_documento": user.tipo_documento,
                "numero_documento": user.numero_documento,
                "genero": user.genero,
                "fecha_creacion": user.fecha_creacion
            }
            for user in users
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))