"""
CEISA Document API
==================

Document validation and submission to CEISA API.

Endpoints:
    - POST /openapi/document/check            - Validate JSON document before sending
    - POST /openapi/document?isFinal=false     - Submit document (draft)
    - POST /openapi/document?isFinal=true      - Submit document (final)
"""

import frappe
import requests
from .auth import get_ceisa_settings, ensure_login, build_auth_headers


@frappe.whitelist()
def check_document(payload):
    """Validate JSON document format before sending to CEISA.

    Endpoint: POST /openapi/document/check
    Requires: Bearer token

    Args:
        payload: JSON document payload (dict or JSON string)

    Returns:
        dict with validation result
    """
    import json as _json
    import datetime

    def _serialize(obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    try:
        token = ensure_login()
        if not token:
            return {"status": "error", "message": "Tidak bisa mendapatkan token. Silakan login terlebih dahulu."}

        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"

        # Handle string payload
        if isinstance(payload, str):
            payload = _json.loads(payload)

        url = f"{base_url}/openapi/document/check"
        headers = build_auth_headers(token)

        # Serialize with date handler, then parse back for requests
        payload_str = _json.dumps(payload, default=_serialize)
        payload_clean = _json.loads(payload_str)

        response = requests.post(url, json=payload_clean, headers=headers)

        try:
            data = response.json()
        except Exception:
            data = response.text

        return {
            "status": "success" if response.status_code == 200 else "error",
            "http_code": response.status_code,
            "data": data
        }

    except requests.exceptions.HTTPError as e:
        frappe.log_error(frappe.get_traceback(), "Check Document Error")
        return {"status": "error", "message": f"HTTP Error: {e.response.status_code} - {e.response.text}"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Check Document Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def send_document(payload, is_final=False):
    """Submit document to CEISA (Draft or Final).

    Endpoint: POST /openapi/document?isFinal={true/false}
    Requires: Bearer token

    Args:
        payload: JSON document payload (dict or JSON string)
        is_final: Boolean, set to True to submit as Final, False for Draft

    Returns:
        dict with submission result
    """
    import json as _json
    import datetime

    def _serialize(obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    try:
        token = ensure_login()
        if not token:
            return {"status": "error", "message": "Tidak bisa mendapatkan token. Silakan login terlebih dahulu."}

        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"

        # Handle string payload
        if isinstance(payload, str):
            payload = _json.loads(payload)

        # Ensure is_final is string 'true' or 'false' for URL
        final_str = "true" if is_final else "false"
        url = f"{base_url}/openapi/document?isFinal={final_str}"
        headers = build_auth_headers(token)

        # Serialize with date handler, then parse back for requests
        payload_str = _json.dumps(payload, default=_serialize)
        payload_clean = _json.loads(payload_str)

        response = requests.post(url, json=payload_clean, headers=headers)

        try:
            data = response.json()
        except Exception:
            data = response.text

        return {
            "status": "success" if response.status_code == 200 else "error",
            "http_code": response.status_code,
            "data": data
        }

    except requests.exceptions.HTTPError as e:
        frappe.log_error(frappe.get_traceback(), "Send Document Error")
        return {"status": "error", "message": f"HTTP Error: {e.response.status_code} - {e.response.text}"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Send Document Error")
        return {"status": "error", "message": str(e)}
