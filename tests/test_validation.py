from datetime import date, timedelta
import pytest
from pydantic import ValidationError
from app.schemas import PatientCreate


def base_payload():
    return {
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": "1990-04-15",
        "sex": "Female",
        "phone_number": "415-555-1212",
        "address_line_1": "100 Market Street",
        "city": "San Francisco",
        "state": "CA",
        "zip_code": "94105",
    }


def test_valid_patient_normalizes_phone():
    patient = PatientCreate.model_validate(base_payload())
    assert patient.phone_number == "4155551212"
    assert patient.state == "CA"


def test_future_dob_rejected():
    payload = base_payload()
    payload["date_of_birth"] = (date.today() + timedelta(days=1)).isoformat()
    with pytest.raises(ValidationError):
        PatientCreate.model_validate(payload)


def test_short_phone_rejected():
    payload = base_payload()
    payload["phone_number"] = "123"
    with pytest.raises(ValidationError):
        PatientCreate.model_validate(payload)


def test_invalid_state_rejected():
    payload = base_payload()
    payload["state"] = "XX"
    with pytest.raises(ValidationError):
        PatientCreate.model_validate(payload)
