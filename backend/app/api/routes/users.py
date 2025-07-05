# backend/app/api/routes/users.py - CORREGIDO
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from passlib.context import CryptContext
from datetime import date

from app.db.session import get_session
from app.models import (
    User, UserCreate,UserCreateAdmin, UserRead, UserUpdate, UserRegister, UserLogin,
    TipoDocumento, Genero
)
# ✅ IMPORTAR DEPENDENCIAS DE AUTENTICACIÓN
from app.core.deps import get_current_user, require_admin, require_admin_or_owner

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ===== FUNCIONES DE VALIDACIÓN (sin cambios) =====
def hash_password(password: str) -> str:
    """Hash de contraseña"""
    return pwd_context.hash(password)

def validate_documento_peruano(tipo: TipoDocumento, numero: str) -> bool:
    """Validar formato de documentos peruanos"""
    numero = numero.replace("-", "").replace(" ", "")
    
    if tipo == TipoDocumento.DNI:
        return len(numero) == 8 and numero.isdigit()
    elif tipo == TipoDocumento.RUC:
        if len(numero) != 11 or not numero.isdigit():
            return False
        return numero.startswith(('10', '15', '17', '20'))
    elif tipo == TipoDocumento.CE:
        return len(numero) == 9 and numero.isdigit()
    
    return False

def calculate_age(fecha_nacimiento: date) -> int:
    """Calcular edad desde fecha de nacimiento"""
    today = date.today()
    return today.year - fecha_nacimiento.year - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))

# ===== ENDPOINTS CORREGIDOS CON PERMISOS =====

@router.get("/", response_model=List[UserRead])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(True),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)  # ✅ SOLO ADMIN
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
async def get_user(
    user_id: int, 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)  # ✅ VERIFICAR PERMISOS
):
    """Obtener un usuario específico"""
    try:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # ✅ VERIFICAR PERMISOS: Admin o el mismo usuario
        if current_user.rol != "admin" and current_user.id != user_id:
            raise HTTPException(status_code=403, detail="No tienes permisos para ver este usuario")
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=UserRead)
async def create_user(
    user_data: UserCreateAdmin,  # ✅ CAMBIAR A UserCreateAdmin
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Crear un nuevo usuario con rol específico (solo admin)"""
    try:
        # Validaciones existentes...
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
        
        # ✅ ADMIN PUEDE ESPECIFICAR CUALQUIER ROL
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
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)  # ✅ VERIFICAR PERMISOS
):
    """Actualizar un usuario"""
    try:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # ✅ VERIFICAR PERMISOS: Admin o el mismo usuario
        if current_user.rol != "admin" and current_user.id != user_id:
            raise HTTPException(status_code=403, detail="No tienes permisos para actualizar este usuario")
        
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
async def delete_user(
    user_id: int, 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)  # ✅ SOLO ADMIN
):
    """Eliminar un usuario (soft delete) - solo admin"""
    try:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # ✅ NO PERMITIR QUE EL ADMIN SE ELIMINE A SÍ MISMO
        if user_id == current_user.id:
            raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")
        
        user.esta_activo = False
        await session.commit()
        return {"message": "Usuario eliminado exitosamente", "id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/email/{email}", response_model=UserRead)
async def get_user_by_email(
    email: str, 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)  # ✅ SOLO ADMIN
):
    """Obtener usuario por email (solo admin)"""
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

# ===== ENDPOINTS DE BÚSQUEDA (CON PERMISOS) =====

@router.get("/search/document")
async def search_user_by_document(
    numero_documento: str = Query(..., description="Número de documento a buscar"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)  # ✅ SOLO ADMIN
):
    """Buscar usuario por número de documento (solo admin)"""
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
async def get_user_demographics(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)  # ✅ SOLO ADMIN
):
    """Obtener estadísticas demográficas de usuarios (solo admin)"""
    try:
        # Código sin cambios...
        total_result = await session.execute(
            select(User).where(User.esta_activo == True)
        )
        total_users = len(total_result.scalars().all())
        
        genero_result = await session.execute(
            select(User.genero, User.id).where(User.esta_activo == True)
        )
        users_by_gender = {}
        for user in genero_result.all():
            genero = user[0]
            users_by_gender[genero] = users_by_gender.get(genero, 0) + 1
        
        doc_result = await session.execute(
            select(User.tipo_documento, User.id).where(User.esta_activo == True)
        )
        users_by_doc_type = {}
        for user in doc_result.all():
            doc_type = user[0]
            users_by_doc_type[doc_type] = users_by_doc_type.get(doc_type, 0) + 1
        
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
    """Validar formato de documento peruano - PÚBLICO"""
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
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)  # ✅ SOLO ADMIN
):
    """Búsqueda avanzada de usuarios (solo admin)"""
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
                "fecha_creacion": user.fecha_creacion,
                "rol": user.rol  # ✅ INCLUIR ROL PARA ADMIN
            }
            for user in users
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))