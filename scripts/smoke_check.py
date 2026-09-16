"""Run after deployment: python scripts/smoke_test.py https://YOUR-APP.example"""
import sys
import uuid
import httpx

base = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8000"
suffix = str(uuid.uuid4())[:6]
payload = {
    "first_name": "Jane",
    "last_name": f"Demo-{suffix}",
    "date_of_birth": "1990-04-15",
    "sex": "Female",
    "phone_number": "4155551212",
    "address_line_1": "100 Market Street",
    "city": "San Francisco",
    "state": "CA",
    "zip_code": "94105"
}

with httpx.Client(timeout=15) as c:
    r = c.get(f"{base}/health")
    print("health", r.status_code, r.json())
    r = c.post(f"{base}/patients", json=payload)
    print("create", r.status_code, r.json())
    r = c.get(f"{base}/patients", params={"phone_number": "4155551212"})
    print("list", r.status_code, r.json())
