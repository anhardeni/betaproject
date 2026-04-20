"""
CEISA Document API
==================

Document validation and submission to CEISA API.

Endpoints:
    - POST /openapi/document/check            - Validate JSON document before sending
    - POST /openapi/document?isFinal=false     - Submit document (draft)
    - POST /openapi/document?isFinal=true      - Submit document (final)
"""

import json
import datetime
import frappe
import requests
from .auth import get_ceisa_settings, ensure_login, build_auth_headers, refresh_token


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _date_serializer(obj):
    """JSON serializer that converts date/datetime objects to ISO strings."""
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _clean_payload(payload):
    """Ensure payload is a plain JSON-safe dict (handles str input + date objects)."""
    if isinstance(payload, str):
        payload = json.loads(payload)
    # Round-trip through JSON to coerce all date objects
    return json.loads(json.dumps(payload, default=_date_serializer))


def _post_with_retry(url, payload_clean, token, log_tag):
    """POST to CEISA with automatic one-time 401 token-refresh retry.

    Args:
        url          : Full URL to POST to
        payload_clean: Already-serialized dict payload
        token        : Current Bearer token
        log_tag      : Label used in frappe.log_error on 401

    Returns:
        requests.Response
    """
    headers = build_auth_headers(token)
    response = requests.post(url, json=payload_clean, headers=headers)

    if response.status_code == 401:
        frappe.log_error(f"{log_tag}: 401 received, attempting token refresh", "Token Refresh")
        new_token = refresh_token()
        if new_token:
            headers = build_auth_headers(new_token)
            response = requests.post(url, json=payload_clean, headers=headers)

    return response


def _parse_response(response):
    """Parse a requests.Response into our standard return dict."""
    try:
        data = response.json()
    except Exception:
        data = response.text
    return {
        "status": "success" if response.status_code in [200, 201] else "error",
        "http_code": response.status_code,
        "data": data
    }


# ── Public API functions ────────────────────────────────────────────────────────

@frappe.whitelist()
def check_document(payload):
    """Validate JSON document format before sending to CEISA.

    Endpoint: POST /openapi/document/check
    Requires: Bearer token

    Args:
        payload: JSON document payload (dict or JSON string)

    Returns:
        dict: { status, http_code, data }
    """
    try:
        token = ensure_login()
        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"
        url = f"{base_url}/openapi/document/check"

        response = _post_with_retry(url, _clean_payload(payload), token, "check_document")
        return _parse_response(response)

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
        payload : JSON document payload (dict or JSON string)
        is_final: True = Final submission, False = Draft

    Returns:
        dict: { status, http_code, data }
    """
    try:
        token = ensure_login()
        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"
        final_str = "true" if is_final else "false"
        url = f"{base_url}/openapi/document?isFinal={final_str}"

        response = _post_with_retry(url, _clean_payload(payload), token, "send_document")
        result = _parse_response(response) # hasil: {status, http_code, data}
        
        # -------------------------------------------------------------------
        # 2. FILTER "BEBAS ERROR" (Di sinilah kail otomasi kita pasang)
        # -------------------------------------------------------------------
        # Pastikan kita hanya membuat Log Status JIKA dokumen ini adalah FINAL
        # dan respons dari CEISA menyatakan sukses (status == 'success' atau http_code == 200)
        
        if result.get("http_code") in [200, 201] and result.get("status") != "error":
            
            # Kita harus ekstrak Nomor Aju dari payload karena kita tidak melempar header_doc
            payload_dict = payload if isinstance(payload, dict) else json.loads(payload)
            no_aju_dikirim = payload_dict.get("nomorAju")
            
            if no_aju_dikirim:
                # Ambil dokumen HEADER V21 asli dari database untuk mendapatkan 'company' dan 'kode_dokumen'
                if frappe.db.exists("HEADER V21", no_aju_dikirim):
                    header_doc = frappe.get_doc("HEADER V21", no_aju_dikirim)
                    
                    # PANGGIL FUNGSI THE HANDOFF 
                    from singlecore_apps.singlecore_apps.doctype.header_v21.header_v21 import auto_create_customs_log
                    
                    # Lempar objek dokumen, string payload asli, dan balasan utuh CEISA
                    payload_str = payload if isinstance(payload, str) else json.dumps(payload)
                    response_raw_str = json.dumps(result)
                    
                    # Panggil Pembuatan Log Pabean
                    auto_create_customs_log(header_doc, payload_str, response_raw_str)
        # -------------------------------------------------------------------

        # Kembalikan response normal ke UI
        return result    
        

    except requests.exceptions.HTTPError as e:
        frappe.log_error(frappe.get_traceback(), "Send Document Error")
        return {"status": "error", "message": f"HTTP Error: {e.response.status_code} - {e.response.text}"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Send Document Error")
        return {"status": "error", "message": str(e)}
