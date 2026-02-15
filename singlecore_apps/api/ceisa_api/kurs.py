"""
CEISA Kurs API
==============

Get exchange rates (kurs) from CEISA API.
Endpoint: GET /openapi/kurs/{currency}
"""

import frappe
import requests
from .auth import get_ceisa_settings, ensure_login, build_auth_headers


@frappe.whitelist()
def get_kurs(currency="EUR"):
    """Get exchange rate (kurs) from CEISA API.

    Endpoint: GET /openapi/kurs/{currency}
    Requires: Bearer token

    Args:
        currency: Currency code (default: USD)

    Returns:
        dict with kurs data, e.g.:
        {
            "status": "success",
            "data": {
                "status": "true",
                "message": "success",
                "data": [{"nilaiKurs": "16813"}]
            }
        }
    """
    try:
        token = ensure_login()
        if not token:
            return {"status": "error", "message": "Tidak bisa mendapatkan token. Silakan login terlebih dahulu."}

        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"

        url = f"{base_url}/openapi/kurs/{currency}"
        headers = build_auth_headers(token)

        response = requests.get(url, headers=headers)

        return {
            "status": "success" if response.status_code == 200 else "error",
            "http_code": response.status_code,
            "data": response.json() if response.content else response.text
        }

    except requests.exceptions.HTTPError as e:
        frappe.log_error(frappe.get_traceback(), "Get Kurs Error")
        return {"status": "error", "message": f"HTTP Error: {e.response.status_code} - {e.response.text}"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Kurs Error")
        return {"status": "error", "message": str(e)}
