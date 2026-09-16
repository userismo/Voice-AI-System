from datetime import date
import re
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import PatientCreate, PatientRead, PatientUpdate, normalize_phone
from ..services import patient_service as svc

router = APIRouter(prefix="/patients", tags=["patients"])


def ok(data):
    if isinstance(data, list):
        return {"data": [PatientRead.model_validate(x).model_dump(mode="json") for x in data], "error": None}
    return {"data": PatientRead.model_validate(data).model_dump(mode="json"), "error": None}


@router.get("")
def list_patients(
    last_name: str | None = Query(default=None),
    date_of_birth: date | None = Query(default=None),
    phone_number: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if phone_number:
        try:
            phone_number = normalize_phone(phone_number)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
    return ok(svc.list_patients(db, last_name, date_of_birth, phone_number))


@router.get("/{patient_id}")
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = svc.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return ok(patient)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    patient = svc.create_patient(db, payload)
    return ok(patient)


@router.put("/{patient_id}")
def update_patient(patient_id: str, payload: PatientUpdate, db: Session = Depends(get_db)):
    patient = svc.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return ok(svc.update_patient(db, patient, payload))


@router.delete("/{patient_id}")
def delete_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = svc.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient = svc.soft_delete_patient(db, patient)
    return ok(patient)
