from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.routes.Pago import calcular_cuenta

router = APIRouter(
    prefix="/reserva",
    tags=["Reserva"],
    responses={404: {"description": "Not found"}},
)

# Estados que BLOQUEAN la habitación (no libera las fechas)
ESTADOS_ACTIVOS = ["Pendiente", "Confirmada", "Check-in"]


def validar_disponibilidad(
    db: Session,
    id_habitacion: int,
    fecha_entrada: datetime,
    fecha_salida: datetime,
    excluir_id_reserva: int | None = None,
) -> None:
    """
    Dos rangos [A, B) se solapan si: entrada_existente < salida_nueva
    AND salida_existente > entrada_nueva.
    """
    query = (
        db.query(models.TReserva)
        .filter(
            models.TReserva.id_habitacion == id_habitacion,
            models.TReserva.estado.in_(ESTADOS_ACTIVOS),
            models.TReserva.fecha_entrada < fecha_salida,
            models.TReserva.fecha_salida > fecha_entrada,
        )
    )
    if excluir_id_reserva:  # al editar, no compararse consigo misma
        query = query.filter(models.TReserva.id_reserva != excluir_id_reserva)

    if query.first():
        raise HTTPException(
            status_code=400,
            detail="La habitación ya tiene una reserva que se cruza con esas fechas",
        )


@router.get("/", response_model=list[schemas.ReservaGet])
def listar_reservas(
    estado: schemas.ESTADOS_RESERVA | None = None,
    id_huesped: int | None = None,
    id_habitacion: int | None = None,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    query = db.query(models.TReserva)

    if estado:
        query = query.filter(models.TReserva.estado == estado)
    if id_huesped is not None:
        query = query.filter(models.TReserva.id_huesped == id_huesped)
    if id_habitacion is not None:
        query = query.filter(models.TReserva.id_habitacion == id_habitacion)

    return query.order_by(models.TReserva.fecha_entrada).all()


@router.get("/{id_reserva}", response_model=schemas.ReservaDetalleGet)
def obtener_reserva(
    id_reserva: int,
    db: Session = Depends(get_db),
):
    reserva = (
        db.query(models.TReserva)
        .filter(models.TReserva.id_reserva == id_reserva)
        .first()
    )
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    # --- Cálculos de la cuenta ---
    noches = (reserva.fecha_salida.date() - reserva.fecha_entrada.date()).days

    total_habitacion = reserva.habitacion.tipo_habitacion.precio_noche * noches

    total_servicios = sum(
        rs.cantidad * rs.precio_unitario for rs in reserva.reserva_servicios
    ) or Decimal("0.00")

    total_pagado = sum(pago.monto for pago in reserva.pagos) or Decimal("0.00")

    return {
        **reserva.__dict__,
        "huesped": reserva.huesped,
        "habitacion": reserva.habitacion,
        "noches": noches,
        "total_habitacion": total_habitacion,
        "total_servicios": total_servicios,
        "total_pagado": total_pagado,
        "saldo": total_habitacion + total_servicios - total_pagado,
    }


@router.post("/", response_model=schemas.ReservaGet, status_code=status.HTTP_201_CREATED)
def crear_reserva(
    reserva_data: schemas.ReservaCreate,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    # 1. Validar que el huésped exista
    huesped = (
        db.query(models.THuesped)
        .filter(models.THuesped.id_huesped == reserva_data.id_huesped)
        .first()
    )
    if not huesped:
        raise HTTPException(status_code=404, detail="El huésped no existe")

    # 2. Validar que la habitación exista
    habitacion = (
        db.query(models.THabitacion)
        .filter(models.THabitacion.id_habitacion == reserva_data.id_habitacion)
        .first()
    )
    if not habitacion:
        raise HTTPException(status_code=404, detail="La habitación no existe")

    # 3. Validar fechas coherentes
    if reserva_data.fecha_salida <= reserva_data.fecha_entrada:
        raise HTTPException(
            status_code=400,
            detail="La fecha de salida debe ser posterior a la fecha de entrada",
        )
    # Descomenta cuando pases a producción (molesta para pruebas con fechas viejas):
    # if reserva_data.fecha_entrada.date() < datetime.now().date():
    #     raise HTTPException(status_code=400, detail="La fecha de entrada no puede ser en el pasado")

    # 4. Validar capacidad del tipo de habitación
    tipo = habitacion.tipo_habitacion
    if reserva_data.cantidad_personas > tipo.capacidad:
        raise HTTPException(
            status_code=400,
            detail=f"La habitación admite máximo {tipo.capacidad} personas "
                   f"(solicitaste {reserva_data.cantidad_personas})",
        )

    # 5. Validar que no se cruce con otra reserva activa
    validar_disponibilidad(
        db,
        reserva_data.id_habitacion,
        reserva_data.fecha_entrada,
        reserva_data.fecha_salida,
    )

    # 6. Validar que la habitación no esté en Mantenimiento
    if habitacion.estado == "Mantenimiento":
        raise HTTPException(
            status_code=400,
            detail="La habitación está en mantenimiento, no admite reservas",
        )

    nueva_reserva = models.TReserva(
        id_huesped=reserva_data.id_huesped,
        id_habitacion=reserva_data.id_habitacion,
        id_usuario="USU001",  # ⚠️ reemplazar por current_user.id_usuario cuando actives JWT
        fecha_entrada=reserva_data.fecha_entrada,
        fecha_salida=reserva_data.fecha_salida,
        cantidad_personas=reserva_data.cantidad_personas,
        estado=reserva_data.estado,
        observaciones=reserva_data.observaciones,
    )

    db.add(nueva_reserva)
    db.commit()
    db.refresh(nueva_reserva)
    return nueva_reserva


@router.put("/{id_reserva}", response_model=schemas.ReservaGet)
def actualizar_reserva(
    id_reserva: int,
    reserva_data: schemas.ReservaUpdate,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    reserva = (
        db.query(models.TReserva)
        .filter(models.TReserva.id_reserva == id_reserva)
        .first()
    )
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    if reserva.estado in ["Check-out", "Cancelada"]:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede modificar una reserva en estado {reserva.estado}",
        )

    datos = reserva_data.model_dump(exclude_unset=True)

    # Validar combinación final de fechas/habitación (lo que queda tras el update)
    fecha_entrada = datos.get("fecha_entrada", reserva.fecha_entrada)
    fecha_salida = datos.get("fecha_salida", reserva.fecha_salida)
    id_habitacion = datos.get("id_habitacion", reserva.id_habitacion)

    if fecha_salida <= fecha_entrada:
        raise HTTPException(
            status_code=400,
            detail="La fecha de salida debe ser posterior a la fecha de entrada",
        )

    # Si cambia habitación o fechas, re-validar disponibilidad
    if (
        id_habitacion != reserva.id_habitacion
        or fecha_entrada != reserva.fecha_entrada
        or fecha_salida != reserva.fecha_salida
    ):
        validar_disponibilidad(
            db, id_habitacion, fecha_entrada, fecha_salida,
            excluir_id_reserva=id_reserva,
        )

    # Si cambia la cantidad de personas, re-validar capacidad
    if "cantidad_personas" in datos:
        habitacion = db.query(models.THabitacion).get(id_habitacion)
        if datos["cantidad_personas"] > habitacion.tipo_habitacion.capacidad:
            raise HTTPException(
                status_code=400,
                detail=f"La habitación admite máximo {habitacion.tipo_habitacion.capacidad} personas",
            )

    for campo, valor in datos.items():
        setattr(reserva, campo, valor)

    db.commit()
    db.refresh(reserva)
    return reserva


@router.patch("/{id_reserva}/check-in", response_model=schemas.ReservaGet)
def hacer_check_in(
    id_reserva: int,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    """Check-in: reserva → Check-in, habitación → Ocupada."""
    reserva = (
        db.query(models.TReserva)
        .filter(models.TReserva.id_reserva == id_reserva)
        .first()
    )
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    if reserva.estado not in ["Pendiente", "Confirmada"]:
        raise HTTPException(
            status_code=400,
            detail=f"Solo se puede hacer check-in desde Pendiente o Confirmada (estado actual: {reserva.estado})",
        )

    reserva.estado = "Check-in"
    reserva.habitacion.estado = "Ocupada"  # 🎯 la magia: relationship al poder

    db.commit()
    db.refresh(reserva)
    return reserva


@router.patch("/{id_reserva}/check-out", response_model=schemas.ReservaGet)
def hacer_check_out(
    id_reserva: int,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    """Check-out: reserva → Check-out, habitación → Limpieza."""
    reserva = (
        db.query(models.TReserva)
        .filter(models.TReserva.id_reserva == id_reserva)
        .first()
    )
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    if reserva.estado != "Check-in":
        raise HTTPException(
            status_code=400,
            detail="Solo se puede hacer check-out de una reserva con check-in registrado",
        )
        
    cuenta = calcular_cuenta(reserva)
    if cuenta["saldo"] > 0:
            raise HTTPException(
                status_code=400,
                detail=f"No se puede hacer check-out con saldo pendiente: Bs {cuenta['saldo']}",
            )
        

    reserva.estado = "Check-out"
    reserva.habitacion.estado = "Limpieza"  # pasa a manos de limpieza

    db.commit()
    db.refresh(reserva)
    return reserva


@router.patch("/{id_reserva}/cancelar", response_model=schemas.ReservaGet)
def cancelar_reserva(
    id_reserva: int,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    """Cancela la reserva. Si el huésped ya estaba adentro, libera la habitación."""
    reserva = (
        db.query(models.TReserva)
        .filter(models.TReserva.id_reserva == id_reserva)
        .first()
    )
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    if reserva.estado in ["Check-out", "Cancelada"]:
        raise HTTPException(
            status_code=400,
            detail=f"La reserva ya está en estado {reserva.estado}",
        )

    reserva.estado = "Cancelada"

    # Si estaba ocupada (check-in activo), liberar la habitación
    if reserva.habitacion.estado == "Ocupada":
        reserva.habitacion.estado = "Limpieza"

    db.commit()
    db.refresh(reserva)
    return reserva