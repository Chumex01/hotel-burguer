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
from app.routes import auth
Base.metadata.create_all(bind=engine)


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="API Hotel", version="1.0.0")

# ⬇️ ESTE BLOQUE — después de crear la app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # el origen EXACTO de tu front
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
app.include_router(auth.router)