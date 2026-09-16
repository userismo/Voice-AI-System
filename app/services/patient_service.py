from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import Patient
from ..schemas import PatientCreate, PatientUpdate


def list_patients(db: Session, last_name: str | None = None, date_of_birth=None, phone_number: str | None = None):
    stmt = select(Patient).where(Patient.deleted_at.is_(None))
    if last_name:
        stmt = stmt.where(Patient.last_name.ilike(last_name))
    if date_of_birth:
        stmt = stmt.where(Patient.date_of_birth == date_of_birth)
    if phone_number:
        stmt = stmt.where(Patient.phone_number == phone_number)
    stmt = stmt.order_by(Patient.created_at.desc())
    return list(db.scalars(stmt).all())


def get_patient(db: Session, patient_id: str):
    return db.scalar(select(Patient).where(Patient.patient_id == patient_id, Patient.deleted_at.is_(None)))


def find_by_phone(db: Session, phone_number: str):
    return db.scalar(select(Patient).where(Patient.phone_number == phone_number, Patient.deleted_at.is_(None)).order_by(Patient.created_at.desc()))


def create_patient(db: Session, payload: PatientCreate) -> Patient:
    patient = Patient(**payload.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def update_patient(db: Session, patient: Patient, payload: PatientUpdate) -> Patient:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(patient, key, value)
    patient.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(patient)
    return patient


def soft_delete_patient(db: Session, patient: Patient) -> Patient:
    patient.deleted_at = datetime.now(timezone.utc)
    patient.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(patient)
    return patient
