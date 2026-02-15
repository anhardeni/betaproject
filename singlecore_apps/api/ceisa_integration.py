"""
CEISA Integration - Main Entry Point
=====================================

This module serves as the main entry point for CEISA API integration.
Core API query functions are organized in the ceisa_api/ folder:

    ceisa_api/
    ├── __init__.py   - Package exports
    ├── auth.py       - Login, token caching, header building
    ├── kurs.py       - Exchange rate (kurs) queries
    └── status.py     - Document status queries (by Nomor Aju / NPWP)

This file retains the send_ceisa_document function and re-exports
auth functions for backward compatibility.
"""

import frappe
import requests
from . import ceisa_export

# Re-export from ceisa_api for backward compatibility
from .ceisa_api.auth import (
    get_ceisa_settings,
    get_cached_token,
    build_auth_headers as _build_auth_headers,
    ensure_login as _ensure_login,
    login_beacukai,
)
from .ceisa_api.kurs import get_kurs
from .ceisa_api.status import get_status_by_nomor_aju, get_status_by_npwp

# Backward compatibility alias
check_ceisa_status = get_status_by_nomor_aju


@frappe.whitelist()
def send_ceisa_document(docname):
    """Dynamically sends the correct CEISA document based on kode_dokumen.

    Endpoint: POST /openapi/document?isFinal=false
    """
    token = _ensure_login()
    if not token:
        return {"status": "error", "message": "Please login to Beacukai first."}

    try:
        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"

        # Get the document to determine its type
        doc = frappe.get_doc("HEADER V21", docname)
        bc_type = doc.kode_dokumen

        # Mapping of document codes to their export functions
        EXPORT_MAP = {
            "16": ceisa_export.get_ceisa_bc16_json,
            "20": ceisa_export.get_ceisa_bc20_json,
            "23": ceisa_export.get_ceisa_bc23_json,
            "25": ceisa_export.get_ceisa_bc25_json,
            "27": ceisa_export.get_ceisa_bc27_json,
            "28": ceisa_export.get_ceisa_bc28_json,
            "30": ceisa_export.get_ceisa_bc30_json,
            "33": ceisa_export.get_ceisa_bc33_json,
            "40": ceisa_export.get_ceisa_bc40_json,
            "41": ceisa_export.get_ceisa_bc41_json,
            "261": ceisa_export.get_ceisa_bc261_json,
            "262": ceisa_export.get_ceisa_bc262_json,
            "331": ceisa_export.get_ceisa_p3bet_json,
            "511": ceisa_export.get_ceisa_ftz011_json,
            "512": ceisa_export.get_ceisa_ftz012_json,
            "513": ceisa_export.get_ceisa_ftz013_json
        }

        export_func = EXPORT_MAP.get(str(bc_type))
        if not export_func:
            return {"status": "error", "message": f"Document type {bc_type} is not supported for automatic sending yet."}

        # Generate payload
        payload = export_func(docname)

        if isinstance(payload, dict) and payload.get("status") == "error":
            return payload

        url = f"{base_url}/openapi/document?isFinal=false"
        headers = _build_auth_headers(token)

        response = requests.post(url, json=payload, headers=headers)

        return {
            "status": "success" if response.status_code == 200 else "error",
            "http_code": response.status_code,
            "response": response.json() if response.content else response.text
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Send CEISA Document Error")
        return {"status": "error", "message": str(e)}
