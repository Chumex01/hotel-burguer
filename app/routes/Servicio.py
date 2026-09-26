from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/servicio",
    tags=["Servicio"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[schemas.ServicioGet])
def listar_servicios(
    estado: schemas.ESTADO_SERVICIO | None = None,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    """Filtro opcional. Ej: /servicio/?estado=Activo para el menú de recepción."""
    query = db.query(models.TServicio).filter(
        models.TServicio.fecha_eliminado == None
    )

    if estado:
        query = query.filter(models.TServicio.estado == estado)

    return query.all()


@router.get("/{id_servicio}", response_model=schemas.ServicioGet)
def obtener_servicio(
    id_servicio: int,
    db: Session = Depends(get_db),
):
    servicio = (
        db.query(models.TServicio)
        .filter(
            models.TServicio.id_servicio == id_servicio,
            models.TServicio.fecha_eliminado == None,
        )
        .first()
    )
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return servicio


@router.post("/", response_model=schemas.ServicioGet, status_code=status.HTTP_201_CREATED)
def crear_servicio(
    servicio_data: schemas.ServicioCreate,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    nombre_existente = (
        db.query(models.TServicio)
        .filter(
            models.TServicio.nombre == servicio_data.nombre,
            models.TServicio.fecha_eliminado == None,
        )
        .first()
    )
    if nombre_existente:
        raise HTTPException(status_code=400, detail="Ya existe un servicio con ese nombre")

    nuevo_servicio = models.TServicio(
        nombre=servicio_data.nombre,
        descripcion=servicio_data.descripcion,
        precio=servicio_data.precio,
        estado="Activo",
    )

    db.add(nuevo_servicio)
    db.commit()
    db.refresh(nuevo_servicio)
    return nuevo_servicio


@router.put("/{id_servicio}", response_model=schemas.ServicioGet)
def actualizar_servicio(
    id_servicio: int,
    servicio_data: schemas.ServicioUpdate,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    servicio = (
        db.query(models.TServicio)
        .filter(
            models.TServicio.id_servicio == id_servicio,
            models.TServicio.fecha_eliminado == None,
        )
        .first()
    )
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    datos = servicio_data.model_dump(exclude_unset=True)

    # Si cambian el nombre, validar que no colisione con otro servicio activo
    if "nombre" in datos and datos["nombre"] != servicio.nombre:
        nombre_existente = (
            db.query(models.TServicio)
            .filter(
                models.TServicio.nombre == datos["nombre"],
                models.TServicio.id_servicio != id_servicio,
                models.TServicio.fecha_eliminado == None,
            )
            .first()
        )
        if nombre_existente:
            raise HTTPException(status_code=400, detail="Ya existe un servicio con ese nombre")

    for campo, valor in datos.items():
        setattr(servicio, campo, valor)

    db.commit()
    db.refresh(servicio)
    return servicio


@router.patch("/{id_servicio}/estado", response_model=schemas.ServicioGet)
def cambiar_estado_servicio(
    id_servicio: int,
    estado_data: schemas.ServicioEstadoUpdate,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    """Desactivar/activar sin eliminar. Ej: temporada baja → piscina Inactiva."""
    servicio = (
        db.query(models.TServicio)
        .filter(
            models.TServicio.id_servicio == id_servicio,
            models.TServicio.fecha_eliminado == None,
        )
        .first()
    )
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    servicio.estado = estado_data.estado
    db.commit()
    db.refresh(servicio)
    return servicio


@router.delete("/{id_servicio}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_servicio(
    id_servicio: int,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    """Borrado LÓGICO. Las reservas antiguas conservan su historial gracias a precio_unitario."""
    servicio = (
        db.query(models.TServicio)
        .filter(
            models.TServicio.id_servicio == id_servicio,
            models.TServicio.fecha_eliminado == None,
        )
        .first()
    )
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    servicio.fecha_eliminado = datetime.now()
    servicio.estado = "Inactivo"  # por si acaso, queda doblemente fuera de circulación
    db.commit()