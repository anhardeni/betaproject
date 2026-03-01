# apps/singlecore_apps/singlecore_apps/mcp.py
#
# PENTING: File ini di-import otomatis oleh Frappe saat load_assets().
# Jangan taruh import yang bisa gagal di top-level, karena akan CRASH seluruh app.

import frappe
import datetime
from typing import List, Dict, Any, Optional

# --- Coba import frappe_mcp (opsional) ---
try:
    import frappe_mcp
    mcp = frappe_mcp.MCP("singlecore-mcp")
    HAS_MCP = True
except ImportError:
    HAS_MCP = False
    mcp = None
    frappe.logger().warning("frappe_mcp not installed – MCP tools disabled")


# ──────────────────────────────────────────
# Helper: no-op decorator jika MCP tidak tersedia
# ──────────────────────────────────────────
def _noop_decorator(**kwargs):
    """Fallback decorator yang tidak melakukan apa-apa."""
    def wrapper(fn):
        return fn
    return wrapper

mcp_tool = mcp.tool if HAS_MCP else _noop_decorator
mcp_register = mcp.register if HAS_MCP else _noop_decorator


# ──────────────────────────────────────────
# Basic whitelisted API
# ──────────────────────────────────────────
@frappe.whitelist()
def hello(name: str):
    """Contoh tool sederhana - callable via API"""
    return f"Hello {name}!"


@mcp_register()
@frappe.whitelist()
def handle_mcp():
    """Handle request MCP"""
    if not HAS_MCP:
        return {"error": "frappe_mcp is not installed"}
    try:
        return mcp.serve()
    except Exception as e:
        frappe.log_error(f"MCP Error: {e}", "MCP Handler")
        return {"error": str(e)}


# ──────────────────────────────────────────
# MCP Tools
# ──────────────────────────────────────────
@mcp_tool(description="List PIB terbaru")
@frappe.whitelist()
def list_dokumen_terbaru(limit: int = 10) -> list:
    """
    Daftar PIB (Pemberitahuan Impor Barang) terbaru.

    Args:
        limit: Jumlah record
    """
    return frappe.get_all("HEADER V21",
        fields=["name", "nomoraju", "kode_dokumen", "kode_kantor"],
        limit=limit,
        order_by="creation desc"
    )


@mcp_tool(description="Get tarif HS code dari CEISA API")
@frappe.whitelist()
def mcp_get_tarif_hs(kode_hs: str, tanggal: str = "2022-07-20") -> dict:
    """
    Query tarif berdasarkan kode HS dari CEISA.

    Args:
        kode_hs: Kode HS (contoh: "72109000")
        tanggal: Tanggal referensi YYYY-MM-DD (default: 2022-07-20)
    """
    from singlecore_apps.api.ceisa_api.tarif import get_tarif_hs
    return get_tarif_hs(kode_hs, tanggal)


@mcp_tool(description="Get kurs valuta asing dari CEISA API (endpoint: /openapi/kurs/{currency})")
@frappe.whitelist()
def mcp_get_kurs(currency: str = "USD") -> dict:
    """
    Query kurs valuta asing yang berlaku dari CEISA.

    Args:
        currency: Kode mata uang (default: USD). Contoh: "USD", "EUR", "SGD", "JPY", "CNY"
    """
    from singlecore_apps.api.ceisa_api.kurs import get_kurs
    return get_kurs(currency)



@mcp_tool(description="Cek status dokumen CEISA by Nomor Aju")
@frappe.whitelist()
def mcp_get_status(nomor_aju: str) -> dict:
    """
    Cek status/respon dokumen pabean berdasarkan Nomor Aju.

    Args:
        nomor_aju: Nomor Aju dokumen (26 digit)
    """
    from singlecore_apps.api.ceisa_api.status import get_status_by_nomor_aju
    return get_status_by_nomor_aju(nomor_aju)


@mcp_tool(description="Cek status dokumen CEISA by NPWP perusahaan")
@frappe.whitelist()
def mcp_get_status_by_npwp(npwp: str) -> dict:
    """
    Cek status/respon dokumen pabean berdasarkan NPWP perusahaan.

    Args:
        npwp: NPWP perusahaan (15 digit)
    """
    from singlecore_apps.api.ceisa_api.status import get_status_by_npwp
    return get_status_by_npwp(npwp)


@mcp_tool(description="Cek lartas (larangan/pembatasan) HS code dari CEISA API")
@frappe.whitelist()
def mcp_get_lartas_hscode(kode_hs: str) -> dict:
    """
    Cek larangan/pembatasan untuk kode HS.

    Args:
        kode_hs: Kode HS (contoh: "72109090")
    """
    from singlecore_apps.api.ceisa_api.tarif import get_lartas_hscode
    return get_lartas_hscode(kode_hs)


@mcp_tool(description="Get data manifes BC11 dari CEISA API")
@frappe.whitelist()
def mcp_get_manifes(no_host_bl: str, tgl_host_bl: str, kode_kantor: str, nama_perusahaan: str) -> dict:
    """
    Query manifes BC11 dari CEISA.

    Args:
        no_host_bl: Nomor House BL
        tgl_host_bl: Tanggal House BL (YYYY-MM-DD)
        kode_kantor: Kode kantor pabean
        nama_perusahaan: Nama perusahaan
    """
    from singlecore_apps.api.ceisa_api.manifes import get_manifes
    return get_manifes(no_host_bl, tgl_host_bl, kode_kantor, nama_perusahaan)


@mcp_tool(description="Download file respon dokumen CEISA")
@frappe.whitelist()
def mcp_download_respon(path: str) -> dict:
    """
    Download file respon dari CEISA. Path didapat dari hasil get_status.

    Args:
        path: Path file respon (dari response status)
    """
    from singlecore_apps.api.ceisa_api.status import download_respon
    return download_respon(path)


@mcp_tool(description="Cetak formulir respon dokumen pabean")
@frappe.whitelist()
def mcp_cetak_formulir(nomor_aju: str) -> dict:
    """
    Cetak formulir respon dokumen pabean.

    Args:
        nomor_aju: Nomor Aju dokumen (26 digit)
    """
    from singlecore_apps.api.ceisa_api.status import cetak_formulir
    return cetak_formulir(nomor_aju)


@mcp_tool(description="Validasi format JSON dokumen sebelum kirim ke CEISA")
@frappe.whitelist()
def mcp_check_document(payload: str) -> dict:
    """
    Validasi format JSON dokumen sebelum dikirim ke CEISA.

    Args:
        payload: JSON string dokumen pabean
    """
    from singlecore_apps.api.ceisa_api.document import check_document
    return check_document(payload)


@mcp_tool(description="Kirim dokumen pabean ke CEISA (Draft atau Final)")
@frappe.whitelist()
def mcp_send_document(payload: str, is_final: bool = False) -> dict:
    """
    Kirim dokumen pabean ke CEISA. Pastikan sudah dicheck sebelumnya.

    Args:
        payload: JSON string dokumen pabean
        is_final: Set ke True untuk kirim sebagai Final, False untuk Draft (default: False)
    """
    from singlecore_apps.api.ceisa_api.document import send_document
    return send_document(payload, is_final)