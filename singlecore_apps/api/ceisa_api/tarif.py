"""
CEISA Tarif HS API
==================

Query tarif HS code and lartas (larangan/pembatasan) from CEISA API.

Endpoints:
    - GET /openapi/tarif-hs?kodeHs={kodeHs}&tanggal={tanggal}
    - GET /openapi/hs-lartas?kodeHs={kodeHs}
"""

import frappe
import requests
from .auth import get_ceisa_settings, ensure_login, build_auth_headers


@frappe.whitelist()
def get_tarif_hs(kode_hs, tanggal=None):
    """Get tarif HS code from CEISA API.

    Endpoint: GET /openapi/tarif-hs?kodeHs={kodeHs}&tanggal={tanggal}
    Requires: Bearer token

    Args:
        kode_hs: Kode HS (e.g. "0901110000")
        tanggal: Tanggal referensi format YYYY-MM-DD (default: today)

    Returns:
        dict with tarif HS data
    """
    try:
        token = ensure_login()
        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"

        if not tanggal:
            from datetime import date
            tanggal = date(2022, 7, 20).strftime("%Y-%m-%d")

        url = f"{base_url}/openapi/tarif-hs"
        headers = build_auth_headers(token)
        params = {
            "kodeHs": kode_hs,
            "tanggal": tanggal
        }

        response = requests.get(url, headers=headers, params=params)

        return {
            "status": "success" if response.status_code == 200 else "error",
            "http_code": response.status_code,
            "data": response.json() if response.content else response.text
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Tarif HS Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_lartas_hscode(kode_hs):
    """Check larangan/pembatasan (lartas) for HS code.

    Endpoint: GET /openapi/hs-lartas?kodeHs={kodeHs}
    Requires: Bearer token

    Args:
        kode_hs: Kode HS (e.g. "0901110000")

    Returns:
        dict with lartas data
    """
    try:
        token = ensure_login()
        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"

        url = f"{base_url}/openapi/hs-lartas"
        headers = build_auth_headers(token)
        params = {"kodeHs": kode_hs}

        response = requests.get(url, headers=headers, params=params)

        return {
            "status": "success" if response.status_code == 200 else "error",
            "http_code": response.status_code,
            "data": response.json() if response.content else response.text
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Lartas HS Error")
        return {"status": "error", "message": str(e)}
