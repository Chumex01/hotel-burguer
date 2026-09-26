from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from pydantic import Field
from decimal import Decimal
from typing import Literal
from app import schemas

# ROL
class RolCreate(BaseModel):
    id_rol: str
    nombre: str
    descripcion: str

class RolGet(BaseModel):
    id_rol: str
    nombre: str
    descripcion: str
    fecha_creacion: datetime
# USUARIO
class UsuarioGet(BaseModel):
    id_usuario: str
    id_rol: str
    nombre: str
    apellido: str
    usuario: str
    email: str
    estado: str
    fecha_creacion: datetime
    
    model_config = {"from_atributes": True}

class UsuarioCreate(BaseModel):
    id_rol: str
    nombre: str
    apellido: str
    usuario: str
    password: str
    email: str
    estado: str = "Activo"
#HUESPEDES
# --- HUÉSPEDES ---
class HuespedGet(BaseModel):
    id_huesped: int
    ci: str
    nombre: str
    apellido: str
    telefono: str | None = None
    email: str | None = None
    nacionalidad: str | None = None
    fecha_registro: datetime

    model_config = {"from_attributes": True}


class HuespedCreate(BaseModel):
    ci: str
    nombre: str
    apellido: str
    telefono: str | None = None
    email: str | None = None
    nacionalidad: str | None = None


class HuespedUpdate(BaseModel):
    ci: str | None = None
    nombre: str | None = None
    apellido: str | None = None
    telefono: str | None = None
    email: str | None = None
    nacionalidad: str | None = None
# --- TIPOS DE HABITACIÓN ---
class TipoHabitacionGet(BaseModel):
    id_tipo: int
    nombre: str
    descripcion: str | None = None
    capacidad: int
    precio_noche: Decimal
    fecha_creacion: datetime

    model_config = {"from_attributes": True}


class TipoHabitacionCreate(BaseModel):
    nombre: str = Field(max_length=30)
    descripcion: str | None = None
    capacidad: int = Field(gt=0)          # mayor a 0, si no → 422 automático
    precio_noche: Decimal = Field(gt=0)   # evita precios 0 o negativos


class TipoHabitacionUpdate(BaseModel):
    nombre: str | None = Field(default=None, max_length=30)
    descripcion: str | None = None
    capacidad: int | None = Field(default=None, gt=0)
    precio_noche: Decimal | None = Field(default=None, gt=0)
# --- HABITACIONES ---

ESTADOS_HABITACION = Literal["Disponible", "Ocupada", "Mantenimiento", "Limpieza"]


class HabitacionGet(BaseModel):
    id_habitacion: int
    id_tipo: int
    numero: str
    piso: int
    estado: str

    model_config = {"from_attributes": True}


class HabitacionCreate(BaseModel):
    id_tipo: int
    numero: str = Field(max_length=10)
    piso: int = Field(ge=1)  # sin sótanos ni pisos 0 😄
    estado: ESTADOS_HABITACION = "Disponible"


class HabitacionUpdate(BaseModel):
    id_tipo: int | None = None
    numero: str | None = Field(default=None, max_length=10)
    piso: int | None = Field(default=None, ge=1)
    estado: ESTADOS_HABITACION | None = None


class HabitacionEstadoUpdate(BaseModel):
    estado: ESTADOS_HABITACION
    
class HabitacionConTipoGet(BaseModel):
    tipo_habitacion: TipoHabitacionGet  # debe llamarse igual que la relationship
    
# --- RESERVAS ---
ESTADOS_RESERVA = Literal["Pendiente", "Confirmada", "Check-in", "Check-out", "Cancelada"]


class ReservaGet(BaseModel):
    id_reserva: int
    id_huesped: int
    id_habitacion: int
    id_usuario: str
    fecha_reserva: datetime
    fecha_entrada: datetime
    fecha_salida: datetime
    cantidad_personas: int
    estado: str
    observaciones: str | None = None

    model_config = {"from_attributes": True}


class ReservaCreate(BaseModel):
    id_huesped: int
    id_habitacion: int
    fecha_entrada: datetime
    fecha_salida: datetime
    cantidad_personas: int = Field(ge=1)
    estado: ESTADOS_RESERVA = "Pendiente"
    observaciones: str | None = None


class ReservaUpdate(BaseModel):
    id_habitacion: int | None = None
    fecha_entrada: datetime | None = None
    fecha_salida: datetime | None = None
    cantidad_personas: int | None = Field(default=None, ge=1)
    observaciones: str | None = None


# --- DETALLE DE RESERVA (con totales calculados) ---
class ReservaDetalleGet(ReservaGet):
    huesped: schemas.HuespedGet
    habitacion: schemas.HabitacionGet
    noches: int
    total_habitacion: Decimal
    total_servicios: Decimal
    total_pagado: Decimal
    saldo: Decimal
# --- SERVICIOS ---
ESTADO_SERVICIO = Literal["Activo", "Inactivo"]


class ServicioGet(BaseModel):
    id_servicio: int
    nombre: str
    descripcion: str | None = None
    precio: Decimal
    estado: str
    fecha_creacion: datetime

    model_config = {"from_attributes": True}


class ServicioCreate(BaseModel):
    nombre: str = Field(max_length=50)
    descripcion: str | None = None
    precio: Decimal = Field(gt=0)


class ServicioUpdate(BaseModel):
    nombre: str | None = Field(default=None, max_length=50)
    descripcion: str | None = None
    precio: Decimal | None = Field(default=None, gt=0)


class ServicioEstadoUpdate(BaseModel):
    estado: ESTADO_SERVICIO
# --- RESERVA_SERVICIOS (consumos de la cuenta) ---
class ReservaServicioGet(BaseModel):
    id_reserva_servicio: int
    id_reserva: int
    id_servicio: int
    cantidad: int
    precio_unitario: Decimal
    fecha: datetime
    observacion: str | None = None

    model_config = {"from_attributes": True}


class ReservaServicioConServicioGet(ReservaServicioGet):
    # 'servicio' debe llamarse igual que la relationship del modelo
    servicio: schemas.ServicioGet


class ReservaServicioCreate(BaseModel):
    id_reserva: int
    id_servicio: int
    cantidad: int = Field(default=1, ge=1)
    observacion: str | None = None
    # 🚫 SIN precio_unitario: lo pone el servidor con el precio vigente


class ReservaServicioUpdate(BaseModel):
    cantidad: int | None = Field(default=None, ge=1)
    observacion: str | None = None


# --- CUENTA (el "ticket" de la reserva) ---
class CuentaReservaGet(BaseModel):
    id_reserva: int
    estado_reserva: str
    detalle: list[ReservaServicioConServicioGet]
    total_servicios: Decimal
# --- PAGOS ---
METODOS_PAGO = Literal["Efectivo", "Transferencia", "Tarjeta", "QR"]
ESTADOS_PAGO = Literal["Pendiente", "Pagado", "Anulado", "Reembolsado"]


class PagoGet(BaseModel):
    id_pago: int
    id_reserva: int
    fecha_pago: datetime
    monto: Decimal
    metodo_pago: str
    estado: str
    observacion: str | None = None

    model_config = {"from_attributes": True}


class PagoCreate(BaseModel):
    id_reserva: int
    monto: Decimal = Field(gt=0)  # no existen pagos de 0 ni negativos
    metodo_pago: METODOS_PAGO
    estado: ESTADOS_PAGO = "Pagado"
    observacion: str | None = None


class PagoUpdate(BaseModel):
    # 🚫 SIN monto: el monto de un pago registrado no se edita, se anula y se re-registra
    metodo_pago: METODOS_PAGO | None = None
    observacion: str | None = None


# --- RESUMEN DE CUENTA (lo que se muestra en el check-out) ---
class CuentaCompletaGet(BaseModel):
    id_reserva: int
    estado_reserva: str
    huesped: str
    habitacion: str
    noches: int
    precio_noche: Decimal
    total_habitacion: Decimal
    total_servicios: Decimal
    total_pagado: Decimal
    saldo: Decimal
# --- AUDITORÍA (solo lectura) ---
class AuditoriaGet(BaseModel):
    id_auditoria: int
    id_usuario: str | None = None
    accion: str
    tabla_afectada: str
    id_registro: int | None = None
    fecha: datetime
    descripcion: str | None = None
    ip: str | None = None

    model_config = {"from_attributes": True}