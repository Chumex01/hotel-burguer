from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/tipo-habitacion",
    tags=["TipoHabitacion"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[schemas.TipoHabitacionGet])
def listar_tipos_habitacion(
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    tipos = (
        db.query(models.TTipoHabitacion)
        .filter(models.TTipoHabitacion.fecha_eliminado == None)
        .all()
    )
    return tipos


@router.get("/{id_tipo}", response_model=schemas.TipoHabitacionGet)
def obtener_tipo_habitacion(
    id_tipo: int,
    db: Session = Depends(get_db),
):
    tipo = (
        db.query(models.TTipoHabitacion)
        .filter(
            models.TTipoHabitacion.id_tipo == id_tipo,
            models.TTipoHabitacion.fecha_eliminado == None,
        )
        .first()
    )
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de habitación no encontrado")
    return tipo


@router.post("/", response_model=schemas.TipoHabitacionGet, status_code=status.HTTP_201_CREATED)
def crear_tipo_habitacion(
    tipo_data: schemas.TipoHabitacionCreate,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    # Validar nombre único entre los tipos ACTIVOS
    # (un tipo eliminado lógicamente no bloquea reutilizar su nombre)
    nombre_existente = (
        db.query(models.TTipoHabitacion)
        .filter(
            models.TTipoHabitacion.nombre == tipo_data.nombre,
            models.TTipoHabitacion.fecha_eliminado == None,
        )
        .first()
    )
    if nombre_existente:
        raise HTTPException(status_code=400, detail="Ya existe un tipo de habitación con ese nombre")

    nuevo_tipo = models.TTipoHabitacion(
        nombre=tipo_data.nombre,
        descripcion=tipo_data.descripcion,
        capacidad=tipo_data.capacidad,
        precio_noche=tipo_data.precio_noche,
    )

    db.add(nuevo_tipo)
    db.commit()
    db.refresh(nuevo_tipo)
    return nuevo_tipo


@router.put("/{id_tipo}", response_model=schemas.TipoHabitacionGet)
def actualizar_tipo_habitacion(
    id_tipo: int,
    tipo_data: schemas.TipoHabitacionUpdate,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    tipo = (
        db.query(models.TTipoHabitacion)
        .filter(
            models.TTipoHabitacion.id_tipo == id_tipo,
            models.TTipoHabitacion.fecha_eliminado == None,
        )
        .first()
    )
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de habitación no encontrado")

    datos = tipo_data.model_dump(exclude_unset=True)

    # Si cambian el nombre, validar que no colisione con otro tipo activo
    if "nombre" in datos and datos["nombre"] != tipo.nombre:
        nombre_existente = (
            db.query(models.TTipoHabitacion)
            .filter(
                models.TTipoHabitacion.nombre == datos["nombre"],
                models.TTipoHabitacion.id_tipo != id_tipo,
                models.TTipoHabitacion.fecha_eliminado == None,
            )
            .first()
        )
        if nombre_existente:
            raise HTTPException(status_code=400, detail="Ya existe un tipo de habitación con ese nombre")

    for campo, valor in datos.items():
        setattr(tipo, campo, valor)

    db.commit()
    db.refresh(tipo)
    return tipo


@router.delete("/{id_tipo}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_tipo_habitacion(
    id_tipo: int,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    tipo = (
        db.query(models.TTipoHabitacion)
        .filter(
            models.TTipoHabitacion.id_tipo == id_tipo,
            models.TTipoHabitacion.fecha_eliminado == None,
        )
        .first()
    )
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de habitación no encontrado")


    tiene_habitaciones = (
        db.query(models.THabitacion)
        .filter(
            models.THabitacion.id_tipo == id_tipo,
            models.THabitacion.estado != "Mantenimiento",  # o simplemente todas
        )
        .first()
    )
    if tiene_habitaciones:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar: el tipo tiene habitaciones asociadas",
        )

    tipo.fecha_eliminado = datetime.now()
    db.commit()