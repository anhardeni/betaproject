# -*- coding: utf-8 -*-
# Copyright (c) 2026, AnharDeni and contributors
# License: MIT

"""
PO/PI to HEADER V21 Integration
================================
Mengintegrasikan Purchase Order (PO) dan Purchase Invoice (PI) dari ERPNext 
dengan HEADER V21 untuk semua dokumen BC.

Functions:
- make_header_v21_from_po: Buat HEADER dari single PO
- make_header_v21_from_pi: Buat HEADER dari single PI  
- make_header_v21_multi_sources: Buat dari multiple PO/PI
- populate_header_from_po: Populate existing HEADER dari PO
- populate_header_from_pi: Populate existing HEADER dari PI
"""

import frappe
from frappe import _
from frappe.utils import today, flt, cint, getdate


# ═══════════════════════════════════════════════════════════════════
# VALIDATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def validate_source_document(doc_name, source_type):
    """
    Validasi PO/PI sebelum konversi ke HEADER V21
    
    Args:
        doc_name: Nama dokumen (PO/PI name)
        source_type: "po" atau "pi"
    
    Returns:
        (valid: bool, message: str, doc: Document/None)
    """
    doctype = "Purchase Order" if source_type == "po" else "Purchase Invoice"
    
    if not frappe.db.exists(doctype, doc_name):
        return False, _("{0} {1} tidak ditemukan").format(doctype, doc_name), None
    
    doc = frappe.get_doc(doctype, doc_name)
    
    # Check docstatus
    if doc.docstatus == 0:
        return False, _("{0} {1} belum di-submit. Harap submit terlebih dahulu.").format(doctype, doc_name), None
    
    if doc.docstatus == 2:
        return False, _("{0} {1} sudah dibatalkan.").format(doctype, doc_name), None
    
    # Check items
    if not doc.items or len(doc.items) == 0:
        return False, _("{0} {1} tidak memiliki items.").format(doctype, doc_name), None
    
    return True, "Valid", doc


# ═══════════════════════════════════════════════════════════════════
# HELPER: GENERATE NOMOR AJU
# ═══════════════════════════════════════════════════════════════════

def generate_nomor_aju(sources, source_type, kode_dokumen):
    """
    Generate unique nomor aju from sources
    Format: BC{kode}{YYMMDD}{SOURCE_CODES}
    """
    date_str = today().replace("-", "")[2:8]  # YYMMDD
    
    # Get last 4 chars of each source
    source_codes = "".join([s[-4:] for s in sources[:3]])
    
    base_aju = f"BC{kode_dokumen}{date_str}{source_codes}"
    
    # Check if exists and add suffix if needed
    counter = 1
    nomor_aju = base_aju
    while frappe.db.exists("HEADER V21", {"nomoraju": nomor_aju}):
        nomor_aju = f"{base_aju}{counter}"
        counter += 1
        if counter > 99:
            break
    
    return nomor_aju


# ═══════════════════════════════════════════════════════════════════
# HELPER: ADD SOURCE DOCUMENT TO DOKUMEN CHILD TABLE
# ═══════════════════════════════════════════════════════════════════

def add_source_to_dokumen(header, source_doc, source_type):
    """
    Add PO/PI as document entry in DOKUMEN child table
    
    Args:
        header: HEADER V21 document
        source_doc: Purchase Order or Purchase Invoice document
        source_type: "po" or "pi"
    """
    # Get next seri number
    existing_seri = len(header.dokumen) if header.dokumen else 0
    next_seri = existing_seri + 1
    
    # Document code: "999" for PO, "380" for PI (Commercial Invoice)
    kode_dokumen = "999" if source_type == "po" else "380"
    
    # Get document date
    if source_type == "po":
        tanggal = source_doc.transaction_date
    else:
        tanggal = source_doc.posting_date
    
    # Append to dokumen child table
    dokumen = header.append("dokumen")
    dokumen.seri = next_seri
    dokumen.kode_dokumen = kode_dokumen
    dokumen.nomor_dokumen = source_doc.name
    dokumen.tanggal_dokumen = tanggal


# ═══════════════════════════════════════════════════════════════════
# HELPER: GET COMPANY DATA FOR ENTITAS
# ═══════════════════════════════════════════════════════════════════


def get_company_entitas_data(company_name=None):
    """
    Get company data for ENTITAS Kode 3 (Pengusaha TPB) dan Kode 7 (Pemilik Barang)
    """
    if not company_name:
        company_name = frappe.defaults.get_user_default("Company") or frappe.get_single("Global Defaults").default_company
    
    if not company_name:
        return {}
    
    company = frappe.get_doc("Company", company_name)
    
    # Get company address
    address = ""
    if company.get("company_address"):
        addr_doc = frappe.get_doc("Address", company.company_address)
        address = ", ".join(filter(None, [
            addr_doc.address_line1,
            addr_doc.address_line2,
            addr_doc.city,
            addr_doc.state,
            addr_doc.country
        ]))
    
    return {
        "nama_entitas": company.company_name,
        "alamat_entitas": address or company.get("address") or "",
        "nomor_identitas": company.tax_id or "",  # NPWP
        "nib_entitas": company.get("custom_nib") or "",
        "niper_entitas": company.get("custom_niper") or "",
        "kode_jenis_identitas": "5",  # NPWP
        "kode_status": "1",
        "kode_negara": "ID",
    }


# ═══════════════════════════════════════════════════════════════════
# HELPER: GET SUPPLIER DATA FOR ENTITAS
# ═══════════════════════════════════════════════════════════════════

def get_supplier_entitas_data(supplier_name):
    """
    Get supplier data for ENTITAS Kode 5 (Pemasok)
    """
    if not supplier_name or not frappe.db.exists("Supplier", supplier_name):
        return {}
    
    supplier = frappe.get_doc("Supplier", supplier_name)
    
    # Get supplier address
    address = ""
    address_name = frappe.db.get_value("Dynamic Link", {
        "link_doctype": "Supplier",
        "link_name": supplier_name,
        "parenttype": "Address"
    }, "parent")
    
    if address_name:
        addr_doc = frappe.get_doc("Address", address_name)
        address = ", ".join(filter(None, [
            addr_doc.address_line1,
            addr_doc.address_line2,
            addr_doc.city,
            addr_doc.state,
            addr_doc.country
        ]))
    
    # Get country code
    country_code = ""
    if supplier.country:
        country_code = frappe.db.get_value("Country", supplier.country, "code") or ""
        country_code = country_code.upper()[:2] if country_code else ""
    
    return {
        "nama_entitas": supplier.supplier_name,
        "alamat_entitas": address,
        "kode_negara": country_code,
        "nomor_identitas": supplier.tax_id or "",
    }


# ═══════════════════════════════════════════════════════════════════
# HELPER: UOM MAPPING
# ═══════════════════════════════════════════════════════════════════

def get_ceisa_uom(uom_name):
    """
    Map ERPNext UOM to CEISA Reference UOM (Referensi Satuan Barang)
    """
    if not uom_name:
        return "KGS"
    
    # Try exact match first
    if frappe.db.exists("Referensi Satuan Barang", uom_name):
        return uom_name
    
    # Common mappings
    UOM_MAP = {
        "nos": "PCE",
        "unit": "PCE",
        "set": "SET",
        "kg": "KGM",
        "kilogram": "KGM",
        "kgs": "KGM",
        "meter": "MTR",
        "mtr": "MTR",
        "box": "BX",
        "pcs": "PCE",
        "piece": "PCE"
    }
    
    mapped = UOM_MAP.get(uom_name.lower())
    if mapped and frappe.db.exists("Referensi Satuan Barang", mapped):
        return mapped
        
    # If still not found, try to find by description or just get the first one as fallback
    # In production, we should probably throw a clearer error or have a default 'KGM'
    fallback = frappe.db.get_value("Referensi Satuan Barang", {"name": ["like", f"%{uom_name}%"]}, "name")
    if not fallback:
        # Final fallback to KGS/KGM which is most common
        fallback = "KGM" if frappe.db.exists("Referensi Satuan Barang", "KGM") else "KGS"
        
    return fallback


# ═══════════════════════════════════════════════════════════════════
# HELPER: MAP ITEM TO BARANG V1
# ═══════════════════════════════════════════════════════════════════

def map_item_to_barang(item_row, seri_barang, header_name):
    """
    Map PO/PI item row to BARANG V1 fields
    Returns tuple: (barang_data dict, warning message or None)
    """
    item_code = item_row.item_code
    
    # Get Item master data
    item_doc = frappe.get_doc("Item", item_code) if frappe.db.exists("Item", item_code) else None
    
    # Get HS Code - check custom field or standard
    hs_code = ""
    if item_doc:
        hs_code = (
            item_doc.get("customs_tariff_number") or 
            item_doc.get("custom_hs_code") or 
            item_doc.get("hs_code") or 
            ""
        )
    
    # Validate HS code exists in reference table
    validated_hs = ""
    hs_warning = None
    if hs_code:
        # Clean the HS code (remove dots, spaces)
        clean_hs = hs_code.replace(".", "").replace(" ", "").strip()
        
        # Try exact match first
        if frappe.db.exists("Referensi HS 2022 v1", clean_hs):
            validated_hs = clean_hs
        else:
            # Try first 8 digits (standard HS code length)
            partial_hs = clean_hs[:8] if len(clean_hs) >= 8 else clean_hs
            if frappe.db.exists("Referensi HS 2022 v1", partial_hs):
                validated_hs = partial_hs
            else:
                # HS code not found in reference - warn user
                hs_warning = f"{item_code}: HS '{hs_code}' tidak ditemukan di referensi"
    else:
        # No HS code defined for item
        hs_warning = f"{item_code}: Tidak ada HS code di master Item"
    
    # Get country of origin
    country_origin = ""
    if item_doc:
        country_origin = (
            item_doc.get("country_of_origin") or 
            item_doc.get("custom_country_of_origin") or 
            ""
        )
        # Convert country name to code if needed
        if country_origin and len(country_origin) > 2:
            country_code = frappe.db.get_value("Country", country_origin, "code")
            country_origin = country_code.upper()[:2] if country_code else ""
    
    # Calculate weight
    weight = flt(item_row.qty) * flt(item_doc.get("weight_per_unit") or 1 if item_doc else 1)
    
    # Get UOM
    uom = item_doc.stock_uom if item_doc else (item_row.uom or "Nos")
    ceisa_uom = get_ceisa_uom(uom)
    
    barang_data = {
        "nomoraju": header_name,
        "seri_barang": seri_barang,
        "hs": validated_hs,  # Leave empty if not found (user can fix later)
        "kode_barang": item_code,
        "uraian": item_row.item_name or (item_doc.item_name if item_doc else ""),
        "merek": item_doc.get("brand") or item_doc.get("customs_brand") or "" if item_doc else "",
        "tipe": item_doc.get("custom_type") or "" if item_doc else "",
        "spesifikasi_lain": item_row.description[:200] if item_row.description else "",
        "kode_satuan": ceisa_uom,
        "jumlah_satuan": flt(item_row.qty, 4),
        "netto": flt(weight, 4),
        "cif": flt(item_row.amount, 2),
        "harga_satuan": flt(item_row.rate, 4),
        "kode_negara_asal": country_origin or "",
        "kode_kondisi_barang": "1",  # Default: Baik
    }
    
    return barang_data, hs_warning


# ═══════════════════════════════════════════════════════════════════
# MAIN API: CREATE HEADER FROM PO
# ═══════════════════════════════════════════════════════════════════

@frappe.whitelist()
def make_header_v21_from_po(po_name, kode_dokumen="23", kode_kantor=None):
    """
    Create HEADER V21 from single Purchase Order
    
    Args:
        po_name: Purchase Order name
        kode_dokumen: BC document type (20, 23, 25, 27, 30, etc.)
        kode_kantor: Customs office code
    
    Returns:
        dict with status, header_name, message
    """
    return make_header_v21_multi_sources([po_name], "po", kode_dokumen, kode_kantor)


# ═══════════════════════════════════════════════════════════════════
# MAIN API: CREATE HEADER FROM PI
# ═══════════════════════════════════════════════════════════════════

@frappe.whitelist()
def make_header_v21_from_pi(pi_name, kode_dokumen="23", kode_kantor=None):
    """
    Create HEADER V21 from single Purchase Invoice
    """
    return make_header_v21_multi_sources([pi_name], "pi", kode_dokumen, kode_kantor)


# ═══════════════════════════════════════════════════════════════════
# MAIN API: CREATE HEADER FROM MULTIPLE SOURCES
# ═══════════════════════════════════════════════════════════════════

@frappe.whitelist()
def make_header_v21_multi_sources(sources, source_type="po", kode_dokumen="23", kode_kantor=None):
    """
    Create HEADER V21 from multiple PO/PI
    
    Args:
        sources: List of PO/PI names (can be JSON string)
        source_type: "po" or "pi"
        kode_dokumen: BC document type
        kode_kantor: Customs office code
    
    Returns:
        dict with status, header_name, barang_count, total_value
    """
    import json
    
    # Parse sources if JSON string
    if isinstance(sources, str):
        try:
            sources = json.loads(sources)
        except:
            sources = [sources]
    
    if not sources:
        return {"status": "error", "message": _("Tidak ada sumber dokumen yang dipilih")}
    
    # Validate all sources
    validated_docs = []
    for source_name in sources:
        valid, message, doc = validate_source_document(source_name, source_type)
        if not valid:
            return {"status": "error", "message": message}
        validated_docs.append(doc)
    
    try:
        # Generate nomor aju
        nomor_aju = generate_nomor_aju(sources, source_type, kode_dokumen)
        
        # Create HEADER V21
        header = frappe.new_doc("HEADER V21")
        header.kode_dokumen = kode_dokumen
        
        # Office code
        if not kode_kantor:
            # Try to get default from existing headers or fallback
            last_office = frappe.db.get_value("HEADER V21", {}, "kode_kantor", order_by="creation desc")
            header.kode_kantor = last_office or "040300"
        else:
            header.kode_kantor = kode_kantor
        
        # Get first document for common fields
        first_doc = validated_docs[0]
        
        # Map header fields
        header.kode_valuta = first_doc.currency
        header.tanggal_pernyataan = today()
        header.nama_pernyataan = first_doc.supplier_name or first_doc.supplier
        header.kota_pernyataan = "Jakarta"  # Default
        
        # Save first to get name for child tables
        header.insert(ignore_permissions=True)
        header_name = header.name
        
        # Set nomoraju after insert (autoname generates the main name)
        frappe.db.set_value("HEADER V21", header_name, "nomoraju", nomor_aju)
        
        # ═══════════════════════════════════════════════════════════
        # POPULATE ENTITAS
        # ═══════════════════════════════════════════════════════════
        
        # Kode 3: Pengusaha TPB (from Company)
        company_data = get_company_entitas_data(first_doc.company)
        if company_data:
            entitas_3 = header.append("entitas")
            entitas_3.seri = 1
            entitas_3.kode_entitas = "3"
            for key, value in company_data.items():
                if hasattr(entitas_3, key):
                    setattr(entitas_3, key, value)
        
        # Kode 5: Pemasok (from Supplier)
        supplier_data = get_supplier_entitas_data(first_doc.supplier)
        if supplier_data:
            entitas_5 = header.append("entitas")
            entitas_5.seri = 2
            entitas_5.kode_entitas = "5"
            for key, value in supplier_data.items():
                if hasattr(entitas_5, key):
                    setattr(entitas_5, key, value)
        
        # Kode 7: Pemilik Barang (same as Kode 3)
        if company_data:
            entitas_7 = header.append("entitas")
            entitas_7.seri = 3
            entitas_7.kode_entitas = "7"
            for key, value in company_data.items():
                if hasattr(entitas_7, key):
                    setattr(entitas_7, key, value)
        
        # ═══════════════════════════════════════════════════════════
        # POPULATE DOKUMEN (add source PO/PI to document list)
        # ═══════════════════════════════════════════════════════════
        
        for doc in validated_docs:
            add_source_to_dokumen(header, doc, source_type)
        
        # ═══════════════════════════════════════════════════════════
        # POPULATE BARANG V1
        # ═══════════════════════════════════════════════════════════
        
        total_items = []
        total_value = 0
        total_netto = 0
        
        for doc in validated_docs:
            for item_row in doc.items:
                total_items.append(item_row)
                total_value += flt(item_row.amount)
        
        # Create BARANG V1 records (separate DocType, not child table)
        hs_warnings = []
        for idx, item_row in enumerate(total_items, 1):
            barang_data, hs_warning = map_item_to_barang(item_row, idx, header_name)
            if hs_warning:
                hs_warnings.append(hs_warning)
            
            barang = frappe.new_doc("BARANG V1")
            for key, value in barang_data.items():
                if hasattr(barang, key):
                    setattr(barang, key, value)
            barang.insert(ignore_permissions=True)
            
            total_netto += flt(barang.netto)
        
        # ═══════════════════════════════════════════════════════════
        # UPDATE HEADER TOTALS
        # ═══════════════════════════════════════════════════════════
        
        header.reload()
        header.nilai_barang = flt(total_value, 2)
        header.cif = flt(total_value, 2)
        header.netto = flt(total_netto, 4)
        header.bruto = flt(total_netto * 1.05, 4)  # Bruto = Netto + 5%
        header.save(ignore_permissions=True)
        
        frappe.db.commit()
        
        # Build message with warnings if any
        message = _("HEADER V21 berhasil dibuat dengan {0} barang").format(len(total_items))
        if hs_warnings:
            message += "<br><br><strong>⚠️ Peringatan HS Code:</strong><br>" + "<br>".join(hs_warnings[:5])
            if len(hs_warnings) > 5:
                message += f"<br>...dan {len(hs_warnings) - 5} item lainnya"
        
        return {
            "status": "success",
            "header_name": header_name,
            "nomor_aju": nomor_aju,
            "barang_count": len(total_items),
            "total_value": total_value,
            "sources": sources,
            "message": message,
            "hs_warnings": hs_warnings
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Make HEADER V21 Error")
        return {"status": "error", "message": str(e)}


# ═══════════════════════════════════════════════════════════════════
# API: POPULATE EXISTING HEADER FROM PO
# ═══════════════════════════════════════════════════════════════════

@frappe.whitelist()
def populate_header_from_po(header_name, po_name):
    """
    Populate existing HEADER V21 with data from PO
    (for use from HEADER V21 form)
    """
    return populate_header_from_source(header_name, po_name, "po")


@frappe.whitelist()
def populate_header_from_pi(header_name, pi_name):
    """
    Populate existing HEADER V21 with data from PI
    """
    return populate_header_from_source(header_name, pi_name, "pi")


def populate_header_from_source(header_name, source_name, source_type):
    """
    Populate existing HEADER V21 with data from PO/PI
    """
    # Validate source
    valid, message, source_doc = validate_source_document(source_name, source_type)
    if not valid:
        return {"status": "error", "message": message}
    
    # Get header
    if not frappe.db.exists("HEADER V21", header_name):
        return {"status": "error", "message": _("HEADER V21 {0} tidak ditemukan").format(header_name)}
    
    header = frappe.get_doc("HEADER V21", header_name)
    
    try:
        # Update header fields
        header.kode_valuta = source_doc.currency
        header.nama_pernyataan = source_doc.supplier_name or source_doc.supplier
        
        # Add ENTITAS if empty
        if not header.entitas or len(header.entitas) == 0:
            # Kode 3: Pengusaha TPB
            company_data = get_company_entitas_data(source_doc.company)
            if company_data:
                entitas_3 = header.append("entitas")
                entitas_3.seri = 1
                entitas_3.kode_entitas = "3"
                for key, value in company_data.items():
                    if hasattr(entitas_3, key):
                        setattr(entitas_3, key, value)
            
            # Kode 5: Pemasok
            supplier_data = get_supplier_entitas_data(source_doc.supplier)
            if supplier_data:
                entitas_5 = header.append("entitas")
                entitas_5.seri = 2
                entitas_5.kode_entitas = "5"
                for key, value in supplier_data.items():
                    if hasattr(entitas_5, key):
                        setattr(entitas_5, key, value)
            
            # Kode 7: Pemilik Barang
            if company_data:
                entitas_7 = header.append("entitas")
                entitas_7.seri = 3
                entitas_7.kode_entitas = "7"
                for key, value in company_data.items():
                    if hasattr(entitas_7, key):
                        setattr(entitas_7, key, value)
        
        # ═══════════════════════════════════════════════════════════
        # POPULATE DOKUMEN (add source PO/PI to document list)
        # ═══════════════════════════════════════════════════════════
        
        add_source_to_dokumen(header, source_doc, source_type)
        
        # Get existing barang count for seri numbering
        existing_barang = frappe.get_all("BARANG V1", 
            filters={"nomoraju": header_name}, 
            fields=["name"]
        )
        start_seri = len(existing_barang) + 1
        
        # Add BARANG V1
        total_value = 0
        total_netto = 0
        barang_added = 0
        hs_warnings = []
        
        for idx, item_row in enumerate(source_doc.items, start_seri):
            barang_data, hs_warning = map_item_to_barang(item_row, idx, header_name)
            if hs_warning:
                hs_warnings.append(hs_warning)
            
            barang = frappe.new_doc("BARANG V1")
            for key, value in barang_data.items():
                if hasattr(barang, key):
                    setattr(barang, key, value)
            barang.insert(ignore_permissions=True)
            
            total_value += flt(item_row.amount)
            total_netto += flt(barang.netto)
            barang_added += 1
        
        # Update header totals
        header.nilai_barang = flt(header.nilai_barang or 0) + flt(total_value, 2)
        header.cif = flt(header.cif or 0) + flt(total_value, 2)
        header.netto = flt(header.netto or 0) + flt(total_netto, 4)
        header.bruto = flt(header.netto * 1.05, 4)
        header.save(ignore_permissions=True)
        
        frappe.db.commit()
        
        # Build message with warnings if any
        message = _("{0} barang ditambahkan dari {1}").format(barang_added, source_name)
        if hs_warnings:
            message += "<br><br><strong>⚠️ Peringatan HS Code:</strong><br>" + "<br>".join(hs_warnings[:5])
            if len(hs_warnings) > 5:
                message += f"<br>...dan {len(hs_warnings) - 5} item lainnya"
        
        return {
            "status": "success",
            "header_name": header_name,
            "barang_added": barang_added,
            "total_value": total_value,
            "message": message,
            "hs_warnings": hs_warnings
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Populate HEADER Error")
        return {"status": "error", "message": str(e)}


# ═══════════════════════════════════════════════════════════════════
# API: GET AVAILABLE PO/PI FOR PICKER
# ═══════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_available_purchase_orders():
    """Get list of submitted POs for picker dialog"""
    return frappe.get_all("Purchase Order",
        filters={"docstatus": 1},
        fields=["name", "supplier_name", "grand_total", "currency", "transaction_date"],
        order_by="transaction_date desc",
        limit=50
    )


@frappe.whitelist()
def get_available_purchase_invoices():
    """Get list of submitted PIs for picker dialog"""
    return frappe.get_all("Purchase Invoice",
        filters={"docstatus": 1},
        fields=["name", "supplier_name", "grand_total", "currency", "posting_date"],
        order_by="posting_date desc",
        limit=50
    )


@frappe.whitelist()
def get_kantor_list():
    """Get list of customs offices for dialog"""
    return frappe.get_all("Referensi Kantor", fields=["name", "uraian_kantor"], order_by="name asc")
