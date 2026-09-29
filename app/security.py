from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app import models
from app.audit import create_audit_log

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# --- FUNCIONES DE PASSWORD ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def get_password_hash(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


# --- TOKEN ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# --- AUTHENTICATE CON AUDITORÍA (adaptado al hotel) ---
def authenticate_user(db: Session, nombre: str, password: str, request: Request):
    user = (
        db.query(models.TUsuario)
        .filter(models.TUsuario.usuario == nombre)   # ✅ columna del hotel
        .first()
    )

    client_ip = request.client.host if request.client else "Desconocida"
    user_agent = request.headers.get("user-agent", "Desconocido")

    if not user:
        create_audit_log(
            db=db, id_usuario="NO_EXISTE", tabla="tusuarios",
            accion="INTENTO_LOGIN_FALLIDO",
            new_val={"motivo": "Usuario no encontrado", "nombre_intentado": nombre},
            ip=client_ip, user_agent=user_agent,
        )
        return False

    if not verify_password(password, user.password):   # ✅ 'password', no 'clave'
        create_audit_log(
            db=db, id_usuario=user.id_usuario, tabla="tusuarios",
            accion="INTENTO_LOGIN_FALLIDO",
            new_val={"motivo": "Contraseña incorrecta"},
            ip=client_ip, user_agent=user_agent,
        )
        return False

    if user.fecha_eliminado is not None or user.estado != "Activo":
        create_audit_log(
            db=db, id_usuario=user.id_usuario, tabla="tusuarios",
            accion="INTENTO_LOGIN_FALLIDO",
            new_val={"motivo": "Usuario inactivo o eliminado"},
            ip=client_ip, user_agent=user_agent,
        )
        return False

    create_audit_log(
        db=db, id_usuario=user.id_usuario, tabla="tusuarios",
        accion="LOGIN_EXITOSO",
        ip=client_ip, user_agent=user_agent,
    )
    return user


# --- OBTENER USUARIO ACTUAL (adaptado: PK es id_usuario) ---
async def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        nombre: str = payload.get("sub")
        if nombre is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.TUsuario).filter(models.TUsuario.nombre == nombre).first()
    if user is None:
        raise credentials_exception
        
    token_revocado = db.query(models.TokenRevocado).filter(models.TokenRevocado.token == token).first()
    if token_revocado:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido. Sesión cerrada previamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# --- VERIFICAR SI ESTÁ ACTIVO ---
async def get_current_active_user(
    current_user: models.TUsuario = Depends(get_current_user),
):
    if current_user.fecha_eliminado is not None or current_user.estado != "Activo":
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user