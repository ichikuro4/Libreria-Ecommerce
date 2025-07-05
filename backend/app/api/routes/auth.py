"""
Rutas de autenticación
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from app.db.session import get_session
from app.models import User, UserLogin, UserRegister, UserRead, TokenResponse, RefreshTokenRequest, ChangePasswordRequest
from app.core.security import (
    verify_password, get_password_hash, create_access_token, 
    create_refresh_token, verify_token, ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.core.deps import get_current_user, get_current_active_user

router = APIRouter()

@router.post("/register", response_model=UserRead)
async def register(user_data: UserRegister, session: AsyncSession = Depends(get_session)):
    """Registro de nuevos usuarios"""
    try:
        # Verificar email único
        existing_email = await session.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing_email.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un usuario con este email"
            )
        
        # Verificar documento único
        existing_doc = await session.execute(
            select(User).where(User.numero_documento == user_data.numero_documento)
        )
        if existing_doc.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un usuario con este número de documento"
            )
        
        # Crear usuario
        user_dict = user_data.dict(exclude={"password"})
        user_dict["hashed_password"] = get_password_hash(user_data.password)
        user_dict["rol"] = "cliente"  # Siempre cliente en registro público
        
        user = User(**user_dict)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@router.post("/login", response_model=TokenResponse)
async def login(user_credentials: UserLogin, session: AsyncSession = Depends(get_session)):
    """Iniciar sesión"""
    try:
        # Buscar usuario por email
        result = await session.execute(
            select(User).where(User.email == user_credentials.email)
        )
        user = result.scalar_one_or_none()
        
        # Verificar usuario y contraseña
        if not user or not verify_password(user_credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos"
            )
        
        if not user.esta_activo:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cuenta desactivada"
            )
        
        # Crear tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Actualizar última actividad
        user.fecha_ultima_actividad = datetime.now()
        await session.commit()
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserRead.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest, 
    session: AsyncSession = Depends(get_session)
):
    """Renovar token de acceso"""
    try:
        # Verificar refresh token
        token_data = verify_token(refresh_data.refresh_token, token_type="refresh")
        user_id = token_data["user_id"]
        
        # Buscar usuario
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user or not user.esta_activo:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no válido"
            )
        
        # Crear nuevos tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserRead.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresh inválido"
        )

@router.get("/me", response_model=UserRead)
async def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """Obtener perfil del usuario actual"""
    return current_user

@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Cambiar contraseña del usuario actual"""
    try:
        # Verificar contraseña actual
        if not verify_password(password_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contraseña actual incorrecta"
            )
        
        # Actualizar contraseña
        current_user.hashed_password = get_password_hash(password_data.new_password)
        await session.commit()
        
        return {"message": "Contraseña actualizada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@router.post("/logout")
async def logout():
    """Cerrar sesión (en frontend eliminar tokens)"""
    return {"message": "Sesión cerrada exitosamente"}