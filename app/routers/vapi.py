"""Vapi function-tool webhook.

The endpoint is intentionally tolerant of small payload-shape differences. It searches
for tool calls in the incoming JSON, dispatches supported function names, and returns
Vapi's required {"results": [{"toolCallId": ..., "result": ...}]} structure.
"""
import json
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import PatientCreate, PatientRead, PatientUpdate, normalize_phone
from ..services import patient_service as svc

logger = logging.getLogger("voice_patient_agent.vapi")
router = APIRouter(prefix="/vapi", tags=["vapi"])


def _walk_tool_calls(obj: Any):
    calls = []
    if isinstance(obj, dict):
        # Common OpenAI/Vapi-ish tool-call objects.
        if ("id" in obj or "toolCallId" in obj) and (
            "function" in obj or "name" in obj or "functionCall" in obj
        ):
            calls.append(obj)
        for value in obj.values():
            calls.extend(_walk_tool_calls(value))
    elif isinstance(obj, list):
        for item in obj:
            calls.extend(_walk_tool_calls(item))
    return calls


def _parse_call(call: dict) -> tuple[str, str, dict]:
    call_id = call.get("id") or call.get("toolCallId") or call.get("tool_call_id") or "unknown"
    function_obj = call.get("function") or call.get("functionCall") or {}
    name = call.get("name") or function_obj.get("name") or call.get("functionName")
    args = call.get("arguments") or function_obj.get("arguments") or call.get("parameters") or {}
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            args = {}
    return str(call_id), str(name or ""), args if isinstance(args, dict) else {}


def _result(call_id: str, payload: Any):
    return {"toolCallId": call_id, "result": json.dumps(payload, default=str)}


@router.post("/tools")
async def vapi_tools(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    calls = _walk_tool_calls(body)
    if not calls:
        raise HTTPException(status_code=400, detail="No Vapi tool call found in payload")

    results = []
    for raw_call in calls:
        call_id, name, args = _parse_call(raw_call)
        try:
            if name == "save_patient":
                payload = PatientCreate.model_validate(args)
                patient = svc.create_patient(db, payload)
                data = PatientRead.model_validate(patient).model_dump(mode="json")
                # Logging minimum required final data payload for observability.
                logger.info("patient_saved payload=%s", json.dumps(data, default=str))
                results.append(_result(call_id, {"success": True, "patient": data}))

            elif name == "lookup_patient_by_phone":
                phone = normalize_phone(args.get("phone_number"))
                patient = svc.find_by_phone(db, phone)
                if patient:
                    data = PatientRead.model_validate(patient).model_dump(mode="json")
                    results.append(_result(call_id, {"found": True, "patient": data}))
                else:
                    results.append(_result(call_id, {"found": False}))

            elif name == "update_patient":
                patient_id = args.pop("patient_id", None)
                if not patient_id:
                    raise ValueError("patient_id is required")
                patient = svc.get_patient(db, patient_id)
                if not patient:
                    results.append(_result(call_id, {"success": False, "error": "Patient not found"}))
                    continue
                payload = PatientUpdate.model_validate(args)
                patient = svc.update_patient(db, patient, payload)
                data = PatientRead.model_validate(patient).model_dump(mode="json")
                logger.info("patient_updated payload=%s", json.dumps(data, default=str))
                results.append(_result(call_id, {"success": True, "patient": data}))

            else:
                results.append(_result(call_id, {"success": False, "error": f"Unsupported tool: {name}"}))

        except (ValidationError, ValueError) as exc:
            results.append(_result(call_id, {"success": False, "error": str(exc)}))
        except Exception:
            logger.exception("Vapi tool failed: %s", name)
            results.append(_result(call_id, {"success": False, "error": "Internal server error"}))

    return {"results": results}
