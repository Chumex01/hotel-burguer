from fastapi import APIRouter, Depends, HTTPException, Request, status
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/rol",
    tags=["Rol"],
    responses={404: {"descripcion": "Not found"}},
)

SUPER_ADMIN = "ROL001"

@router.get("/", response_model=list[schemas.RolGet])
def listar_roles(
    db: Session = Depends(get_db),
    #current_user = models.TUsuario = Depends(get_current_user),
):
  roles = (
      db.query(models.TRol)
      .filter(models.TRol.fecha_eliminado == None)
      .all()
  )
  return roles  

@router.post("/", response_model=schemas.RolGet, status_code=status.HTTP_201_CREATED)
def crear_rol(
    request: Request,
    rol_data: schemas.RolCreate,
    db: Session = Depends(get_db),
    #current_user = models.TUsuario = Depends(get_current_user)
):
    existente = (
        db.query(models.TRol)
        .filter(models.TRol.id_rol == rol_data.id_rol)
        .first()
    )
    if existente:
        raise HTTPException(status_code=400, detail="El ID ya está en uso")
    
    nombre_existente = (
        db.query(models.TRol)
        .filter(models.TRol.nombre == rol_data.nombre)
        .first()
    )
    if nombre_existente:
        raise HTTPException(status_code=400, detail="El nombre del Rol ya está en uso")
    
    nuevo_rol = models.TRol(
        id_rol=rol_data.id_rol,
        nombre=rol_data.nombre,
        descripcion=rol_data.descripcion
    )
    
    db.add(nuevo_rol)
    db.flush()
    db.commit()
    db.refresh(nuevo_rol)
    return nuevo_rol