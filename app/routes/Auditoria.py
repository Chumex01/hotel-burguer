from fastapi import APIRouter, Depends
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/auditoria",
    tags=["Auditoria"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[schemas.AuditoriaGet])
def listar_auditoria(
    id_usuario: str | None = None,
    tabla_afectada: str | None = None,
    accion: str | None = None,
    fecha_desde: datetime | None = None,
    fecha_hasta: datetime | None = None,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    """Filtros combinables. Ej:
    /auditoria/?id_usuario=USU002&accion=UPDATE&tabla_afectada=tpagos
    → ¿qué modificó el recepcionista 2 en pagos?"""
    query = db.query(models.TAuditoria)

    if id_usuario:
        query = query.filter(models.TAuditoria.id_usuario == id_usuario)
    if tabla_afectada:
        query = query.filter(models.TAuditoria.tabla_afectada == tabla_afectada)
    if accion:
        query = query.filter(models.TAuditoria.accion == accion)
    if fecha_desde:
        query = query.filter(models.TAuditoria.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(models.TAuditoria.fecha <= fecha_hasta)

    # Más nuevo primero + tope para no explotar la respuesta
    return query.order_by(models.TAuditoria.fecha.desc()).limit(200).all()