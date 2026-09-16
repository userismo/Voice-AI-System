from tests.test_api import client


def test_vapi_save_patient_tool():
    body = {
        "message": {
            "type": "tool-calls",
            "toolCallList": [
                {
                    "id": "call_demo_1",
                    "type": "function",
                    "function": {
                        "name": "save_patient",
                        "arguments": {
                            "first_name": "John",
                            "last_name": "Smith",
                            "date_of_birth": "03/20/1985",
                            "sex": "Male",
                            "phone_number": "212-555-0101",
                            "address_line_1": "10 Broadway",
                            "city": "New York",
                            "state": "NY",
                            "zip_code": "10004"
                        }
                    }
                }
            ]
        }
    }
    response = client.post("/vapi/tools", json=body)
    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["toolCallId"] == "call_demo_1"
    assert '"success": true' in result["result"]
