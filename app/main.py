from fastapi import FastAPI
from app.database import engine, Base
from app import models
from app.routes import Rol
from app.routes import Usuario
from app.routes import Huesped
from app.routes import TipoHabitacion
from app.routes import Habitacion
from app.routes import Reserva
from app.routes import Servicio
from app.routes import ReservaServicio
from app.routes import Pago
from app.routes import Auditoria

Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Hotel", version="1.0.0")


@app.get("/")
def root():
    return {"mensaje": "API Hotel funcionando 🏨"}



app.include_router(Rol.router)
app.include_router(Usuario.router)
app.include_router(Huesped.router)
app.include_router(TipoHabitacion.router)
app.include_router(Habitacion.router)
app.include_router(Reserva.router)
app.include_router(Servicio.router)
app.include_router(ReservaServicio.router)
app.include_router(Pago.router)
app.include_router(Auditoria.router)