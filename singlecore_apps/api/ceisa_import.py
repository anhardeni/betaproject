import frappe
import openpyxl
import base64
import io
from frappe.utils import getdate, flt, cint
from datetime import datetime, date

@frappe.whitelist(allow_guest=True)
def import_ceisa_excel(file_data, dry_run=False):
    audit_report = {
        "unmapped_columns": {},
        "missing_columns": {},
        "empty_fields": {},  # Track which fields had empty values
        "stats": {}
    }

    def save_doc(d):
        d.flags.ignore_links = True
        d.flags.ignore_permissions = True
        d.save(ignore_permissions=True)

    try:
        # Decode file
        if file_data.startswith("/private/files/") or file_data.startswith("/files/"):
            if file_data.startswith("/private/"):
                file_path = frappe.get_site_path(file_data.strip("/"))
            else:
                # /files/ points to public/files/
                file_path = frappe.get_site_path("public", file_data.strip("/"))
            with open(file_path, "rb") as f:
                decoded_file = f.read()
        else:
            if "," in file_data:
                file_data = file_data.split(",")[1]
            decoded_file = base64.b64decode(file_data)

        wb = openpyxl.load_workbook(io.BytesIO(decoded_file), data_only=True)
        
        # Helper: Get Sheet Data
        def get_sheet_data(sheet_name, optional=False, expected_columns=None):
            if sheet_name not in wb.sheetnames:
                if not optional:
                    frappe.throw(f"Sheet {sheet_name} not found")
                return []
            
            ws = wb[sheet_name]
            rows = list(ws.values)
            if not rows: return []
            
            # Helper to normalize header
            def normalize(h):
                if not h: return ""
                return " ".join(str(h).strip().upper().split())

            headers = [normalize(c) for c in rows[0]]
            
            # Audit
            if expected_columns:
                present = set(headers)
                # Filter out empty headers
                present = {x for x in present if x}

                if isinstance(expected_columns, dict):
                    # Smart Audit with Aliases
                    mapping = expected_columns
                    expected_keys = set(mapping.keys())
                    
                    unmapped = [h for h in present if h not in expected_keys]
                    
                    # Missing by Target Field
                    found_targets = {mapping[h] for h in present if h in mapping}
                    all_targets = set(mapping.values())
                    missing_targets = all_targets - found_targets
                    
                    # Reverse map for display
                    reverse_map = {}
                    for k, v in mapping.items():
                        reverse_map.setdefault(v, []).append(k)
                    
                    missing = [reverse_map[mt][0] for mt in missing_targets]

                else:
                    # Legacy List Audit
                    expected = set(expected_columns)
                    unmapped = [ue for ue in present if ue not in expected]
                    missing = [mex for mex in expected if mex not in present]
                
                if unmapped:
                    audit_report["unmapped_columns"][sheet_name] = list(unmapped)
                if missing:
                    audit_report["missing_columns"][sheet_name] = missing

            data_list = []
            for row in rows[1:]:
                row_dict = {}
                has_data = False
                for idx, val in enumerate(row):
                    if idx < len(headers):
                        row_dict[headers[idx]] = val
                        if val: has_data = True
                if has_data:
                    data_list.append(row_dict)
            return data_list

        DATE_FIELDS = [
            "tanggal_bc11", "tanggal_berangkat", "tanggal_ekspor", "tanggal_masuk",
            "tanggal_muat", "tanggal_tiba", "tanggal_periksa", "tanggal_stuffing",
            "tanggal_pernyataan", "tanggal_bukti_bayar", "tanggal_daftar",
            "tanggal_ijin_entitas", "tanggal_dokumen", "tanggal_jaminan", 
            "tanggal_jatuh_tempo", "tanggal_bpj", "tanggal_daftar_asal",
            "jatuh_tempo_royalti", "tanggal_respon"
        ]

        def parse_excel_date(val):
            if not val: return None
            if isinstance(val, (datetime, date)): return val
            
            val_str = str(val).strip()
            formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y", 
                      "%d/%m/%Y", "%m/%d/%Y"]
            for fmt in formats:
                try:
                    return datetime.strptime(val_str, fmt).date()
                except ValueError:
                    continue
            return None

        # 1. HEADER MAPPING
        HEADER_MAPPING = {
            "NOMOR AJU": "nomoraju",
            "KODE DOKUMEN": "kode_dokumen",
            "KODE KANTOR": "kode_kantor",
            "KOTA PERNYATAAN": "kota_pernyataan",
            "TANGGAL PERNYATAAN": "tanggal_pernyataan",
            "NAMA PERNYATAAN": "nama_pernyataan",
            "JABATAN PERNYATAAN": "jabatan_pernyataan",
            "KODE KANTOR BONGKAR": "kode_kantor_bongkar",
            "KODE KANTOR PERIKSA": "kode_kantor_periksa",
            "KODE KANTOR TUJUAN": "kode_kantor_tujuan",
            "KODE KANTOR EKSPOR": "kode_kantor_ekspor",
            #"KODE JENIS PIB": "kode_jenis_pib", # Sometimes not in Excel?
            "KODE JENIS EKSPOR": "kode_jenis_ekspor",
            "KODE JENIS TPB": "kode_jenis_tpb",
            "KODE JENIS PLB": "kode_jenis_plb",
            "KODE JENIS IMPOR": "kode_jenis_impor",
            "KODE TUJUAN PEMASUKAN": "kode_tujuan_pemasukan",
            "KODE TUJUAN PENGIRIMAN": "kode_tujuan_pengiriman",
            "KODE TUJUAN TPB": "kode_tujuan_tpb",
            "KODE CARA DAGANG": "kode_cara_dagang",
            "KODE CARA BAYAR": "kode_cara_bayar",
            "KODE CARA BAYAR LAINNYA": "kode_cara_bayar_lainnya",
            "KODE GUDANG ASAL": "kode_gudang_asal",
            "KODE GUDANG TUJUAN": "kode_gudang_tujuan",
            "KODE JENIS KIRIM": "kode_jenis_kirim",
            "KODE JENIS PENGIRIMAN": "kode_jenis_pengiriman",
            "KODE KATEGORI EKSPOR": "kode_kategori_ekspor",
            "KODE KATEGORI MASUK FTZ": "kode_kategori_masuk_ftz",
            "KODE KATEGORI KELUAR FTZ": "kode_kategori_keluar_ftz",
            "KODE KATEGORI BARANG FTZ": "kode_kategori_barang_ftz",
            "KODE LOKASI": "kode_lokasi",
            "KODE LOKASI BAYAR": "kode_lokasi_bayar",
            "LOKASI ASAL": "lokasi_asal",
            "LOKASI TUJUAN": "lokasi_tujuan",
            "KODE DAERAH ASAL": "kode_daerah_asal",
            "KODE NEGARA TUJUAN": "kode_negara_tujuan",
            "KODE TUTUP PU": "kode_tutup_pu",
            "NOMOR BC11": "nomor_bc11",
            "NOMOR BC 11": "nomor_bc11",  # Alias with space
            "NO BC11": "nomor_bc11",  # Alias short form
            "TANGGAL BC11": "tanggal_bc11",
            "TANGGAL BC 11": "tanggal_bc11",  # Alias with space
            "TGL BC11": "tanggal_bc11",  # Alias short form
            "NOMOR POS": "nomor_pos",
            "NO POS": "nomor_pos",  # Alias short form
            "NOMOR SUB POS": "nomor_sub_pos",
            "NO SUB POS": "nomor_sub_pos",  # Alias short form
            "NOMOR SUBPOS": "nomor_sub_pos",  # Alias no space
            "KODE PELABUHAN BONGKAR": "kode_pelabuhan_bongkar",
            "KODE PELABUHAN MUAT": "kode_pelabuhan_muat",
            "KODE PELABUHAN MUAT AKHIR": "kode_pelabuhan_muat_akhir",
            "KODE PELABUHAN TRANSIT": "kode_pelabuhan_transit",
            "KODE PELABUHAN TUJUAN": "kode_pelabuhan_tujuan",
            "KODE PELABUHAN EKSPOR": "kode_pelabuhan_ekspor",
            "KODE TPS": "kode_tps",
            "TANGGAL BERANGKAT": "tanggal_berangkat",
            "TANGGAL EKSPOR": "tanggal_ekspor",
            "TANGGAL MASUK": "tanggal_masuk",
            "TANGGAL MUAT": "tanggal_muat",
            "TANGGAL TIBA": "tanggal_tiba",
            "TANGGAL PERIKSA": "tanggal_periksa",
            "TEMPAT STUFFING": "tempat_stuffing",
            "TANGGAL STUFFING": "tanggal_stuffing",
            "KODE TANDA PENGAMAN": "kode_tanda_pengaman",
            "JUMLAH TANDA PENGAMAN": "jumlah_tanda_pengaman",
            "FLAG CURAH": "flag_curah",
            "FLAG SDA": "flag_sda",
            "FLAG VD": "flag_vd",
            "FLAG MIGAS": "flag_migas",
            "KODE ASURANSI": "kode_asuransi",
            "ASURANSI": "asuransi",
            "NILAI BARANG": "nilai_barang",
            "NILAI INCOTERM": "nilai_incoterm",
            "NILAI MAKLON": "nilai_maklon",
            "FREIGHT": "freight",
            "FOB": "fob",
            "BIAYA TAMBAHAN": "biaya_tambahan",
            "BIAYA PENGURANG": "biaya_pengurang",
            "VD": "vd",
            "CIF": "cif",
            "HARGA_PENYERAHAN": "harga_penyerahan",
            "NDPBM": "ndpbm",
            "TOTAL DANA SAWIT": "total_dana_sawit",
            "DASAR PENGENAAN PAJAK": "dasar_pengenaan_pajak",
            "NILAI JASA": "nilai_jasa",
            "UANG MUKA": "uang_muka",
            "BRUTO": "bruto",
            "NETTO": "netto",
            "VOLUME": "volume",
            "KODE VALUTA": "kode_valuta",
            "KODE INCOTERM": "kode_incoterm",
            "KODE JASA KENA PAJAK": "kode_jasa_kena_pajak",
            "NOMOR BUKTI BAYAR": "nomor_bukti_bayar",
            "TANGGAL BUKTI BAYAR": "tanggal_bukti_bayar",
            "KODE JENIS NILAI": "kode_jenis_nilai",
            "KODE KANTOR MUAT": "kode_kantor_muat",
            "NOMOR DAFTAR": "nomor_daftar",
            "TANGGAL DAFTAR": "tanggal_daftar",
            "KODE ASAL BARANG FTZ": "kode_barang_asal_ftz",
            "KODE TUJUAN PENGELUARAN": "kode_tujuan_pengeluaran",
            "PPN PAJAK": "ppn_pajak",
            "PPNBM PAJAK": "ppnbm_pajak",
            "TARIF PPN PAJAK": "tarif_ppn_pajak",
            "TARIF PPNBM PAJAK": "tarif_ppnbm_pajak",
            "BARANG TIDAK BERWUJUD": "barang_tidak_berwujud",
            # Additional Mappings
            "FLAG KONSOL": "flag_konsol",
            "FLAG PROPORSIONAL NETTO": "flag_proporsional_netto",
            "FLAG AP BK": "flag_ap_bk", # If exists
            "KODE JENIS PENGELUARAN": "kode_jenis_pengeluaran",
            "KODE JENIS PROSEDUR": "kode_jenis_prosedur",
            "KODE JENIS PENGANGKUTAN": "kode_jenis_pengangkutan",
            "BARANG KIRIMAN": "barang_kiriman"
        }

        # Fetch HEADER data
        header_rows = get_sheet_data("HEADER", expected_columns=HEADER_MAPPING)
        if not header_rows:
            frappe.throw("No data in HEADER sheet")
        
        header_row = header_rows[0]
        nomor_aju = header_row.get("NOMOR AJU")
        if not nomor_aju:
            frappe.throw("NOMOR AJU is missing in HEADER")
        # Normalize nomor_aju to string for consistent comparison
        nomor_aju = str(nomor_aju).strip()

        # Get/Create Header Doc
        if frappe.db.exists("HEADER V21", {"nomoraju": nomor_aju}):
            doc = frappe.get_doc("HEADER V21", {"nomoraju": nomor_aju})
        else:
            doc = frappe.new_doc("HEADER V21")
            doc.nomoraju = nomor_aju

        # Map Header
        for excel_col, doc_field in HEADER_MAPPING.items():
            val = header_row.get(excel_col)
            if val is not None and val != "":
                if doc_field in DATE_FIELDS:
                    doc.set(doc_field, parse_excel_date(val))
                else:
                    doc.set(doc_field, val)

        # Helper for Child Tables
        def create_child(doctype, parent_field, sheet_name, mapping, optional=False):
            rows = get_sheet_data(sheet_name, optional, expected_columns=mapping)
            if not rows and optional: return
            
            child_list = []
            for row in rows:
                row_nomor_aju = str(row.get("NOMOR AJU") or "").strip()
                if row_nomor_aju != nomor_aju: continue
                child_item = {}
                for excel_col, doc_field in mapping.items():
                    val = row.get(excel_col)
                    if val is not None and val != "":
                         if doc_field in DATE_FIELDS:
                             child_item[doc_field] = parse_excel_date(val)
                         else:
                             child_item[doc_field] = val
                child_list.append(child_item)
            
            doc.set(parent_field, child_list)
            audit_report["stats"][doctype] = len(child_list)

        # CHILD TABLES IMPORT
        
        # ENTITAS
        create_child("entitas", "entitas", "ENTITAS", {
            "NOMOR AJU": "nomoraju",
            "SERI": "seri",
            "KODE ENTITAS": "kode_entitas",
            #"KODE JENIS ENTITAS": "kode_jenis_entitas",
            "NOMOR IDENTITAS": "nomor_identitas",
            "NAMA ENTITAS": "nama_entitas",
            "ALAMAT ENTITAS": "alamat_entitas",
            "NIB ENTITAS": "nib_entitas",
            "KODE JENIS API": "kode_jenis_api",
            "KODE STATUS": "kode_status",
            "KODE NEGARA": "kode_negara",
            "NOMOR IJIN ENTITAS": "nomor_ijin_entitas",
            "TANGGAL IJIN ENTITAS": "tanggal_ijin_entitas",
            "KODE JENIS IDENTITAS": "kode_jenis_identitas",
            "NIPER ENTITAS": "niper_entitas",
            "KODE AFILIASI": "kode_afiliasi",
            "KODE KATEGORI KONSOLIDATOR": "kode_kategori_konsolidator"
        })

        # KEMASAN
        create_child("kemasan", "kemasan", "KEMASAN", {
            "NOMOR AJU": "nomoraju",
            "SERI": "seri",
            "KODE KEMASAN": "kode_kemasan",
            "JUMLAH KEMASAN": "jumlah_kemasan",
            "MERK KEMASAN": "merek_kemasan",
            "MEREK": "merek_kemasan" # Alias
        })

        # DOKUMEN
        create_child("dokumen", "dokumen", "DOKUMEN", {
            "NOMOR AJU": "nomoraju",
            "SERI DOKUMEN": "seri",
            "SERI": "seri", # Alias
            "KODE DOKUMEN": "kode_dokumen",
            "NOMOR DOKUMEN": "nomor_dokumen",
            "TANGGAL DOKUMEN": "tanggal_dokumen",
            "KODE FASILITAS": "kode_fasilitas",
            "KODE IJIN": "kode_ijin"
        })

        # PENGANGKUT
        create_child("pengangkut", "pengangkut", "PENGANGKUT", {
            "NOMOR AJU": "nomoraju",
            "SERI PENGANGKUT": "seri_pengangkut",
            "SERI": "seri_pengangkut", # Alias
            "KODE CARA ANGKUT": "kode_cara_angkut",
            "NAMA PENGANGKUT": "nama_pengangkut",
            "NOMOR PENGANGKUT": "nomor_pengangkut",
            "KODE BENDERA": "kode_bendera",
            "CALL SIGN": "call_sign",
            "FLAG ANGKUT PLB": "flag_angkut_plb",
            "CARA PENGANGKUTAN LAINNYA": "cara_pengangkutan_lainnya"
        })
        
        # KONTAINER
        create_child("kontainer", "kontainer", "KONTAINER", {
            "NOMOR AJU": "nomoraju",
            "SERI KONTAINER": "seri",
            "SERI": "seri", # Alias
            "NOMOR KONTAINER": "nomor_kontainer",
            "NOMOR KONTINER": "nomor_kontainer", # Typo handling
            "KODE UKURAN KONTAINER": "kode_ukuran_kontainer",
            "KODE JENIS KONTAINER": "kode_jenis_kontainer",
            "KODE TIPE KONTAINER": "kode_tipe_kontainer"
        })

        # KOMPONEN BIAYA (Optional)
        create_child("komponen_biaya", "komponen_biaya", "KOMPONENBIAYA", {
            "NOMOR AJU": "nomoraju",
            "JENIS NILAI": "jenisnilai",
            "HARGA INVOICE": "hargainvoice",
            "PEMBAYARAN TIDAK LANGSUNG": "pembayarantidaklangsung",
            "DISKON": "diskon",
            "KOMISI PENJUALAN": "komisipenjualan",
            "BIAYA PENGEMASAN": "biayapengemasan",
            "BIAYA PENGEPAKAN": "biayapengepakan",
            "ASSIST": "assist",
            "ROYALTI": "royalti",
            "PROCEEDS": "proceeds",
            "BIAYA TRANSPORTASI": "biayatransportasi",
            "BIAYA PEMUATAN": "biayapemuatan",
            "ASURANSI": "asuransi",
            "GARANSI": "garansi",
            "BIAYA KEPENTINGAN SENDIRI": "biayakepentingansendiri",
            "BIAYA PASCA IMPOR": "biayapascaimpor",
            "BIAYA PAJAK INTERNAL": "biayapajakinternal",
            "BUNGA": "bunga",
            "DEVIDEN": "deviden"
        }, optional=True)

        # PUNGUTAN & JAMINAN & BANK DEVISA (Using new logic if needed, referencing previous conv)
        create_child("pungutan", "pungutan", "PUNGUTAN", {
            "NOMOR AJU": "nomoraju",
            "KODE FASILITAS TARIF": "kode_fasilitas_tarif",
            "KODE JENIS PUNGUTAN": "kode_jenis_pungutan",
            "NILAI PUNGUTAN": "nilai_pungutan",
            "NPWP BILLING": "npwp_billing"
        })

        create_child("jaminan", "jaminan", "JAMINAN", {
            "NOMOR AJU": "nomoraju",
            "KODE JAMINAN": "kode_jaminan",
            "NOMOR BPJ": "nomor_bpj",
            "TANGGAL BPJ": "tanggal_bpj",
            "NILAI JAMINAN": "nilai_jaminan",
            "TANGGAL JATUH TEMPO": "tanggal_jatuh_tempo",
            "PENJAMIN": "penjamin",
            "NOMOR JAMINAN": "nomor_jaminan",
            "TANGGAL JAMINAN": "tanggal_jaminan",
            "KODE KANTOR": "kode_kantor" 
        })

        create_child("bank_devisa", "bank_devisa", "BANKDEVISA", {
            "NOMOR AJU": "nomoraju",
            "KODE": "kode",
            "NAMA": "nama",
            "SERI": "seri"
        })

        # RESPON Sheet (JSON Dump)
        respon_rows = get_sheet_data("RESPON", optional=True)
        if respon_rows:
            import json
            doc.respon_json = json.dumps(respon_rows, default=str)

        # Save Header 
        save_doc(doc)

        # --- BARANG PROCESSING ---
        barang_rows = get_sheet_data("BARANG")
        
        BARANG_MAPPING = {
            "NOMOR AJU": "nomoraju",
            "SERI BARANG": "seri_barang",
            "HS": "hs",
            "KODE BARANG": "kode_barang",
            "URAIAN": "uraian",
            "MEREK": "merek",
            "MERK": "merek", # Alias
            "TIPE": "tipe",
            "UKURAN": "ukuran",
            "SPESIFIKASI LAIN": "spesifikasi_lain",
            "KODE SATUAN": "kode_satuan",
            "JUMLAH SATUAN": "jumlah_satuan",
            "KODE KEMASAN": "kode_kemasan",
            "JUMLAH KEMASAN": "jumlah_kemasan",
            "NETTO": "netto",
            "BRUTO": "bruto",
            "VOLUME": "volume",
            "CIF": "cif",
            "CIF RUPIAH": "cif_rupiah",
            "NDPBM": "ndpbm",
            "FOB": "fob",
            "ASURANSI": "asuransi",
            "FREIGHT": "freight",
            "NILAI BARANG": "nilai_barang",
            "NILAI JASA": "nilai_jasa",
            "NILAI DANA SAWIT": "nilai_dana_sawit",
            "NILAI DEVISA": "nilai_devisa",
            "PERSENTASE IMPOR": "persentase_impor",
            "DISKON": "diskon",
            "HARGA PENYERAHAN": "harga_penyerahan",
            "HARGA PEROLEHAN": "harga_perolehan",
            "HARGA SATUAN": "harga_satuan",
            "HARGA EKSPOR": "harga_ekspor",
            "HARGA PATOKAN": "harga_patokan",
            "NILAI TAMBAH": "nilai_tambah",
            "PERNYATAAN LARTAS": "pernyataan_lartas",
            "TAHUN PEMBUATAN": "tahun_pembuatan",
            "KODE JENIS EKSPOR": "kode_jenis_ekspor",
            "SERI IZIN": "seri_izin",
            "KODE ASAL BARANG": "kode_asal_barang",
            "STATEMENT PERBEDAAN HARGA": "statement_perbedaan_harga",
            "SALDO AWAL": "saldo_awal",
            "KAPASITAS SILINDER": "kapasitas_silinder",
            "JATUH TEMPO ROYALTI": "jatuh_tempo_royalti",
            "FLAG TIS": "flag_tis",
            "KODE KANTOR ASAL": "kode_kantor_asal",
            "ISI PER KEMASAN": "isi_per_kemasan",
            "FLAG 4 TAHUN": "flag_4_tahun",
            "KODE DOKUMEN ASAL": "kode_dokumen_asal",
            "KODE BKC": "kode_bkc",
            "KODE SUB KOMODITI BKC": "kode_sub_komoditi_bkc",
            "NOMOR AJU ASAL": "nomor_aju_asal",
            "KODE GUNA BARANG": "kode_guna_barang",
            "SERI BARANG ASAL": "seri_barang_asal",
            "SALDO AKHIR": "saldo_akhir",
            "KODE PERHITUNGAN": "kode_perhitungan",
            "KODE JENIS NILAI": "kode_jenis_nilai",
            "KODE KOMODITI BKC": "kode_komoditi_bkc",
            "NOMOR DAFTAR ASAL": "nomor_daftar_asal",
            "JUMLAH REALISASI": "jumlah_realisasi",
            "TANGGAL DAFTAR ASAL": "tanggal_daftar_asal",
            "METODE PENENTUAN NILAI": "metode_penentuan_nilai",
            "HJE CUKAI": "hje_cukai",
            "TARIF CUKAI": "tarif_cukai",
            "JUMLAH PITA CUKAI": "jumlah_pita_cukai",
            "JUMLAH DILEKATKAN": "jumlah_dilekatkan"
        }

        # Sheets for Barang Children
        bt_rows = get_sheet_data("BARANGTARIF")
        bd_rows = get_sheet_data("BARANGDOKUMEN")
        be_rows = get_sheet_data("BARANGENTITAS") # Maps to barang_pemilik
        bvd_rows = get_sheet_data("BARANGVD")
        bspe_rows = get_sheet_data("BARANGSPEKKHUSUS")
        
        # BAHAN BAKU Sheets
        bb_rows = get_sheet_data("BAHANBAKU")
        bbt_rows = get_sheet_data("BAHANBAKUTARIF")
        bbd_rows = get_sheet_data("BAHANBAKUDOKUMEN")

        audit_report["stats"]["BARANG V1"] = 0
        
        for b_row in barang_rows:
            seri_barang = cint(b_row.get("SERI BARANG"))
            if not seri_barang: continue  # Skip rows with no seri_barang
            
            # Check exist - use doc.name (HEADER V21 document name) for the Link field
            existing_b = frappe.get_all("BARANG V1", filters={
                "nomoraju": doc.name, "seri_barang": seri_barang
            })
            
            if existing_b:
                b_doc = frappe.get_doc("BARANG V1", existing_b[0].name)
            else:
                b_doc = frappe.new_doc("BARANG V1")
                b_doc.nomoraju = doc.name  # Link to HEADER V21 by document name
            
            # Map Barang
            for excel_col, doc_field in BARANG_MAPPING.items():
                val = b_row.get(excel_col)
                if val is not None and val != "":
                     if doc_field in DATE_FIELDS:
                         b_doc.set(doc_field, parse_excel_date(val))
                     elif isinstance(val, (int, float)):
                        b_doc.set(doc_field, flt(val))
                     else:
                        b_doc.set(doc_field, val)
            
            # Child Tables for BARANG
            
            # Tarif
            child_bt = []
            for r in bt_rows:
                if cint(r.get("SERI BARANG")) == seri_barang:
                    child_bt.append({
                        "seri_barang": seri_barang,
                        "kode_pungutan": r.get("KODE PUNGUTAN"),
                        "kode_tarif": r.get("KODE TARIF"),
                        "tarif": flt(r.get("TARIF")),
                        "kode_fasilitas": r.get("KODE FASILITAS"),
                        "tarif_fasilitas": flt(r.get("TARIF FASILITAS")),
                        "nilai_bayar": flt(r.get("NILAI BAYAR")),
                        "nilai_fasilitas": flt(r.get("NILAI FASILITAS")),
                        "nilai_sudah_dilunasi": flt(r.get("NILAI SUDAH DILUNASI")),
                        "kode_komoditi_cukai": r.get("KODE KOMODITI CUKAI"),
                        "kode_sub_komoditi_cukai": r.get("KODE SUB KOMODITI CUKAI"),
                        "jumlah_satuan": flt(r.get("JUMLAH SATUAN")),
                        "kode_satuan": r.get("KODE SATUAN")
                    })
            b_doc.set("barang_tarif", child_bt)
            
            # Dokumen
            child_bd = []
            for r in bd_rows:
                 if cint(r.get("SERI BARANG")) == seri_barang:
                    child_bd.append({
                        "seri_dokumen": r.get("SERI DOKUMEN"),
                        "seri_izin": r.get("SERI IZIN")
                    })
            b_doc.set("barang_dokumen", child_bd)
            
            # Pemilik (Entitas)
            child_be = []
            for r in be_rows:
                 if cint(r.get("SERI BARANG")) == seri_barang:
                    child_be.append({
                        "seri_entitas": r.get("SERI ENTITAS")
                    })
            b_doc.set("barang_pemilik", child_be)
            
            # Spek Khusus
            child_sp = []
            for r in bspe_rows:
                 if cint(r.get("SERI BARANG")) == seri_barang:
                    child_sp.append({
                        "kode": r.get("KODE"),
                        "uraian": r.get("URAIAN")
                    })
            b_doc.set("barang_spek_khusus", child_sp)

            # VD
            child_vd = []
            for r in bvd_rows:
                 if cint(r.get("SERI BARANG")) == seri_barang:
                    child_vd.append({
                        "kode_jenis_vd": r.get("KODE VD"),
                        "nilai_barang": flt(r.get("NILAI BARANG")),
                        "biaya_tambahan": flt(r.get("BIAYA TAMBAHAN")),
                        "biaya_pengurang": flt(r.get("BIAYA PENGURANG")),
                        "jatuh_tempo": parse_excel_date(r.get("JATUH TEMPO"))
                    })
            b_doc.set("barang_vd", child_vd)

            save_doc(b_doc)
            audit_report["stats"]["BARANG V1"] += 1
            
            # Track child table stats
            audit_report["stats"]["BARANG TARIF"] = audit_report["stats"].get("BARANG TARIF", 0) + len(child_bt)
            audit_report["stats"]["BARANG DOKUMEN"] = audit_report["stats"].get("BARANG DOKUMEN", 0) + len(child_bd)
            audit_report["stats"]["BARANG PEMILIK"] = audit_report["stats"].get("BARANG PEMILIK", 0) + len(child_be)
            audit_report["stats"]["BARANG SPEK KHUSUS"] = audit_report["stats"].get("BARANG SPEK KHUSUS", 0) + len(child_sp)
            audit_report["stats"]["BARANG VD"] = audit_report["stats"].get("BARANG VD", 0) + len(child_vd)
            
            # --- BAHAN BAKU --- (Linked to BARANG)
            for bb_row in bb_rows:
                if cint(bb_row.get("SERI BARANG")) == seri_barang:
                    seri_bahan_baku = cint(bb_row.get("SERI BAHAN BAKU"))
                    
                    filters = {
                        "nomoraju": nomor_aju, 
                        "seri_barang": seri_barang,
                        "seri_bahan_baku": seri_bahan_baku
                    }
                    existing_bb = frappe.get_all("BAHAN BAKU", filters=filters)
                    
                    if existing_bb:
                        bb_doc = frappe.get_doc("BAHAN BAKU", existing_bb[0].name)
                    else:
                        bb_doc = frappe.new_doc("BAHAN BAKU")
                        bb_doc.update(filters)
                        bb_doc.parent_barang = b_doc.name
                    
                    # Map Bahan Baku
                    # Reusing BARANG_MAPPING keys where possible or direct map
                    # Since we have many fields, let's map directly from row using generic logic?
                    # Or explicit for safety.
                    
                    bb_doc.hs = bb_row.get("HS")
                    bb_doc.kode_barang = bb_row.get("KODE BARANG")
                    bb_doc.uraian = bb_row.get("URAIAN")
                    bb_doc.merek = bb_row.get("MEREK")
                    bb_doc.tipe = bb_row.get("TIPE")
                    bb_doc.ukuran = bb_row.get("UKURAN")
                    bb_doc.spesifikasi_lain = bb_row.get("SPESIFIKASI LAIN")
                    bb_doc.kode_satuan = bb_row.get("KODE SATUAN")
                    bb_doc.jumlah_satuan = flt(bb_row.get("JUMLAH SATUAN"))
                    bb_doc.kode_asal_bahan_baku = bb_row.get("KODE ASAL BAHAN BAKU")
                    bb_doc.cif = flt(bb_row.get("CIF"))
                    bb_doc.cif_rupiah = flt(bb_row.get("CIF RUPIAH"))
                    bb_doc.harga_penyerahan = flt(bb_row.get("HARGA PENYERAHAN"))
                    bb_doc.harga_perolehan = flt(bb_row.get("HARGA PEROLEHAN"))
                    bb_doc.ndpbm = flt(bb_row.get("NDPBM"))
                    bb_doc.netto = flt(bb_row.get("NETTO"))
                    bb_doc.bruto = flt(bb_row.get("BRUTO"))
                    bb_doc.volume = flt(bb_row.get("VOLUME"))
                    
                    # New fields
                    bb_doc.kode_bkc = bb_row.get("KODE BKC")
                    bb_doc.kode_komoditi_bkc = bb_row.get("KODE KOMODITI BKC")
                    bb_doc.kode_sub_komoditi_bkc = bb_row.get("KODE SUB KOMODITI BKC")
                    bb_doc.flag_tis = bb_row.get("FLAG TIS")
                    bb_doc.isi_per_kemasan = bb_row.get("ISI PER KEMASAN")
                    bb_doc.jumlah_dilekatkan = bb_row.get("JUMLAH DILEKATKAN")
                    bb_doc.jumlah_pita_cukai = bb_row.get("JUMLAH PITA CUKAI")
                    bb_doc.hje_cukai = flt(bb_row.get("HJE CUKAI"))
                    bb_doc.tarif_cukai = flt(bb_row.get("TARIF CUKAI"))
                    bb_doc.nomor_aju_asal = bb_row.get("NOMOR AJU ASAL")
                    bb_doc.nomor_daftar_asal = bb_row.get("NOMOR DAFTAR ASAL")
                    bb_doc.tanggal_daftar_asal = parse_excel_date(bb_row.get("TANGGAL DAFTAR ASAL"))
                    bb_doc.kode_dokumen_asal = bb_row.get("KODE DOKUMEN ASAL")
                    bb_doc.kode_kantor_asal = bb_row.get("KODE KANTOR ASAL")
                    
                    # Children of Bahan Baku
                    # BB Tarif
                    child_bbt = []
                    for r in bbt_rows:
                        if (cint(r.get("SERI BARANG")) == seri_barang and 
                            cint(r.get("SERI BAHAN BAKU")) == seri_bahan_baku):
                            child_bbt.append({
                                "kode_pungutan": r.get("KODE PUNGUTAN"),
                                "kode_tarif": r.get("KODE TARIF"),
                                "tarif": flt(r.get("TARIF")),
                                "kode_fasilitas": r.get("KODE FASILITAS"),
                                "tarif_fasilitas": flt(r.get("TARIF FASILITAS")),
                                "nilai_bayar": flt(r.get("NILAI BAYAR")),
                                "nilai_fasilitas": flt(r.get("NILAI FASILITAS")),
                                "kode_asal_bahan_baku": r.get("KODE ASAL BAHAN BAKU"),
                                "jumlah_satuan": flt(r.get("JUMLAH SATUAN")),
                                "kode_satuan": r.get("KODE SATUAN")
                            })
                    bb_doc.set("bahan_tarif", child_bbt)
                    
                    # BB Dokumen
                    child_bbd = []
                    for r in bbd_rows:
                         if (cint(r.get("SERI BARANG")) == seri_barang and 
                            cint(r.get("SERI BAHAN BAKU")) == seri_bahan_baku):
                             child_bbd.append({
                                 "seri_dokumen": r.get("SERI DOKUMEN"),
                                 "seri_izin": r.get("SERI IZIN"),
                                 "kode_asal_bahan_baku": r.get("KODE_ASAL_BAHAN_BAKU")
                             })
                    bb_doc.set("bahan_baku_dokumen", child_bbd)
                    
                    save_doc(bb_doc)
                    
                    # Track BAHAN BAKU stats
                    audit_report["stats"]["BAHAN BAKU"] = audit_report["stats"].get("BAHAN BAKU", 0) + 1
                    audit_report["stats"]["BAHAN TARIF"] = audit_report["stats"].get("BAHAN TARIF", 0) + len(child_bbt)
                    audit_report["stats"]["BAHAN BAKU DOKUMEN"] = audit_report["stats"].get("BAHAN BAKU DOKUMEN", 0) + len(child_bbd)
        
        message = f"<b>Successfully processed {nomor_aju}</b>"
        
        # Add statistics to message
        if audit_report["stats"]:
            message += "<br><br><b>📊 Import Statistics:</b><br>"
            for table, count in audit_report["stats"].items():
                message += f"- {table}: {count} records<br>"
        
        # Add unmapped columns warning (data in Excel NOT inserted)
        if audit_report["unmapped_columns"]:
            message += "<br><b>⚠️ Unmapped Columns (data in Excel NOT inserted):</b><br>"
            for sheet, cols in audit_report["unmapped_columns"].items():
                message += f"- {sheet}: {', '.join(cols)}<br>"
        
        # Add missing columns info
        if audit_report["missing_columns"]:
            message += "<br><b>ℹ️ Missing Columns (expected but not in Excel):</b><br>"
            for sheet, cols in audit_report["missing_columns"].items():
                message += f"- {sheet}: {', '.join(cols)}<br>"
        
        if cint(dry_run):
            frappe.db.rollback()
            return {"status": "success", "message": "[DRY RUN] " + message, "audit": audit_report}
        
        frappe.db.commit()
        return {"status": "success", "message": message, "audit": audit_report}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Import CEISA Excel Refactored Error")
        error_msg = f"<b>Error during import:</b> {str(e)}"
        
        # Append stats to error message
        if audit_report["stats"]:
           error_msg += "<br><br><b>Partial Statistics:</b><br>"
           for k, v in audit_report["stats"].items():
                error_msg += f"- {k}: {v}<br>"
                
        return {"status": "error", "message": error_msg, "audit": audit_report}
