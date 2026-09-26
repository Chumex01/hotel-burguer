from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/habitacion",
    tags=["Habitacion"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[schemas.HabitacionGet])
def listar_habitaciones(
    estado: schemas.ESTADOS_HABITACION | None = None,
    piso: int | None = None,
    id_tipo: int | None = None,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    """Filtros opcionales. Ej: /habitacion/?estado=Disponible para recepción."""
    query = db.query(models.THabitacion)

    if estado:
        query = query.filter(models.THabitacion.estado == estado)
    if piso is not None:
        query = query.filter(models.THabitacion.piso == piso)
    if id_tipo is not None:
        query = query.filter(models.THabitacion.id_tipo == id_tipo)

    return query.all()


@router.get("/{id_habitacion}", response_model=schemas.HabitacionGet)
def obtener_habitacion(
    id_habitacion: int,
    db: Session = Depends(get_db),
):
    habitacion = (
        db.query(models.THabitacion)
        .filter(models.THabitacion.id_habitacion == id_habitacion)
        .first()
    )
    if not habitacion:
        raise HTTPException(status_code=404, detail="Habitación no encontrada")
    return habitacion


@router.post("/", response_model=schemas.HabitacionGet, status_code=status.HTTP_201_CREATED)
def crear_habitacion(
    habitacion_data: schemas.HabitacionCreate,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    # 1. Validar que el tipo exista y esté activo
    tipo = (
        db.query(models.TTipoHabitacion)
        .filter(
            models.TTipoHabitacion.id_tipo == habitacion_data.id_tipo,
            models.TTipoHabitacion.fecha_eliminado == None,
        )
        .first()
    )
    if not tipo:
        raise HTTPException(status_code=404, detail="El tipo de habitación no existe o está eliminado")

    # 2. Validar número de habitación único
    numero_existente = (
        db.query(models.THabitacion)
        .filter(models.THabitacion.numero == habitacion_data.numero)
        .first()
    )
    if numero_existente:
        raise HTTPException(status_code=400, detail="Ya existe una habitación con ese número")

    nueva_habitacion = models.THabitacion(
        id_tipo=habitacion_data.id_tipo,
        numero=habitacion_data.numero,
        piso=habitacion_data.piso,
        estado=habitacion_data.estado,
    )

    db.add(nueva_habitacion)
    db.commit()
    db.refresh(nueva_habitacion)
    return nueva_habitacion


@router.put("/{id_habitacion}", response_model=schemas.HabitacionGet)
def actualizar_habitacion(
    id_habitacion: int,
    habitacion_data: schemas.HabitacionUpdate,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    habitacion = (
        db.query(models.THabitacion)
        .filter(models.THabitacion.id_habitacion == id_habitacion)
        .first()
    )
    if not habitacion:
        raise HTTPException(status_code=404, detail="Habitación no encontrada")

    datos = habitacion_data.model_dump(exclude_unset=True)

    # Si cambian el número, validar que no colisione con otra habitación
    if "numero" in datos and datos["numero"] != habitacion.numero:
        numero_existente = (
            db.query(models.THabitacion)
            .filter(
                models.THabitacion.numero == datos["numero"],
                models.THabitacion.id_habitacion != id_habitacion,
            )
            .first()
        )
        if numero_existente:
            raise HTTPException(status_code=400, detail="Ya existe una habitación con ese número")

    # Si cambian el tipo, validar que exista y esté activo
    if "id_tipo" in datos and datos["id_tipo"] != habitacion.id_tipo:
        tipo = (
            db.query(models.TTipoHabitacion)
            .filter(
                models.TTipoHabitacion.id_tipo == datos["id_tipo"],
                models.TTipoHabitacion.fecha_eliminado == None,
            )
            .first()
        )
        if not tipo:
            raise HTTPException(status_code=404, detail="El tipo de habitación no existe o está eliminado")

    for campo, valor in datos.items():
        setattr(habitacion, campo, valor)

    db.commit()
    db.refresh(habitacion)
    return habitacion


@router.patch("/{id_habitacion}/estado", response_model=schemas.HabitacionGet)
def cambiar_estado(
    id_habitacion: int,
    estado_data: schemas.HabitacionEstadoUpdate,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    """Cambio rápido de estado. Ej: limpieza terminó → /habitacion/5/estado {"estado": "Disponible"}"""
    habitacion = (
        db.query(models.THabitacion)
        .filter(models.THabitacion.id_habitacion == id_habitacion)
        .first()
    )
    if not habitacion:
        raise HTTPException(status_code=404, detail="Habitación no encontrada")

    habitacion.estado = estado_data.estado
    db.commit()
    db.refresh(habitacion)
    return habitacion


@router.delete("/{id_habitacion}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_habitacion(
    id_habitacion: int,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    habitacion = (
        db.query(models.THabitacion)
        .filter(models.THabitacion.id_habitacion == id_habitacion)
        .first()
    )
    if not habitacion:
        raise HTTPException(status_code=404, detail="Habitación no encontrada")

    # No eliminar si está ocupada (alguien durmiendo ahí 👀)
    if habitacion.estado == "Ocupada":
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar: la habitación está ocupada",
        )

    # No eliminar si tiene reservas (histórico o futuras)
    tiene_reservas = (
        db.query(models.TReserva)
        .filter(models.TReserva.id_habitacion == id_habitacion)
        .first()
    )
    if tiene_reservas:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar: la habitación tiene reservas asociadas",
        )

    db.delete(habitacion)
    db.commit()