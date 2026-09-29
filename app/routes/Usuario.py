from fastapi import APIRouter, Depends, HTTPException, Request, status
from datetime import datetime
from sqlalchemy.orm import Session
from app.security import get_password_hash
from passlib.context import CryptContext
from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/usuario",
    tags=["Usuario"],
    responses={404: {"description": "Not found"}},
)

def generar_id_usuario(db: Session) -> str:
    """Genera el siguiente ID con patrón: USU001, USU002, USU003..."""
    ultimo = (
        db.query(models.TUsuario)
        .order_by(models.TUsuario.id_usuario.desc())
        .first()
    )
    if ultimo is None:
        return "USU001"
    numero = int(ultimo.id_usuario[3:]) + 1  # "USU005" -> 5 -> 6
    return f"USU{numero:03d}"


@router.get("/", response_model=list[schemas.UsuarioGet])
def listar_usuarios(
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    usuarios = (
        db.query(models.TUsuario)
        .filter(models.TUsuario.fecha_eliminado == None)
        .all()
    )
    return usuarios


@router.post("/", response_model=schemas.UsuarioGet, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    request: Request,
    usuario_data: schemas.UsuarioCreate,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    # 1. Validar que el rol exista y no esté eliminado
    rol = (
        db.query(models.TRol)
        .filter(
            models.TRol.id_rol == usuario_data.id_rol,
            models.TRol.fecha_eliminado == None,
        )
        .first()
    )
    if not rol:
        raise HTTPException(status_code=404, detail="El rol especificado no existe")

    # 2. Validar nombre de usuario único
    usuario_existente = (
        db.query(models.TUsuario)
        .filter(models.TUsuario.usuario == usuario_data.usuario)
        .first()
    )
    if usuario_existente:
        raise HTTPException(status_code=400, detail="El Usuario ya está en uso")

    # 3. Validar email único
    correo_existente = (
        db.query(models.TUsuario)
        .filter(models.TUsuario.email == usuario_data.email)
        .first()
    )
    if correo_existente:
        raise HTTPException(status_code=400, detail="El correo electrónico ya está en uso")

    # 4. Generar ID automático (USU001, USU002...)
    nuevo_id = generar_id_usuario(db)

    # 5. Hashear la contraseña (NUNCA texto plano)
    password_hash = get_password_hash(usuario_data.password)

    nuevo_usuario = models.TUsuario(
        id_usuario=nuevo_id,
        id_rol=usuario_data.id_rol,
        nombre=usuario_data.nombre,
        apellido=usuario_data.apellido,
        usuario=usuario_data.usuario,
        password=password_hash,
        email=usuario_data.email,
        estado=usuario_data.estado,
    )

    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario