from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/huesped",
    tags=["Huesped"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[schemas.HuespedGet])
def listar_huespedes(
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    huespedes = db.query(models.THuesped).all()
    return huespedes


# ⚠️ IMPORTANTE: declarar ANTES de "/{id_huesped}" para que
# FastAPI no intente interpretar "buscar" como un id
@router.get("/buscar", response_model=list[schemas.HuespedGet])
def buscar_huespedes(
    ci: str | None = None,
    nombre: str | None = None,
    apellido: str | None = None,
    db: Session = Depends(get_db),
):
    """Búsqueda para recepción: por CI exacto o nombre/apellido parcial."""
    query = db.query(models.THuesped)

    if ci:
        query = query.filter(models.THuesped.ci == ci)
    if nombre:
        query = query.filter(models.THuesped.nombre.ilike(f"%{nombre}%"))
    if apellido:
        query = query.filter(models.THuesped.apellido.ilike(f"%{apellido}%"))

    return query.all()


@router.get("/{id_huesped}", response_model=schemas.HuespedGet)
def obtener_huesped(
    id_huesped: int,
    db: Session = Depends(get_db),
):
    huesped = (
        db.query(models.THuesped)
        .filter(models.THuesped.id_huesped == id_huesped)
        .first()
    )
    if not huesped:
        raise HTTPException(status_code=404, detail="Huésped no encontrado")
    return huesped


@router.post("/", response_model=schemas.HuespedGet, status_code=status.HTTP_201_CREATED)
def crear_huesped(
    huesped_data: schemas.HuespedCreate,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    ci_existente = (
        db.query(models.THuesped)
        .filter(models.THuesped.ci == huesped_data.ci)
        .first()
    )
    if ci_existente:
        raise HTTPException(status_code=400, detail="Ya existe un huésped registrado con ese CI")

    nuevo_huesped = models.THuesped(
        ci=huesped_data.ci,
        nombre=huesped_data.nombre,
        apellido=huesped_data.apellido,
        telefono=huesped_data.telefono,
        email=huesped_data.email,
        nacionalidad=huesped_data.nacionalidad,
    )

    db.add(nuevo_huesped)
    db.commit()
    db.refresh(nuevo_huesped)
    return nuevo_huesped


@router.put("/{id_huesped}", response_model=schemas.HuespedGet)
def actualizar_huesped(
    id_huesped: int,
    huesped_data: schemas.HuespedUpdate,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    huesped = (
        db.query(models.THuesped)
        .filter(models.THuesped.id_huesped == id_huesped)
        .first()
    )
    if not huesped:
        raise HTTPException(status_code=404, detail="Huésped no encontrado")

    datos = huesped_data.model_dump(exclude_unset=True)  # solo campos enviados

    # Si intentan cambiar el CI, validar que no colisione con otro huésped
    if "ci" in datos and datos["ci"] != huesped.ci:
        ci_existente = (
            db.query(models.THuesped)
            .filter(
                models.THuesped.ci == datos["ci"],
                models.THuesped.id_huesped != id_huesped,
            )
            .first()
        )
        if ci_existente:
            raise HTTPException(status_code=400, detail="Ese CI ya pertenece a otro huésped")

    for campo, valor in datos.items():
        setattr(huesped, campo, valor)

    db.commit()
    db.refresh(huesped)
    return huesped


@router.delete("/{id_huesped}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_huesped(
    id_huesped: int,
    db: Session = Depends(get_db),
    #current_user: models.TUsuario = Depends(get_current_user),
):
    huesped = (
        db.query(models.THuesped)
        .filter(models.THuesped.id_huesped == id_huesped)
        .first()
    )
    if not huesped:
        raise HTTPException(status_code=404, detail="Huésped no encontrado")

    # No eliminar si tiene reservas (la FK lo impediría igual, pero con mensaje claro)
    tiene_reservas = (
        db.query(models.TReserva)
        .filter(models.TReserva.id_huesped == id_huesped)
        .first()
    )
    if tiene_reservas:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar: el huésped tiene reservas asociadas",
        )

    db.delete(huesped)
    db.commit()