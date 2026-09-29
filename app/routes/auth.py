# app/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app import models
from app.security import authenticate_user, create_access_token, get_current_active_user
from app.config import settings
from app.audit import create_audit_log

router = APIRouter(prefix="/auth", tags=["Autenticación"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "IP Desconocida"

@router.post("/login")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(), # La magia de Swagger
    db: Session = Depends(get_db),
):
    # 1. Autenticar al usuario (usamos .username que es lo que manda el formulario)
    user = authenticate_user(db, nombre=form_data.username, password=form_data.password, request=request)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Crear el Token JWT
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.nombre}, # Ajustado a tu PK
        expires_delta=access_token_expires,
    )

    # 3. Auditoría (Ajustada a los campos de TU función create_audit_log)
    create_audit_log(
        db=db,
        id_usuario=user.nombre, # Ajustado a tu modelo
        tabla="tusuarios",
        accion="LOGIN_EXITOSO",
        new_val={
            "ip_address": get_client_ip(request),
            # No guardes el token entero en la auditoría, es una mala práctica de seguridad
        },
    )
    db.commit()

    # 4. Devolver datos del usuario incluyendo el rol
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "nombre": user.nombre,     # Tu campo                  # Tu campo
            "id_rol": user.id_rol,                     # Tu campo
            "rol_nombre": user.rol.nombre if user.rol else "Sin rol desde el back", # Relación que añadimos
        },
    }


@router.post("/logout")
def logout(
    request: Request, # ✅ AÑADIDO para poder sacar la IP
    db: Session = Depends(get_db),
    current_user: models.TUsuario = Depends(get_current_active_user),
    token: str = Depends(oauth2_scheme),
):
    existe = db.query(models.TokenRevocado).filter(models.TokenRevocado.token == token).first()
    if not existe:
        token_revocado = models.TokenRevocado(token=token)
        db.add(token_revocado)
        
        # ✅ AUDITORÍA DEL LOGOUT
        create_audit_log(
            db=db, 
            id_usuario=current_user.nombre, 
            tabla="tusuarios", 
            accion="LOGOUT",
            ip=get_client_ip(request),
            user_agent=request.headers.get("user-agent")
        )
        
        db.commit()

    return {"mensaje": "Sesión cerrada exitosamente. Token invalidado."}