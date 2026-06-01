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


@frappe.whitelist()
def get_document_detail(jenis_dokumen, nomor_aju, kode_kantor, sync_to_db=False):
    """
    Get CEISA document detail by Path parameters: jenisDokumen, nomorAju, kodeKantor.
    
    Args:
        jenis_dokumen (str): "23" for BC 2.3 or "27" for BC 2.7 or "33" for BC 3.3.
                             Strips "BC" or "BC " prefix automatically.
        nomor_aju (str): 26 digit Nomor Aju
        kode_kantor (str): Kode kantor daftar
        sync_to_db (bool): If True, asynchronously syncs the detail to 'Ceisa Document Detail' staging table.
    
    Returns:
        dict: { status, http_code, data }
    """
    try:
        token = ensure_login()
        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"
        
        # Normalize and clean jenisDokumen (remove "BC" prefix if user includes it)
        clean_jenis = str(jenis_dokumen).upper().replace("BC", "").strip()
        
        # API GET /openapi/document/detail/{jenisDokumen}/{nomorAju}/{kodeKantor}
        url = f"{base_url}/openapi/document/detail/{clean_jenis}/{nomor_aju}/{kode_kantor}"
        headers = build_auth_headers(token)
        
        response = requests.get(url, headers=headers, timeout=(5, 30))
        
        # Handle 401 token expired retry
        if response.status_code == 401:
            frappe.log_error(f"get_document_detail: 401 received, attempting token refresh", "Token Refresh")
            new_token = refresh_token()
            if new_token:
                headers = build_auth_headers(new_token)
                response = requests.get(url, headers=headers, timeout=(5, 30))
                
        result = _parse_response(response)
        
        # If sync requested and response is successful, trigger background sync
        if sync_to_db and result.get("status") == "success":
            # Extract nested 'data' list from response if present
            payload_data = result.get("data")
            if isinstance(payload_data, dict) and "data" in payload_data:
                payload_data = payload_data.get("data")
                
            frappe.enqueue(
                "singlecore_apps.api.ceisa_api.document.sync_ceisa_detail_bg",
                nomor_aju=nomor_aju,
                jenis_dokumen=clean_jenis,
                kode_kantor=kode_kantor,
                api_data=payload_data
            )
            
        return result
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Document Detail Error")
        return {"status": "error", "message": str(e)}


def sync_ceisa_detail_bg(nomor_aju, jenis_dokumen, kode_kantor, api_data):
    """
    Background worker to save CEISA document detail in 'Ceisa Document Detail' staging table.
    """
    try:
        from frappe.utils import now_datetime
        
        # Normalize api_data (can be list of dicts, outer response dict, or direct dict)
        if isinstance(api_data, dict) and "data" in api_data:
            inner_data = api_data.get("data")
        else:
            inner_data = api_data
            
        if isinstance(inner_data, list) and len(inner_data) > 0:
            doc_data = inner_data[0]
        elif isinstance(inner_data, dict):
            doc_data = inner_data
        else:
            doc_data = {}
            
        nomor_daftar = doc_data.get("nomorDaftar")
        tanggal_daftar = doc_data.get("tanggalDaftar")
        
        if frappe.db.exists("Ceisa Document Detail", nomor_aju):
            doc = frappe.get_doc("Ceisa Document Detail", nomor_aju)
        else:
            doc = frappe.new_doc("Ceisa Document Detail")
            doc.nomor_aju = nomor_aju
            
        doc.jenis_dokumen = jenis_dokumen
        doc.kode_kantor = kode_kantor
        doc.nomor_daftar = nomor_daftar
        doc.tanggal_daftar = tanggal_daftar
        doc.raw_json = json.dumps(api_data, indent=2, default=_date_serializer)
        doc.status = "Success"
        doc.retrieved_at = now_datetime()
        doc.message = "Successfully synchronized from CEISA API"
        
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Ceisa Detail BG Sync Error: {nomor_aju}")
        try:
            from frappe.utils import now_datetime
            if frappe.db.exists("Ceisa Document Detail", nomor_aju):
                doc = frappe.get_doc("Ceisa Document Detail", nomor_aju)
            else:
                doc = frappe.new_doc("Ceisa Document Detail")
                doc.nomor_aju = nomor_aju
            doc.jenis_dokumen = jenis_dokumen
            doc.kode_kantor = kode_kantor
            doc.status = "Error"
            doc.retrieved_at = now_datetime()
            doc.message = str(e)
            doc.save(ignore_permissions=True)
            frappe.db.commit()
        except Exception:
            pass

