from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from passlib.context import CryptContext

from app.db.session import get_session
from app.models import User, UserCreate, UserRead, UserUpdate

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash de contraseña"""
    return pwd_context.hash(password)

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
    """Crear un nuevo usuario"""
    try:
        # Verificar si ya existe un usuario con el mismo email
        existing = await session.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Ya existe un usuario con este email")
        
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