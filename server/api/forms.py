from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.models import FormDefinition
from schemas.schemas import FormDefinitionCreate, FormDefinitionResponse, FormSchema

router = APIRouter(prefix="/api/forms", tags=["forms"])


@router.post("/", response_model=FormDefinitionResponse)
def create_form(form: FormDefinitionCreate, db: Session = Depends(get_db)):
    existing = db.query(FormDefinition).filter(FormDefinition.name == form.name).order_by(FormDefinition.version.desc()).first()
    version = (existing.version + 1) if existing else 1

    db_form = FormDefinition(
        name=form.name,
        schema_json=form.schema_json.model_dump(),
        version=version,
    )
    db.add(db_form)
    db.commit()
    db.refresh(db_form)
    return db_form


@router.get("/{form_id}", response_model=FormDefinitionResponse)
def get_form(form_id: int, db: Session = Depends(get_db)):
    form = db.query(FormDefinition).filter(FormDefinition.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    return form


@router.get("/", response_model=list[FormDefinitionResponse])
def list_forms(db: Session = Depends(get_db)):
    return db.query(FormDefinition).all()


@router.get("/schema/{form_id}")
def get_form_schema(form_id: int, db: Session = Depends(get_db)):
    form = db.query(FormDefinition).filter(FormDefinition.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    return form.schema_json
