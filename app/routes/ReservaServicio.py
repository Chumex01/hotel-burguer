from fastapi import APIRouter, Depends, HTTPException, status
from decimal import Decimal
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/reserva-servicio",
    tags=["ReservaServicio"],
    responses={404: {"description": "Not found"}},
)

# Estados en los que la reserva aún puede consumir/modificar consumos
ESTADOS_CONSUMO = ["Pendiente", "Confirmada", "Check-in"]


@router.get("/", response_model=list[schemas.ReservaServicioConServicioGet])
def listar_consumos(
    id_reserva: int,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    """Todos los consumos de una reserva. Ej: /reserva-servicio/?id_reserva=15"""
    return (
        db.query(models.TReservaServicio)
        .filter(models.TReservaServicio.id_reserva == id_reserva)
        .order_by(models.TReservaServicio.fecha)
        .all()
    )


# ⚠️ Declarar ANTES de /{id_reserva_servicio}
@router.get("/cuenta", response_model=schemas.CuentaReservaGet)
def obtener_cuenta(
    id_reserva: int,
    db: Session = Depends(get_db),
):
    """El 'ticket': línea por línea + total. Lo que se muestra en el check-out."""
    reserva = (
        db.query(models.TReserva)
        .filter(models.TReserva.id_reserva == id_reserva)
        .first()
    )
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    detalle = (
        db.query(models.TReservaServicio)
        .filter(models.TReservaServicio.id_reserva == id_reserva)
        .order_by(models.TReservaServicio.fecha)
        .all()
    )

    total_servicios = sum(
        (rs.cantidad * rs.precio_unitario for rs in detalle),
        start=Decimal("0.00"),
    )

    return {
        "id_reserva": reserva.id_reserva,
        "estado_reserva": reserva.estado,
        "detalle": detalle,
        "total_servicios": total_servicios,
    }


@router.post(
    "/",
    response_model=schemas.ReservaServicioConServicioGet,
    status_code=status.HTTP_201_CREATED,
)
def agregar_consumo(
    consumo_data: schemas.ReservaServicioCreate,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    # 1. Validar que la reserva exista y esté en estado de consumo
    reserva = (
        db.query(models.TReserva)
        .filter(models.TReserva.id_reserva == consumo_data.id_reserva)
        .first()
    )
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    if reserva.estado not in ESTADOS_CONSUMO:
        raise HTTPException(
            status_code=400,
            detail=f"No se pueden agregar servicios a una reserva en estado {reserva.estado}",
        )

    # 2. Validar que el servicio exista, esté activo y no eliminado
    servicio = (
        db.query(models.TServicio)
        .filter(
            models.TServicio.id_servicio == consumo_data.id_servicio,
            models.TServicio.estado == "Activo",
            models.TServicio.fecha_eliminado == None,
        )
        .first()
    )
    if not servicio:
        raise HTTPException(
            status_code=404,
            detail="El servicio no existe, está inactivo o eliminado",
        )

    # 3. 🎯 Congelar el precio VIGENTE del catálogo en este instante
    nuevo_consumo = models.TReservaServicio(
        id_reserva=consumo_data.id_reserva,
        id_servicio=consumo_data.id_servicio,
        cantidad=consumo_data.cantidad,
        precio_unitario=servicio.precio,  # ⬅️ acá ocurre la magia
        observacion=consumo_data.observacion,
    )

    db.add(nuevo_consumo)
    db.commit()
    db.refresh(nuevo_consumo)
    return nuevo_consumo


@router.put("/{id_reserva_servicio}", response_model=schemas.ReservaServicioConServicioGet)
def actualizar_consumo(
    id_reserva_servicio: int,
    consumo_data: schemas.ReservaServicioUpdate,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    consumo = (
        db.query(models.TReservaServicio)
        .filter(models.TReservaServicio.id_reserva_servicio == id_reserva_servicio)
        .first()
    )
    if not consumo:
        raise HTTPException(status_code=404, detail="Consumo no encontrado")

    # No se toca la cuenta de una reserva cerrada
    if consumo.reserva.estado not in ESTADOS_CONSUMO:
        raise HTTPException(
            status_code=400,
            detail=f"La reserva está en estado {consumo.reserva.estado}, no admite modificaciones",
        )

    datos = consumo_data.model_dump(exclude_unset=True)
    for campo, valor in datos.items():
        setattr(consumo, campo, valor)

    db.commit()
    db.refresh(consumo)
    return consumo


@router.delete("/{id_reserva_servicio}", status_code=status.HTTP_204_NO_CONTENT)
def anular_consumo(
    id_reserva_servicio: int,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    """Quita una línea de la cuenta. Solo si la reserva sigue abierta."""
    consumo = (
        db.query(models.TReservaServicio)
        .filter(models.TReservaServicio.id_reserva_servicio == id_reserva_servicio)
        .first()
    )
    if not consumo:
        raise HTTPException(status_code=404, detail="Consumo no encontrado")

    if consumo.reserva.estado not in ESTADOS_CONSUMO:
        raise HTTPException(
            status_code=400,
            detail=f"La reserva está en estado {consumo.reserva.estado}, no admite modificaciones",
        )

    db.delete(consumo)
    db.commit()