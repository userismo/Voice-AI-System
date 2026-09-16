import os
from pathlib import Path

# Must be set before importing the app/database module.
TEST_DB = Path(__file__).parent / "test_patients.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def sample_patient():
    return {
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": "1990-04-15",
        "sex": "Female",
        "phone_number": "4155551212",
        "address_line_1": "100 Market Street",
        "city": "San Francisco",
        "state": "CA",
        "zip_code": "94105"
    }


def test_crud_flow():
    created = client.post("/patients", json=sample_patient())
    assert created.status_code == 201
    record = created.json()["data"]
    patient_id = record["patient_id"]

    listed = client.get("/patients", params={"phone_number": "4155551212"})
    assert listed.status_code == 200
    assert len(listed.json()["data"]) >= 1

    updated = client.put(f"/patients/{patient_id}", json={"city": "Oakland"})
    assert updated.status_code == 200
    assert updated.json()["data"]["city"] == "Oakland"

    deleted = client.delete(f"/patients/{patient_id}")
    assert deleted.status_code == 200

    missing = client.get(f"/patients/{patient_id}")
    assert missing.status_code == 404
