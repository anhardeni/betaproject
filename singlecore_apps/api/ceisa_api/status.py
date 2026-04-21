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
    """Get CEISA document status/response by Nomor Aju."""
    try:
        token = ensure_login()
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
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Status by Nomor Aju Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_status_by_npwp(npwp):
    """Get CEISA document status/response by NPWP perusahaan."""
    try:
        token = ensure_login()
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
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Status by NPWP Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def download_respon(path):
    """
    Download binary response from CEISA.
    Attempts multiple URL patterns and both Authenticated/Unauthenticated modes.
    """
    try:
        from .auth import ensure_login, build_auth_headers
        token = ensure_login()
        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"

        # Multi-check pola URL
        patterns = [
            f"{base_url}/openapi/download-respon?path={path}",
            f"{base_url}/openapi/{path}",
            f"{base_url}/{path}",
        ]
        
        last_error_info = ""
        
        # Coba tiap pola dengan 2 kondisi: Pakai Token & Tanpa Token
        for url in patterns:
            for use_token in [True, False]:
                try:
                    headers = build_auth_headers(token if use_token else None)
                    if "?" in url:
                        base, query = url.split("?", 1)
                        p_name, p_val = query.split("=", 1)
                        r = requests.get(base, params={p_name: p_val}, headers=headers, timeout=10)
                    else:
                        r = requests.get(url, headers=headers, timeout=10)
                    
                    if r.status_code == 200:
                        # Success case
                        return {
                            "status": "success",
                            "data": r.content,
                            "url": r.url,
                            "mode": "Token" if use_token else "API-Key Only"
                        }
                    else:
                        # Log but continue
                        last_error_info = f"URL: {url} | Status: {r.status_code} | Mode: {'Token' if use_token else 'API-Key'}"
                except Exception as e:
                    last_error_info = f"URL: {url} | Exception: {str(e)}"
                    continue

        # If we reach here, all failed
        return {
            "status": "error",
            "message": f"Download Gagal. Terakhir: {last_error_info}"
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "download_respon System Error")
        return {"status": "error", "message": f"System Error: {str(e)}"}
