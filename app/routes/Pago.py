from fastapi import APIRouter, Depends, HTTPException, status
from decimal import Decimal
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/pago",
    tags=["Pago"],
    responses={404: {"description": "Not found"}},
)


def calcular_cuenta(reserva: models.TReserva) -> dict:
    """Desglose completo: habitación + servicios − pagos válidos."""
    noches = max(
        (reserva.fecha_salida.date() - reserva.fecha_entrada.date()).days, 1
    )
    precio_noche = reserva.habitacion.tipo_habitacion.precio_noche  # ⬅️ capturarlo aquí
    total_habitacion = precio_noche * noches

    total_servicios = sum(
        (rs.cantidad * rs.precio_unitario for rs in reserva.reserva_servicios),
        start=Decimal("0.00"),
    )

    total_pagado = sum(
        (p.monto for p in reserva.pagos if p.estado != "Anulado"),
        start=Decimal("0.00"),
    )

    return {
        "noches": noches,
        "precio_noche": precio_noche,  # ⬅️ y devolverlo
        "total_habitacion": total_habitacion,
        "total_servicios": total_servicios,
        "total_pagado": total_pagado,
        "saldo": total_habitacion + total_servicios - total_pagado,
    }


@router.get("/", response_model=list[schemas.PagoGet])
def listar_pagos(
    id_reserva: int | None = None,
    estado: schemas.ESTADOS_PAGO | None = None,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    """Ej: /pago/?id_reserva=15 — historial de pagos de una reserva."""
    query = db.query(models.TPago)

    if id_reserva is not None:
        query = query.filter(models.TPago.id_reserva == id_reserva)
    if estado:
        query = query.filter(models.TPago.estado == estado)

    return query.order_by(models.TPago.fecha_pago).all()


# ⚠️ Antes de /{id_pago}
@router.get("/cuenta-completa", response_model=schemas.CuentaCompletaGet)
def obtener_cuenta_completa(
    id_reserva: int,
    db: Session = Depends(get_db),
):
    """EL endpoint del check-out: todo lo que debe, todo lo que pagó."""
    reserva = (
        db.query(models.TReserva)
        .filter(models.TReserva.id_reserva == id_reserva)
        .first()
    )
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    cuenta = calcular_cuenta(reserva)

    return {
        "id_reserva": reserva.id_reserva,
        "estado_reserva": reserva.estado,
        "huesped": f"{reserva.huesped.nombre} {reserva.huesped.apellido}",
        "habitacion": reserva.habitacion.numero,
        **cuenta,
    }


@router.get("/{id_pago}", response_model=schemas.PagoGet)
def obtener_pago(
    id_pago: int,
    db: Session = Depends(get_db),
):
    pago = db.query(models.TPago).filter(models.TPago.id_pago == id_pago).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return pago


@router.post("/", response_model=schemas.PagoGet, status_code=status.HTTP_201_CREATED)
def registrar_pago(
    pago_data: schemas.PagoCreate,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    # 1. Validar que la reserva exista
    reserva = (
        db.query(models.TReserva)
        .filter(models.TReserva.id_reserva == pago_data.id_reserva)
        .first()
    )
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    # 2. No se paga una reserva cancelada
    if reserva.estado == "Cancelada":
        raise HTTPException(
            status_code=400,
            detail="No se pueden registrar pagos sobre una reserva cancelada",
        )

    # 3. Evitar sobrepago contra la cuenta conocida
    cuenta = calcular_cuenta(reserva)
    if cuenta["saldo"] <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"La reserva no tiene saldo pendiente (saldo: Bs {cuenta['saldo']})",
        )
    if pago_data.monto > cuenta["saldo"]:
        raise HTTPException(
            status_code=400,
            detail=f"El monto excede el saldo pendiente. "
                   f"Saldo actual: Bs {cuenta['saldo']}, intentas pagar Bs {pago_data.monto}",
        )

    nuevo_pago = models.TPago(
        id_reserva=pago_data.id_reserva,
        monto=pago_data.monto,
        metodo_pago=pago_data.metodo_pago,
        estado=pago_data.estado,
        observacion=pago_data.observacion,
    )

    db.add(nuevo_pago)
    db.commit()
    db.refresh(nuevo_pago)
    return nuevo_pago


@router.put("/{id_pago}", response_model=schemas.PagoGet)
def actualizar_pago(
    id_pago: int,
    pago_data: schemas.PagoUpdate,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    """Solo permite corregir método y observación. El MONTO es intocable."""
    pago = db.query(models.TPago).filter(models.TPago.id_pago == id_pago).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    if pago.estado == "Anulado":
        raise HTTPException(status_code=400, detail="No se puede modificar un pago anulado")

    datos = pago_data.model_dump(exclude_unset=True)
    for campo, valor in datos.items():
        setattr(pago, campo, valor)

    db.commit()
    db.refresh(pago)
    return pago


@router.patch("/{id_pago}/anular", response_model=schemas.PagoGet)
def anular_pago(
    id_pago: int,
    observacion: str,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    """Anula un pago (queda registrado como Anulado, jamás se borra).
    Requiere justificación. Ej: /pago/5/anular?observacion=Error de digitación"""
    pago = db.query(models.TPago).filter(models.TPago.id_pago == id_pago).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    if pago.estado == "Anulado":
        raise HTTPException(status_code=400, detail="El pago ya está anulado")
    if pago.estado == "Reembolsado":
        raise HTTPException(status_code=400, detail="Un pago reembolsado no se anula, ya fue devuelto")

    pago.estado = "Anulado"
    pago.observacion = observacion
    db.commit()
    db.refresh(pago)
    return pago


@router.patch("/{id_pago}/reembolsar", response_model=schemas.PagoGet)
def reembolsar_pago(
    id_pago: int,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    """Marca un pago como devuelto. Ej: cancelación con anticipo pagado."""
    pago = db.query(models.TPago).filter(models.TPago.id_pago == id_pago).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    if pago.estado != "Pagado":
        raise HTTPException(
            status_code=400,
            detail=f"Solo se puede reembolsar un pago en estado Pagado (actual: {pago.estado})",
        )

    pago.estado = "Reembolsado"
    db.commit()
    db.refresh(pago)
    return pago