import json
import decimal
from typing import Optional
from sqlalchemy.orm import Session
from app import models

def serialize(obj):
    """Función helper para serializar objetos especiales a JSON"""
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def create_audit_log(
    db: Session, 
    id_usuario: str,       # Ajustado a tu modelo (String)
    tabla: str, 
    accion: str, 
    old_val: dict = None, 
    new_val: dict = None,
    ip: Optional[str] = None,         # Nuevo
    user_agent: Optional[str] = None  # Nuevo
):
    old_json = json.dumps(old_val, default=serialize) if old_val else None
    new_json = json.dumps(new_val, default=serialize) if new_val else None
    
    audit = models.TAuditoria(
        id_usuario=id_usuario,
        tabla=tabla,
        accion=accion,
        datos_previos=old_json,  # Ajustado al nombre de tu columna
        datos_nuevos=new_json,   # Ajustado al nombre de tu columna
        ip=ip,
        user_agent=user_agent
    )
    
    db.add(audit)
    # Nota: No hacemos commit aquí, se hace en el endpoint para que todo sea transaccional