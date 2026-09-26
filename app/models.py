from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.database import Base


# --- SEGURIDAD Y ACCESO ---


class TRol(Base):
    __tablename__ = "troles"

    id_rol = Column(String(6), primary_key=True)  # ROL001
    nombre = Column(String(30), nullable=False)  # Administrador, Recepcionista, Gerente, Contabilidad
    descripcion = Column(Text)
    fecha_creacion = Column(DateTime, default=lambda: datetime.now())
    fecha_eliminado = Column(DateTime, nullable=True)

    usuarios = relationship("TUsuario", back_populates="rol")


class TUsuario(Base):
    __tablename__ = "tusuarios"

    id_usuario = Column(String(6), primary_key=True, index=True)
    id_rol = Column(String(6), ForeignKey("troles.id_rol"), nullable=False)
    nombre = Column(String(50), nullable=False)
    apellido = Column(String(50), nullable=False)
    usuario = Column(String(20), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  # Hash bcrypt, nunca texto plano
    email = Column(String(100), unique=True, nullable=False)
    estado = Column(String(15), default="Activo")  # Activo / Inactivo
    fecha_creacion = Column(DateTime, default=lambda: datetime.now())
    fecha_eliminado = Column(DateTime, nullable=True)

    rol = relationship("TRol", back_populates="usuarios")
    reservas = relationship("TReserva", back_populates="usuario")
    auditorias = relationship("TAuditoria", back_populates="usuario")


# --- HUÉSPEDES Y HABITACIONES ---


class THuesped(Base):
    __tablename__ = "thuespedes"

    id_huesped = Column(Integer, primary_key=True, index=True)
    ci = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(50), nullable=False)
    apellido = Column(String(50), nullable=False)
    telefono = Column(String(20))
    email = Column(String(100))
    nacionalidad = Column(String(50))
    fecha_registro = Column(DateTime, default=lambda: datetime.now())
    fecha_eliminado = Column(DateTime, nullable=True)

    reservas = relationship("TReserva", back_populates="huesped")


class TTipoHabitacion(Base):
    __tablename__ = "ttipos_habitaciones"

    id_tipo = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(30), nullable=False)  # Individual, Doble, Matrimonial, Suite
    descripcion = Column(Text)
    capacidad = Column(Integer, nullable=False)
    precio_noche = Column(Numeric(10, 2), nullable=False)
    fecha_creacion = Column(DateTime, default=lambda: datetime.now())
    fecha_eliminado = Column(DateTime, nullable=True)

    habitaciones = relationship("THabitacion", back_populates="tipo_habitacion")


class THabitacion(Base):
    __tablename__ = "thabitaciones"

    id_habitacion = Column(Integer, primary_key=True, index=True)
    id_tipo = Column(Integer, ForeignKey("ttipos_habitaciones.id_tipo"), nullable=False)
    numero = Column(String(10), unique=True, nullable=False)
    piso = Column(Integer, nullable=False)
    estado = Column(String(20), default="Disponible")  # Disponible / Ocupada / Mantenimiento / Limpieza

    tipo_habitacion = relationship("TTipoHabitacion", back_populates="habitaciones")
    reservas = relationship("TReserva", back_populates="habitacion")


# --- OPERACIÓN DEL HOTEL ---


class TReserva(Base):
    __tablename__ = "treservas"

    id_reserva = Column(Integer, primary_key=True, index=True)
    id_huesped = Column(Integer, ForeignKey("thuespedes.id_huesped"), nullable=False)
    id_habitacion = Column(Integer, ForeignKey("thabitaciones.id_habitacion"), nullable=False)
    id_usuario = Column(String(6), ForeignKey("tusuarios.id_usuario"), nullable=False)  # Quién registró la reserva
    fecha_reserva = Column(DateTime, default=lambda: datetime.now())
    fecha_entrada = Column(DateTime, nullable=False)
    fecha_salida = Column(DateTime, nullable=False)
    cantidad_personas = Column(Integer, nullable=False)
    estado = Column(String(20), default="Pendiente")  # Pendiente / Confirmada / Check-in / Check-out / Cancelada
    observaciones = Column(Text, nullable=True)

    huesped = relationship("THuesped", back_populates="reservas")
    habitacion = relationship("THabitacion", back_populates="reservas")
    usuario = relationship("TUsuario", back_populates="reservas")
    reserva_servicios = relationship("TReservaServicio", back_populates="reserva")
    pagos = relationship("TPago", back_populates="reserva")


class TServicio(Base):
    __tablename__ = "tservicios"

    id_servicio = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)
    descripcion = Column(Text)
    precio = Column(Numeric(10, 2), nullable=False)
    estado = Column(String(15), default="Activo")  # Activo / Inactivo (se desactiva, no se elimina)
    fecha_creacion = Column(DateTime, default=lambda: datetime.now())
    fecha_eliminado = Column(DateTime, nullable=True)

    reserva_servicios = relationship("TReservaServicio", back_populates="servicio")


class TReservaServicio(Base):
    __tablename__ = "treservas_servicios"

    id_reserva_servicio = Column(Integer, primary_key=True, index=True)
    id_reserva = Column(Integer, ForeignKey("treservas.id_reserva"), nullable=False)
    id_servicio = Column(Integer, ForeignKey("tservicios.id_servicio"), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)
    precio_unitario = Column(Numeric(10, 2), nullable=False)  # ⚠️ Precio histórico al momento del consumo
    fecha = Column(DateTime, default=lambda: datetime.now())
    observacion = Column(Text, nullable=True)

    reserva = relationship("TReserva", back_populates="reserva_servicios")
    servicio = relationship("TServicio", back_populates="reserva_servicios")


class TPago(Base):
    __tablename__ = "tpagos"

    id_pago = Column(Integer, primary_key=True, index=True)
    id_reserva = Column(Integer, ForeignKey("treservas.id_reserva"), nullable=False)
    fecha_pago = Column(DateTime, default=lambda: datetime.now())
    monto = Column(Numeric(10, 2), nullable=False)
    metodo_pago = Column(String(30), nullable=False)  # Efectivo / Transferencia / Tarjeta / QR
    estado = Column(String(20), default="Pagado")  # Pendiente / Pagado / Anulado / Reembolsado
    observacion = Column(Text, nullable=True)

    reserva = relationship("TReserva", back_populates="pagos")


class TAuditoria(Base):
    __tablename__ = "tauditorias"

    id_auditoria = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(String(6), ForeignKey("tusuarios.id_usuario"), nullable=True)  # NULL = acción del sistema
    accion = Column(String(30), nullable=False)  # INSERT / UPDATE / DELETE / LOGIN / LOGOUT
    tabla_afectada = Column(String(30), nullable=False)
    id_registro = Column(Integer, nullable=True)
    fecha = Column(DateTime, default=lambda: datetime.now())
    descripcion = Column(Text)
    ip = Column(String(45))  # 45 caracteres para soportar IPv6

    usuario = relationship("TUsuario", back_populates="auditorias")