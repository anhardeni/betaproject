"""
CEISA Manifes BC11 API
======================

Query manifes BC11 data from CEISA API.

Endpoint:
    - GET /openapi/manifes-bc11?noHostBl={noHostBl}&tglHostBl={tglHostBl}&kodeKantor={kodeKantor}&nama={nama}
"""

import frappe
import requests
from .auth import get_ceisa_settings, ensure_login, build_auth_headers


@frappe.whitelist()
def get_manifes(no_host_bl, tgl_host_bl, kode_kantor, nama_perusahaan):
    """Get manifes BC11 data from CEISA API.

    Endpoint: GET /openapi/manifes-bc11?noHostBl={noHostBl}&tglHostBl={tglHostBl}&kodeKantor={kodeKantor}&nama={nama}
    Requires: Bearer token

    Args:
        no_host_bl: Nomor House BL
        tgl_host_bl: Tanggal House BL format YYYY-MM-DD
        kode_kantor: Kode kantor pabean
        nama_perusahaan: Nama perusahaan

    Returns:
        dict with manifes BC11 data
    """
    try:
        token = ensure_login()
        if not token:
            return {"status": "error", "message": "Tidak bisa mendapatkan token. Silakan login terlebih dahulu."}

        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"

        url = f"{base_url}/openapi/manifes-bc11"
        headers = build_auth_headers(token)
        params = {
            "noHostBl": no_host_bl,
            "tglHostBl": tgl_host_bl,
            "kodeKantor": kode_kantor,
            "nama": nama_perusahaan
        }

        response = requests.get(url, headers=headers, params=params)

        return {
            "status": "success" if response.status_code == 200 else "error",
            "http_code": response.status_code,
            "data": response.json() if response.content else response.text
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Manifes BC11 Error")
        return {"status": "error", "message": str(e)}
