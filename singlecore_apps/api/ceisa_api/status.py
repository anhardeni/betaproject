"""
CEISA Status & Respon API
=========================

Check document status/response from CEISA API.

Endpoints:
    - GET /openapi/status/{nomorAju}              - Status by Nomor Aju
    - GET /openapi/status?idPerusahaan={npwp}     - Status by NPWP
    - GET /openapi/download-respon/{path}         - Download response file
    - GET /openapi/respon/cetak-formulir/{nomorAju} - Cetak formulir respon
"""

import frappe
import requests
from .auth import get_ceisa_settings, ensure_login, build_auth_headers


@frappe.whitelist()
def get_status_by_nomor_aju(nomor_aju):
    """Get CEISA document status/response by Nomor Aju.

    Endpoint: GET /openapi/status/{nomorAju}
    Requires: Bearer token

    Args:
        nomor_aju: Nomor Aju dokumen pabean (26 digit)

    Returns:
        dict with status response data
    """
    try:
        token = ensure_login()
        if not token:
            return {"status": "error", "message": "Tidak bisa mendapatkan token. Silakan login terlebih dahulu."}

        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"

        url = f"{base_url}/openapi/status/{nomor_aju}"
        headers = build_auth_headers(token)

        response = requests.get(url, headers=headers)

        return {
            "status": "success" if response.status_code == 200 else "error",
            "http_code": response.status_code,
            "data": response.json() if response.content else response.text
        }

    except requests.exceptions.HTTPError as e:
        frappe.log_error(frappe.get_traceback(), "Get Status by Nomor Aju Error")
        return {"status": "error", "message": f"HTTP Error: {e.response.status_code} - {e.response.text}"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Status by Nomor Aju Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_status_by_npwp(npwp):
    """Get CEISA document status/response by NPWP perusahaan.

    Endpoint: GET /openapi/status?idPerusahaan={npwp}
    Requires: Bearer token

    Args:
        npwp: NPWP perusahaan (15 digit)

    Returns:
        dict with list of document statuses for the company
    """
    try:
        token = ensure_login()
        if not token:
            return {"status": "error", "message": "Tidak bisa mendapatkan token. Silakan login terlebih dahulu."}

        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"

        url = f"{base_url}/openapi/status"
        headers = build_auth_headers(token)
        params = {"idPerusahaan": npwp}

        response = requests.get(url, headers=headers, params=params)

        return {
            "status": "success" if response.status_code == 200 else "error",
            "http_code": response.status_code,
            "data": response.json() if response.content else response.text
        }

    except requests.exceptions.HTTPError as e:
        frappe.log_error(frappe.get_traceback(), "Get Status by NPWP Error")
        return {"status": "error", "message": f"HTTP Error: {e.response.status_code} - {e.response.text}"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Status by NPWP Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def download_respon(path):
    """Download response file from CEISA API.

    Endpoint: GET /openapi/download-respon/{path}
    Requires: Bearer token

    The 'path' parameter is obtained from the response of
    get_status_by_nomor_aju() or get_status_by_npwp().

    Args:
        path: File path from status response

    Returns:
        dict with downloaded response data
    """
    try:
        token = ensure_login()
        if not token:
            return {"status": "error", "message": "Tidak bisa mendapatkan token. Silakan login terlebih dahulu."}

        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"

        url = f"{base_url}/openapi/download-respon/{path}"
        headers = build_auth_headers(token)

        response = requests.get(url, headers=headers)

        # Try to parse as JSON, fallback to raw text
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
        frappe.log_error(frappe.get_traceback(), "Download Respon Error")
        return {"status": "error", "message": f"HTTP Error: {e.response.status_code} - {e.response.text}"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Download Respon Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def cetak_formulir(nomor_aju):
    """Cetak formulir respon dokumen pabean.

    Endpoint: GET /openapi/respon/cetak-formulir/{nomorAju}
    Requires: Bearer token

    Args:
        nomor_aju: Nomor Aju dokumen pabean (26 digit)

    Returns:
        dict with formulir data (PDF or response content)
    """
    try:
        token = ensure_login()
        if not token:
            return {"status": "error", "message": "Tidak bisa mendapatkan token. Silakan login terlebih dahulu."}

        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"

        url = f"{base_url}/openapi/respon/cetak-formulir/{nomor_aju}"
        headers = build_auth_headers(token)

        response = requests.get(url, headers=headers)

        # Try to parse as JSON, fallback to raw content
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
        frappe.log_error(frappe.get_traceback(), "Cetak Formulir Error")
        return {"status": "error", "message": f"HTTP Error: {e.response.status_code} - {e.response.text}"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Cetak Formulir Error")
        return {"status": "error", "message": str(e)}
