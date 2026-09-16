from html import escape

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import patient_service as svc


router = APIRouter(tags=["dashboard"])


def safe(value):
    if value is None:
        return "—"
    return escape(str(value))


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def dashboard(db: Session = Depends(get_db)):
    patients = svc.list_patients(db)

    rows = ""

    for patient in patients:
        rows += f"""
        <tr>
            <td>{safe(patient.first_name)} {safe(patient.last_name)}</td>
            <td>{safe(patient.date_of_birth)}</td>
            <td>{safe(patient.sex)}</td>
            <td>{safe(patient.phone_number)}</td>
            <td>{safe(patient.email)}</td>
            <td>{safe(patient.city)}, {safe(patient.state)}</td>
            <td>{safe(patient.zip_code)}</td>
            <td>{safe(patient.preferred_language)}</td>
            <td>{safe(patient.created_at.strftime("%Y-%m-%d %H:%M UTC"))}</td>
        </tr>
        """

    if not rows:
        rows = """
        <tr>
            <td colspan="9" class="empty">No patients registered yet.</td>
        </tr>
        """

    return HTMLResponse(
        content=f"""
<!DOCTYPE html>
<html>
<head>
    <title>Patient Registration Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f4f7fb;
            color: #1f2937;
        }}

        header {{
            background: #ffffff;
            border-bottom: 1px solid #e5e7eb;
            padding: 24px 40px;
        }}

        h1 {{
            margin: 0 0 5px 0;
            font-size: 26px;
        }}

        .subtitle {{
            color: #6b7280;
        }}

        .container {{
            padding: 30px 40px;
        }}

        .card {{
            background: white;
            border-radius: 12px;
            padding: 22px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            overflow-x: auto;
        }}

        .stats {{
            margin-bottom: 20px;
            font-size: 16px;
        }}

        .stats strong {{
            font-size: 24px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            min-width: 900px;
        }}

        th {{
            text-align: left;
            padding: 13px;
            background: #f8fafc;
            border-bottom: 2px solid #e5e7eb;
        }}

        td {{
            padding: 13px;
            border-bottom: 1px solid #e5e7eb;
        }}

        tr:hover {{
            background: #f9fafb;
        }}

        .empty {{
            text-align: center;
            padding: 40px;
            color: #6b7280;
        }}

        .links {{
            margin-top: 20px;
        }}

        .links a {{
            margin-right: 15px;
            color: #2563eb;
            text-decoration: none;
        }}

        .notice {{
            margin-bottom: 20px;
            padding: 12px 16px;
            background: #fff7ed;
            border-radius: 8px;
            color: #9a3412;
        }}
    </style>
</head>

<body>

<header>
    <h1>Patient Registration Dashboard</h1>
    <div class="subtitle">Voice AI Patient Registration System</div>
</header>

<div class="container">

    <div class="notice">
        Demo environment — use fictitious patient information only.
    </div>

    <div class="card">

        <div class="stats">
            Registered Patients<br>
            <strong>{len(patients)}</strong>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Patient</th>
                    <th>Date of Birth</th>
                    <th>Sex</th>
                    <th>Phone</th>
                    <th>Email</th>
                    <th>Location</th>
                    <th>ZIP</th>
                    <th>Language</th>
                    <th>Registered</th>
                </tr>
            </thead>

            <tbody>
                {rows}
            </tbody>

        </table>

        <div class="links">
            <a href="/docs">API Documentation</a>
            <a href="/patients">Raw Patient API</a>
        </div>

    </div>

</div>

</body>
</html>
"""
    )
