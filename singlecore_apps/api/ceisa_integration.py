"""
CEISA Integration - Main Entry Point
=====================================

This module serves as the main entry point for CEISA API integration.
Core API query functions are organized in the ceisa_api/ folder:

    ceisa_api/
    ├── __init__.py   - Package exports
    ├── auth.py       - Login, token caching, header building
    ├── document.py   - check_document / send_document (with 401 auto-retry)
    ├── kurs.py       - Exchange rate queries
    └── status.py     - Document status queries

send_ceisa_document resolves the BC type from HEADER V21 and delegates
everything (serialisation, auth, 401 retry) to send_document().
The export-function mapping is imported from ceisa_export.CEISA_EXPORT_MAP
— the single source of truth shared with check_export_with_ceisa.
"""

import frappe

# Re-export from ceisa_api for backward compatibility
from .ceisa_api.auth import (
    get_ceisa_settings,
    get_cached_token,
    build_auth_headers as _build_auth_headers,
    ensure_login as _ensure_login,
    login_beacukai,
)
from .ceisa_api.document import send_document
from .ceisa_api.kurs import get_kurs
from .ceisa_api.status import get_status_by_nomor_aju, get_status_by_npwp

# Backward compatibility alias
check_ceisa_status = get_status_by_nomor_aju


@frappe.whitelist()
def send_ceisa_document(docname):
    """Dynamically send the correct CEISA document based on kode_dokumen.

    Resolves the BC type from HEADER V21, generates the JSON payload via
    ceisa_export, then delegates send/retry/serialisation to send_document().

    Endpoint (via send_document): POST /openapi/document?isFinal=false
    """
    try:
        # Import here to avoid circular imports at module level
        from .ceisa_export import CEISA_EXPORT_MAP

        doc = frappe.get_doc("HEADER V21", docname)
        bc_type = str(doc.kode_dokumen or "")

        export_func = CEISA_EXPORT_MAP.get(bc_type)
        if not export_func:
            return {"status": "error", "message": f"Document type '{bc_type}' is not supported for automatic sending."}

        payload = export_func(docname)
        if isinstance(payload, dict) and payload.get("status") == "error":
            return payload

        # Delegate to send_document — handles token, serialisation, and 401 retry
        result = send_document(payload, is_final=False)

        # ── Create / update Customs Status Log after successful submission ──
        if result.get("status") == "success":
            try:
                response_data = result.get("data") or {}
                if isinstance(response_data, str):
                    import json as _json
                    try:
                        response_data = _json.loads(response_data)
                    except Exception:
                        response_data = {}

                no_aju = (
                    response_data.get("nomorAju")
                    or response_data.get("nomor_aju")
                    or doc.nomoraju
                    or ""
                )
                no_aju = str(no_aju).strip()

                if no_aju:
                    from singlecore_apps.singlecore_apps.doctype.customs_status_log.customs_status_log import (
                        create_or_update_log,
                    )
                    create_or_update_log(
                        docname=docname,
                        no_aju=no_aju,
                        payload=payload,
                        bc_type=bc_type,
                    )
            except Exception:
                # Non-blocking — log the error but still return success to the caller
                frappe.log_error(
                    frappe.get_traceback(),
                    f"send_ceisa_document: create_or_update_log failed [{docname}]"
                )

        # Rename 'data' → 'response' for JS backward compatibility
        result["response"] = result.pop("data", None)
        return result

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Send CEISA Document Error")
        return {"status": "error", "message": str(e)}
