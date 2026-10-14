import json
import os

# Frappe di-import secara lazy (di dalam fungsi) agar modul ini
# aman di-import SEBELUM Frappe framework selesai inisialisasi (cth: saat bench execute).
# Bare "import frappe" di top-level menyebabkan NameError jika hooks.py
# gagal load karena circular import atau Frappe belum ready.

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "field_mapping.json")

def load_field_mapping():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def get_existing_table_columns(doctype):
    """
    Mengambil daftar nama kolom fisik yang benar-benar ada pada tabel DocType di MariaDB/MySQL.
    """
    try:
        import frappe  # lazy import - aman di luar context Frappe
        table_name = f"tab{doctype}"
        if hasattr(frappe, "db") and frappe.db and hasattr(frappe.db, "get_table_columns"):
            return frappe.db.get_table_columns(doctype) or frappe.db.get_table_columns(table_name) or []
    except Exception:
        pass
    return []

def get_actual_field_name(doctype, field_type_key):
    """
    Mencari nama kolom fisik pertama yang cocok antara konfigurasi field_mapping.json
    dengan kolom yang benar-benar ada di tabel database.
    
    :param doctype: 'Purchase Receipt', 'Delivery Note', 'Stock Entry', dll.
    :param field_type_key: 'jenis_dok', 'no_daftar', atau 'tgl_daftar'
    :return: str nama kolom aktual (misal: 'custom_no_ppkek') atau fallback String kosong.
    """
    mapping = load_field_mapping().get(doctype, {})
    candidate_fields = mapping.get(field_type_key, [])
    
    existing_cols = get_existing_table_columns(doctype)
    
    if existing_cols:
        for field in candidate_fields:
            if field in existing_cols:
                return field
                
    # Fallback jika meta tidak dapat diakses secara langsung saat render awal
    return candidate_fields[0] if candidate_fields else ""

def get_sql_select_fields(doctype, alias_prefix="pr"):
    """
    Menyusun klausa SELECT SQL untuk 3 field PPKEK/BC secara presisi dan aman dari Unknown Column Error.
    """
    jenis_field = get_actual_field_name(doctype, "jenis_dok")
    no_field = get_actual_field_name(doctype, "no_daftar")
    tgl_field = get_actual_field_name(doctype, "tgl_daftar")
    
    jenis_sql = f"{alias_prefix}.`{jenis_field}`" if jenis_field else "''"
    no_sql = f"{alias_prefix}.`{no_field}`" if no_field else "''"
    tgl_sql = f"{alias_prefix}.`{tgl_field}`" if tgl_field else "NULL"
    
    return {
        "jenis_dok": jenis_sql,
        "no_daftar": no_sql,
        "tgl_daftar": tgl_sql,
        "raw_fields": {
            "jenis_dok": jenis_field,
            "no_daftar": no_field,
            "tgl_daftar": tgl_field
        }
    }
