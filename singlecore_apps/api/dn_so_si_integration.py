# -*- coding: utf-8 -*-
# PATCH: Delivery Note -> HEADER V21 (Lengkap + Anti Duplikasi)
# Author: Mohammad Anhar Deni Purnama (AnharDeni) + M365 Copilot assist
# License: MIT

import frappe
from frappe import _
from frappe.utils import today, flt, cint

from singlecore_apps.api.so_si_integration import (
    get_company_entitas_data,
    get_customer_entitas_data,
    get_ceisa_uom,
    generate_nomor_aju
)


# ═══════════════════════════════════════════════════════════════════
# VALIDASI DELIVERY NOTE (tanpa verified flag)
# ═══════════════════════════════════════════════════════════════════

def validate_delivery_note_full(dn_name):
    """Validasi DN: wajib docstatus=1 dan memiliki items."""
    if not frappe.db.exists("Delivery Note", dn_name):
        return False, _("Delivery Note {0} tidak ditemukan").format(dn_name), None

    dn = frappe.get_doc("Delivery Note", dn_name)

    if dn.docstatus != 1:
        return False, _("Delivery Note {0} belum disubmit").format(dn_name), None

    if not dn.items:
        return False, _("Delivery Note {0} tidak memiliki item").format(dn_name), None

    return True, "OK", dn


# ═══════════════════════════════════════════════════════════════════
# ANTI-DUPLIKASI DN SECARA GLOBAL
# ═══════════════════════════════════════════════════════════════════

def dn_used_in_other_header(dn_name, current_header=None):
    """
    Cek apakah DN sudah tercatat di child table 'dokumen' milik HEADER V21 lain.
    Return: (used: bool, header_name: str|None)
    """
    if not frappe.db.exists("Delivery Note", dn_name):
        return False, None

    meta = frappe.get_meta("HEADER V21")
    child_field = meta.get_field("dokumen")
    child_dt = child_field.options if child_field else None
    if not child_dt:
        return False, None  # fallback aman

    rows = frappe.get_all(
        child_dt,
        filters={"nomor_dokumen": dn_name},
        fields=["name", "parent"],
        limit=10
    )
    if not rows:
        return False, None

    for r in rows:
        parent = r.get("parent")
        if not current_header or parent != current_header:
            return True, parent

    return False, None


# ═══════════════════════════════════════════════════════════════════
# HELPER: ADD SOURCE DOKUMEN (extend utk DN)
# ═══════════════════════════════════════════════════════════════════

def add_source_to_dokumen(header, source_doc, source_type, kode_dokumen_sumber_dn=None):
    """
    Tambah entri ke child table DOKUMEN untuk SO/SI/DN.
    Backward compatible dengan pemanggilan lama (param tambahan opsional).
    """
    existing_seri = len(header.dokumen) if header.dokumen else 0
    next_seri = existing_seri + 1

    if source_type == "so":
        kode_dok = "999"               # kebiasaan internal utk Sales Order
        tanggal = source_doc.transaction_date
    elif source_type == "si":
        kode_dok = "380"               # Commercial Invoice
        tanggal = source_doc.posting_date
    elif source_type == "dn":
        kode_dok = kode_dokumen_sumber_dn or "999"  # configurable
        tanggal = source_doc.posting_date
    else:
        kode_dok = "999"
        tanggal = getattr(source_doc, "posting_date", today())

    dok = header.append("dokumen")
    dok.seri = next_seri
    dok.kode_dokumen = kode_dok
    dok.nomor_dokumen = source_doc.name
    dok.tanggal_dokumen = tanggal


# ═══════════════════════════════════════════════════════════════════
# HELPER: RESOLVE CURRENCY UNTUK DN
# ═══════════════════════════════════════════════════════════════════

def resolve_currency_for_dn(dn_doc, price_list=None):
    """
    Urutan sumber currency:
    1) Sales Invoice yang terkait DN (jika ada)
    2) Sales Order terkait (per item → parent)
    3) Price List (jika diberikan)
    4) Default Company Currency
    """
    # 1) dari linked Sales Invoice (via item against_sales_invoice)
    si_name = frappe.db.get_value(
        "Delivery Note Item",
        {"parent": dn_doc.name, "against_sales_invoice": ["is", "set"]},
        "against_sales_invoice"
    )
    if si_name and frappe.db.exists("Sales Invoice", si_name):
        si_cur = frappe.db.get_value("Sales Invoice", si_name, "currency")
        if si_cur:
            return si_cur

    # 2) dari linked Sales Order
    for it in dn_doc.items:
        so_name = getattr(it, "against_sales_order", None) or \
                  (frappe.db.get_value("Sales Order Item", it.so_detail, "parent") if it.get("so_detail") else None)
        if so_name:
            so_cur = frappe.db.get_value("Sales Order", so_name, "currency")
            if so_cur:
                return so_cur

    # 3) dari Price List
    if price_list:
        plc = frappe.db.get_value("Price List", price_list, "currency")
        if plc:
            return plc

    # 4) default company
    return frappe.db.get_value("Company", dn_doc.company, "default_currency") or "IDR"


# ═══════════════════════════════════════════════════════════════════
# HELPER: RESOLVE RATE/AMOUNT UNTUK DN ITEM (maksimal)
# ═══════════════════════════════════════════════════════════════════

def resolve_rate_amount_for_dn_item(dn_item, header_currency, price_list=None, rate_field=None):
    """
    Urutan prioritas nilai item:
    1) Sales Invoice Item (si_detail) → rate/amount
    2) Sales Order Item (so_detail atau match parent+item_code) → rate
    3) Custom rate field di DN Item (rate_field)
    4) Item Price pada price_list → price_list_rate
    5) 0 + warning
    Return: (rate, amount, warning_or_None)
    """
    # 1) Sales Invoice Item
    si_item_name = getattr(dn_item, "si_detail", None)
    if si_item_name and frappe.db.exists("Sales Invoice Item", si_item_name):
        row = frappe.db.get_value("Sales Invoice Item", si_item_name, ["rate", "amount"], as_dict=1)
        if row:
            return flt(row.rate), flt(row.amount), None

    # 2) Sales Order Item
    so_item_name = getattr(dn_item, "so_detail", None)
    if not so_item_name and getattr(dn_item, "against_sales_order", None):
        so_item_name = frappe.db.get_value(
            "Sales Order Item",
            {"parent": dn_item.against_sales_order, "item_code": dn_item.item_code},
            "name"
        )
    if so_item_name and frappe.db.exists("Sales Order Item", so_item_name):
        rate = flt(frappe.db.get_value("Sales Order Item", so_item_name, "rate") or 0)
        return rate, rate * flt(dn_item.qty), None

    # 3) Custom rate field di DN Item
    if rate_field and dn_item.get(rate_field) is not None:
        try:
            rate = flt(dn_item.get(rate_field))
            return rate, rate * flt(dn_item.qty), None
        except Exception:
            pass

    # 4) Item Price (Price List)
    if price_list:
        ip = frappe.db.get_value(
            "Item Price",
            {"price_list": price_list, "item_code": dn_item.item_code},
            ["price_list_rate"],
            as_dict=1
        )
        if ip and ip.get("price_list_rate") is not None:
            rate = flt(ip["price_list_rate"])
            return rate, rate * flt(dn_item.qty), None

    # 5) Fallback 0
    warn = f"{dn_item.item_code}: Tidak ditemukan rate (SI/SO/Custom/Price List). Di-set 0."
    return 0.0, 0.0, warn


# ═══════════════════════════════════════════════════════════════════
# HELPER: MAP DN ITEM → BARANG V1 (kaya data)
# ═══════════════════════════════════════════════════════════════════

def map_dn_item_to_barang_rich(
    dn_item, seri_barang, header_name, header_currency,
    default_coo="ID", price_list=None, rate_field=None
):
    warnings = []
    item_doc = frappe.get_doc("Item", dn_item.item_code) if frappe.db.exists("Item", dn_item.item_code) else None

    # HS dengan validasi referensi
    hs_code = ""
    if item_doc:
        hs_code = item_doc.get("customs_tariff_number") or item_doc.get("custom_hs_code") or item_doc.get("hs_code") or ""
    validated_hs = ""
    if hs_code:
        clean = hs_code.replace(".", "").replace(" ", "").strip()
        if frappe.db.exists("Referensi HS 2022 v1", clean):
            validated_hs = clean
        else:
            partial = clean[:8] if len(clean) >= 8 else clean
            if frappe.db.exists("Referensi HS 2022 v1", partial):
                validated_hs = partial
            else:
                warnings.append(f"{dn_item.item_code}: HS '{hs_code}' tidak ditemukan di referensi")
    else:
        warnings.append(f"{dn_item.item_code}: Tidak ada HS code di master Item")

    # COO
    coo = (item_doc.get("country_of_origin") if item_doc else "") or default_coo
    if len(coo) > 2:
        code = frappe.db.get_value("Country", coo, "code") or default_coo
        coo = (code or default_coo).upper()[:2]

    # UOM
    uom = item_doc.stock_uom if item_doc else (dn_item.uom or "Nos")
    ceisa_uom = get_ceisa_uom(uom)

    # Netto (qty * weight_per_unit; fallback 1 jika kosong)
    wpu = flt(item_doc.get("weight_per_unit") or 0) if item_doc else 0
    netto = flt(dn_item.qty) * (wpu if wpu > 0 else 1.0)
    netto = flt(netto, 4)

    # Nilai (rate & amount)
    rate, amount, warn = resolve_rate_amount_for_dn_item(
        dn_item, header_currency, price_list=price_list, rate_field=rate_field
    )
    if warn:
        warnings.append(warn)

    uraian = dn_item.item_name or (item_doc.item_name if item_doc else dn_item.item_code)
    merek = (item_doc.get("brand") or item_doc.get("customs_brand") or "") if item_doc else ""
    tipe = (item_doc.get("custom_type") or "") if item_doc else ""

    barang_data = {
        "nomoraju": header_name,
        "seri_barang": seri_barang,
        "hs": validated_hs,
        "kode_barang": dn_item.item_code,
        "uraian": uraian,
        "merek": merek,
        "tipe": tipe,
        "spesifikasi_lain": (dn_item.description or "")[:200] if getattr(dn_item, "description", None) else "",
        "kode_satuan": ceisa_uom,
        "jumlah_satuan": flt(dn_item.qty, 4),
        "netto": netto,
        # Untuk ekspor, field 'cif' kita isi nilai FOB/amount baris agar konsisten dengan existing.
        "cif": flt(amount, 2),
        "harga_satuan": flt(rate, 4),
        "kode_negara_asal": coo,
        "kode_kondisi_barang": "1",
    }
    return barang_data, warnings


# ═══════════════════════════════════════════════════════════════════
# API: BUAT HEADER V21 DARI DELIVERY NOTE (Lengkap + Anti Duplikasi)
# ═══════════════════════════════════════════════════════════════════

@frappe.whitelist()
def make_header_v21_from_dn(
    dn_name,
    kode_dokumen="30",
    kode_kantor=None,
    price_list=None,
    rate_field=None,
    kode_dokumen_sumber_dn=None,
    incoterm_field_dn=None,         # contoh: "custom_incoterm"
    port_loading_field=None,        # contoh: "custom_port_loading"
    port_destination_field=None,    # contoh: "custom_port_destination"
    vessel_field=None,              # contoh: "custom_vessel_name"
    voyage_no_field=None,           # contoh: "custom_voyage_no"
    transport_mode_field=None,      # contoh: "custom_transport_mode"
    # Guard anti duplikasi
    block_duplicate_globally=True,
    force=False
):
    """Create HEADER V21 dari satu DN, tarik data selengkap mungkin + blokir duplikasi global."""
    valid, msg, dn = validate_delivery_note_full(dn_name)
    if not valid:
        return {"status": "error", "message": msg}

    # Guard: duplikasi global
    if block_duplicate_globally and not force:
        used, other_header = dn_used_in_other_header(dn_name)
        if used:
            return {
                "status": "error",
                "message": _("DN {0} sudah pernah diimport ke HEADER {1}. Duplikasi diblokir.").format(dn_name, other_header)
            }

    try:
        nomor_aju = generate_nomor_aju([dn_name], "dn", kode_dokumen)

        header = frappe.new_doc("HEADER V21")
        header.kode_dokumen = kode_dokumen
        header.kode_kantor = (kode_kantor or
                              frappe.db.get_value("HEADER V21", {}, "kode_kantor", order_by="creation desc") or
                              "040300")
        header.kode_valuta = resolve_currency_for_dn(dn, price_list=price_list)
        header.tanggal_pernyataan = today()
        header.nama_pernyataan = dn.customer_name or dn.customer
        header.kota_pernyataan = "Jakarta"

        # Optional mapping dari DN custom fields
        if incoterm_field_dn and hasattr(dn, incoterm_field_dn):
            header.kode_incoterm = getattr(dn, incoterm_field_dn)
        if port_loading_field and hasattr(dn, port_loading_field):
            header.kode_pelabuhan_muat = getattr(dn, port_loading_field)
        if port_destination_field and hasattr(dn, port_destination_field):
            header.kode_pelabuhan_tujuan = getattr(dn, port_destination_field)

        # Map Vessel/Transport info ke child table PENGANGKUT
        if vessel_field or voyage_no_field or transport_mode_field:
            p = header.append("pengangkut")
            p.seri_pengangkut = 1
            if vessel_field and hasattr(dn, vessel_field):
                p.nama_pengangkut = getattr(dn, vessel_field)
            if voyage_no_field and hasattr(dn, voyage_no_field):
                p.nomor_pengangkut = getattr(dn, voyage_no_field)
            if transport_mode_field and hasattr(dn, transport_mode_field):
                p.kode_cara_angkut = getattr(dn, transport_mode_field)

        header.insert(ignore_permissions=True)
        header_name = header.name
        frappe.db.set_value("HEADER V21", header_name, "nomoraju", nomor_aju)

        # ENTITAS
        company_data = get_company_entitas_data(dn.company)
        if company_data:
            e3 = header.append("entitas"); e3.seri = 1; e3.kode_entitas = "3"
            for k, v in company_data.items():
                if hasattr(e3, k): setattr(e3, k, v)
        customer_data = get_customer_entitas_data(dn.customer)
        if customer_data:
            e4 = header.append("entitas"); e4.seri = 2; e4.kode_entitas = "4"
            for k, v in customer_data.items():
                if hasattr(e4, k): setattr(e4, k, v)
        if company_data:
            e7 = header.append("entitas"); e7.seri = 3; e7.kode_entitas = "7"
            for k, v in company_data.items():
                if hasattr(e7, k): setattr(e7, k, v)

        # DOKUMEN: DN + SI + SO
        add_source_to_dokumen(header, dn, "dn", kode_dokumen_sumber_dn=kode_dokumen_sumber_dn)

        # Sales Invoice(s) terkait DN (jika ada)
        si_names = set()
        for it in dn.items:
            if it.get("against_sales_invoice"):
                si_names.add(it.against_sales_invoice)
        for si in si_names:
            if frappe.db.exists("Sales Invoice", si):
                si_doc = frappe.get_doc("Sales Invoice", si)
                add_source_to_dokumen(header, si_doc, "si")

        # Sales Order(s) terkait DN (jika ada)
        so_names = set()
        for it in dn.items:
            so_parent = None
            if it.get("against_sales_order"):
                so_parent = it.against_sales_order
            elif it.get("so_detail"):
                so_parent = frappe.db.get_value("Sales Order Item", it.so_detail, "parent")
            if so_parent:
                so_names.add(so_parent)
        for so in so_names:
            if frappe.db.exists("Sales Order", so):
                so_doc = frappe.get_doc("Sales Order", so)
                add_source_to_dokumen(header, so_doc, "so")

        # BARANG V1
        total_value = 0.0
        total_netto = 0.0
        warnings_all = []
        seri = 1
        header_currency = header.kode_valuta

        for it in dn.items:
            barang_data, warns = map_dn_item_to_barang_rich(
                it, seri, header_name, header_currency,
                default_coo="ID", price_list=price_list, rate_field=rate_field
            )
            warnings_all.extend(warns or [])
            barang = frappe.new_doc("BARANG V1")
            for k, v in barang_data.items():
                if hasattr(barang, k): setattr(barang, k, v)
            barang.insert(ignore_permissions=True)

            total_value += flt(barang.cif)
            total_netto += flt(barang.netto)
            seri += 1

        # Update totals
        header.nilai_barang = flt(total_value, 2)
        header.cif = flt(total_value, 2)
        header.netto = flt(total_netto, 4)
        header.bruto = flt(total_netto * 1.05, 4)  # default 5% di atas netto
        header.save(ignore_permissions=True)

        # (Opsional) Lock DN ke HEADER jika ada custom field 'custom_header_v21'
        if frappe.db.has_column("Delivery Note", "custom_header_v21"):
            frappe.db.set_value("Delivery Note", dn_name, "custom_header_v21", header_name, update_modified=False)

        frappe.db.commit()

        message = _("HEADER V21 berhasil dibuat dari Delivery Note {0} dengan {1} barang").format(dn_name, seri - 1)
        if warnings_all:
            message += "<br><br><strong>⚠️ Peringatan:</strong><br>" + "<br>".join(warnings_all[:5])
            if len(warnings_all) > 5:
                message += f"<br>...dan {len(warnings_all) - 5} item lainnya"

        return {
            "status": "success",
            "header_name": header_name,
            "nomor_aju": nomor_aju,
            "barang_count": seri - 1,
            "total_value": total_value,
            "message": message,
            "warnings": warnings_all
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Make HEADER V21 from DN (Rich) Error")
        return {"status": "error", "message": str(e)}


# ═══════════════════════════════════════════════════════════════════
# API: POPULATE HEADER EXISTING DARI DN (Lengkap + Anti Duplikasi)
# ═══════════════════════════════════════════════════════════════════

@frappe.whitelist()
def populate_header_from_dn(
    header_name,
    dn_name,
    price_list=None,
    rate_field=None,
    kode_dokumen_sumber_dn=None,
    # Guard anti duplikasi
    block_duplicate_globally=True,
    allow_same_header=True,
    force=False
):
    """Tambah DN ke HEADER V21 yang sudah ada, lengkap + anti duplikasi."""
    valid, msg, dn = validate_delivery_note_full(dn_name)
    if not valid:
        return {"status": "error", "message": msg}

    if not frappe.db.exists("HEADER V21", header_name):
        return {"status": "error", "message": _("HEADER V21 {0} tidak ditemukan").format(header_name)}

    header = frappe.get_doc("HEADER V21", header_name)

    # Guard: duplikasi global (boleh re-import ke header yang sama jika allow_same_header=True)
    if block_duplicate_globally and not force:
        used, other_header = dn_used_in_other_header(dn_name, current_header=header_name if allow_same_header else None)
        if used:
            return {
                "status": "error",
                "message": _("DN {0} sudah pernah diimport ke HEADER {1}. Duplikasi diblokir.").format(dn_name, other_header)
            }

    # Guard: duplikasi di header yang sama (child DOKUMEN)
    if any(getattr(d, "nomor_dokumen", None) == dn_name for d in (header.dokumen or [])):
        if not force:
            return {"status": "error", "message": _("DN {0} sudah terdaftar di DOKUMEN header ini").format(dn_name)}
        # jika force=True → lanjut

    try:
        # Minimal sync header
        if not header.kode_valuta:
            header.kode_valuta = resolve_currency_for_dn(dn, price_list=price_list)
        if not header.nama_pernyataan:
            header.nama_pernyataan = dn.customer_name or dn.customer

        # ENTITAS jika kosong
        if not header.entitas:
            company_data = get_company_entitas_data(dn.company)
            if company_data:
                e3 = header.append("entitas"); e3.seri = 1; e3.kode_entitas = "3"
                for k, v in company_data.items():
                    if hasattr(e3, k): setattr(e3, k, v)
            customer_data = get_customer_entitas_data(dn.customer)
            if customer_data:
                e4 = header.append("entitas"); e4.seri = 2; e4.kode_entitas = "4"
                for k, v in customer_data.items():
                    if hasattr(e4, k): setattr(e4, k, v)
            if company_data:
                e7 = header.append("entitas"); e7.seri = 3; e7.kode_entitas = "7"
                for k, v in company_data.items():
                    if hasattr(e7, k): setattr(e7, k, v)

        # Dokumen DN
        add_source_to_dokumen(header, dn, "dn", kode_dokumen_sumber_dn=kode_dokumen_sumber_dn)

        # Hitung seri barang mulai dari existing
        existing = frappe.get_all("BARANG V1", filters={"nomoraju": header_name}, fields=["name"])
        start_seri = len(existing) + 1

        total_value = 0.0
        total_netto = 0.0
        warnings_all = []
        header_currency = header.kode_valuta or resolve_currency_for_dn(dn, price_list=price_list)

        idx = start_seri
        for it in dn.items:
            barang_data, warns = map_dn_item_to_barang_rich(
                it, idx, header_name, header_currency,
                default_coo="ID", price_list=price_list, rate_field=rate_field
            )
            warnings_all.extend(warns or [])
            barang = frappe.new_doc("BARANG V1")
            for k, v in barang_data.items():
                if hasattr(barang, k): setattr(barang, k, v)
            barang.insert(ignore_permissions=True)

            total_value += flt(barang.cif)
            total_netto += flt(barang.netto)
            idx += 1

        # Update totals
        header.nilai_barang = flt(header.nilai_barang or 0) + flt(total_value, 2)
        header.cif = flt(header.cif or 0) + flt(total_value, 2)
        header.netto = flt(header.netto or 0) + flt(total_netto, 4)
        header.bruto = flt(header.netto * 1.05, 4)
        header.save(ignore_permissions=True)

        # (Opsional) Lock DN ke HEADER jika ada custom field
        if frappe.db.has_column("Delivery Note", "custom_header_v21"):
            # Jangan overwrite jika field sudah terisi header lain, kecuali force=True
            linked_hdr = frappe.db.get_value("Delivery Note", dn_name, "custom_header_v21")
            if not linked_hdr or linked_hdr == header_name or force:
                frappe.db.set_value("Delivery Note", dn_name, "custom_header_v21", header_name, update_modified=False)

        frappe.db.commit()

        message = _("{0} barang ditambahkan dari Delivery Note {1}").format(len(dn.items), dn_name)
        if warnings_all:
            message += "<br><br><strong>⚠️ Peringatan:</strong><br>" + "<br>".join(warnings_all[:5])
            if len(warnings_all) > 5:
                message += f"<br>...dan {len(warnings_all) - 5} item lainnya"

        return {
            "status": "success",
            "header_name": header_name,
            "barang_added": len(dn.items),
            "total_value": total_value,
            "message": message,
            "warnings": warnings_all
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Populate HEADER from DN (Rich) Error")
        return {"status": "error", "message": str(e)}


# ═══════════════════════════════════════════════════════════════════
# PICKER: DN yang submitted
# ═══════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_verified_delivery_notes():
    """DN yang siap dipilih (docstatus=1)."""
    return frappe.get_all(
        "Delivery Note",
        filters={"docstatus": 1},
        fields=["name", "customer_name", "posting_date", "company"],
        order_by="posting_date desc",
        limit=50
    )