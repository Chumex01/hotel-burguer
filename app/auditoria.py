from datetime import datetime

from fastapi import Request
from sqlalchemy.orm import Session

from app import models


def obtener_ip(request: Request | None) -> str | None:
    """IP real del cliente. Si hay proxy/nginx, viene en X-Forwarded-For."""
    if request is None:
        return None
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def registrar_auditoria(
    db: Session,
    request: Request | None,
    id_usuario: str | None,
    accion: str,                # INSERT / UPDATE / DELETE / LOGIN / LOGOUT
    tabla_afectada: str,        # treservas / tpagos / thuespedes...
    id_registro: int | str | None = None,
    descripcion: str = "",
) -> None:
    """
    Agrega el registro de auditoría a la MISMA transacción del endpoint.
    NO hace commit: si el endpoint falla y hace rollback,
    la auditoría se revierte también (nunca queda constancia de algo que no ocurrió).
    """
    registro = models.TAuditoria(
        id_usuario=id_usuario,
        accion=accion,
        tabla_afectada=tabla_afectada,
        id_registro=id_registro,
        fecha=datetime.now(),
        descripcion=descripcion,
        ip=obtener_ip(request),
    )
    db.add(registro)