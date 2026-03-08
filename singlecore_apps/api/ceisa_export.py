import frappe
import json
import os
from frappe.utils import getdate, flt, cint
from decimal import Decimal, ROUND_HALF_UP

# Helper for exact decimal rounding (fixes jsonschema multipleOf validation)
def round_decimal(value, decimals=2):
    """Round to exact decimal precision using Decimal"""
    if value is None:
        return 0.0
    try:
        d = Decimal(str(flt(value)))
        if decimals == 2:
            res = float(d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        elif decimals == 4:
            res = float(d.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP))
        else:
            res = float(round(flt(value), decimals))
            
        # If whole number, return as int to satisfy strict JSON schemas
        if res == int(res):
            return int(res)
        return res
    except:
        return 0.0

# Helper to format date
def fmt_date(date_obj):
    if not date_obj: return None
    try:
        return getdate(date_obj).strftime('%Y-%m-%d')
    except:
        return str(date_obj).split(' ')[0]

def clean_nulls(obj):
    """Recursively remove None values from dicts and lists"""
    if isinstance(obj, dict):
        return {k: clean_nulls(v) for k, v in obj.items() if v is not None}
    elif isinstance(obj, list):
        return [clean_nulls(v) for v in obj if v is not None]
    return obj

# Helper for merk and tipe length (min 3 chars)
def clean_merk_tipe(value):
    value = str(value or "").strip()
    if not value or len(value) < 3:
        return "- / -"
    return value

# Helper for Entitas codes
def get_kode_entitas(value):
    if not value: return ""
    mapping = {
        "penerima": "1",
        "importir": "1",
        "eksportir": "2",
        "pengusaha tpb": "3",
        "pembeli": "4",
        "pemasok": "5",
        "pengirim": "5",
        "ppjk": "6",
        "pemilik barang": "7",
        "pemilik": "7",
        "penerima barang": "8",
        "penjual": "9"
    }
    val_lower = str(value).lower().strip()
    return mapping.get(val_lower, value)

# Helper for Identitas codes
def get_kode_identitas(value):
    if not value: return "5"
    mapping = {"npwp": "5", "ktp": "3", "paspor": "2", "lainnya": "4"}
    val_lower = str(value).lower().replace(" ", "").replace("-", "").strip()
    if val_lower == "npwp15digit": return "5"
    return mapping.get(val_lower, value)

# Helper for Afiliasi codes
def get_kode_afiliasi(value):
    if not value: return "0"
    mapping = {"tidak": "0", "ada": "1", "ya": "1", "no": "0"}
    val_lower = str(value).lower().strip()
    return mapping.get(val_lower, value)

# Helper for Pungutan codes
def get_kode_pungutan(value):
    if not value: return ""
    val_upper = str(value).upper().strip()
    if "BM" in val_upper and "KITE" in val_upper: return "BMKITE"
    if val_upper == "B.M.": return "BM"
    return val_upper

# Helper to get child table data
def get_child_data(doc, child_table_name, fields_map):
    data = []
    for child in (doc.get(child_table_name) or []):
        item = {}
        for json_field, doc_field in fields_map.items():
            val = child.get(doc_field)
            
            # Type casting and cleaning
            if any(s in json_field.lower() for s in ["seri", "idx"]):
                item[json_field] = cint(val)
            elif json_field in ["merk", "tipe", "merkKemasan", "tipeBarang"]:
                item[json_field] = clean_merk_tipe(val)
            elif json_field == "kodeEntitas":
                item[json_field] = get_kode_entitas(val)
            elif json_field == "kodeJenisIdentitas":
                item[json_field] = get_kode_identitas(val)
            elif json_field == "kodeAfiliasi":
                item[json_field] = get_kode_afiliasi(val)
            elif json_field == "kodeJenisPungutan":
                item[json_field] = get_kode_pungutan(val)
            elif "tanggal" in json_field.lower():
                item[json_field] = fmt_date(val)
            else:
                item[json_field] = val if val is not None else ""
        data.append(item)
    return data

@frappe.whitelist(allow_guest=True)
def get_ceisa_bc27_json(nomor_aju):
    """Export HEADER V21 to BC27 (TPB) JSON format"""
    try:
        doc = frappe.get_doc("HEADER V21", nomor_aju)
        
        # 1. Map Header Fields (BC27 specific)
        payload = {
            "asalData": "S",
            "asuransi": round_decimal(doc.get("asuransi"), 2),
            "bruto": round_decimal(doc.get("bruto"), 4),
            "cif": round_decimal(doc.get("cif"), 2),
            "dasarPengenaanPajak": round_decimal(doc.get("dasar_pengenaan_pajak"), 2),
            "disclaimer": doc.get("disclaimer") or "1",
            "freight": round_decimal(doc.get("freight"), 2),
            "hargaPenyerahan": round_decimal(doc.get("harga_penyerahan"), 4),
            "jabatanTtd": doc.get("jabatan_pernyataan") or "",
            "jumlahKontainer": len(doc.get("kontainer") or []),
            "kodeDokumen": "27",
            "kodeJenisTpb": doc.get("kode_jenis_tpb") or "",
            "kodeKantor": doc.get("kode_kantor") or "",
            "kodeKantorTujuan": doc.get("kode_kantor_tujuan") or "",
            "kodeTps": doc.get("kode_tps") or "",
            "kodeTujuanPengiriman": doc.get("kode_tujuan_pengiriman") or "",
            "kodeTujuanTpb": doc.get("kode_tujuan_tpb") or "",
            "kodeValuta": doc.get("kode_valuta") or "",
            "kotaTtd": doc.get("kota_pernyataan") or "",
            "namaTtd": doc.get("nama_pernyataan") or "",
            "ndpbm": round_decimal(doc.get("ndpbm"), 4),
            "netto": 0.0,  # Will be calculated from barang
            "nik": "",
            "nilaiBarang": round_decimal(doc.get("nilai_barang"), 2),
            "nilaiJasa": round_decimal(doc.get("nilai_jasa"), 2),
            "nomorAju": doc.get("nomoraju") or doc.name or "",
            "seri": 0,
            "tanggalAju": fmt_date(doc.get("tanggal_pernyataan")),
            "tanggalTtd": fmt_date(doc.get("tanggal_pernyataan")),
            "biayaTambahan": round_decimal(doc.get("biaya_tambahan"), 2),
            "biayaPengurang": round_decimal(doc.get("biaya_pengurang"), 2),
            "uangMuka": round_decimal(doc.get("uang_muka"), 2),
            "vd": round_decimal(doc.get("vd"), 4),
            "ppnPajak": round_decimal(doc.get("ppn_pajak"), 2),
            "ppnbmPajak": round_decimal(doc.get("ppnbm_pajak"), 2),
            "tarifPpnPajak": round_decimal(doc.get("tarif_ppn_pajak"), 2),
            "tarifPpnbmPajak": round_decimal(doc.get("tarif_ppnbm_pajak"), 2),
        }

        # 2. Map Entitas (Strict Ordering for BC27: 3, 7, 8)
        entitas_map = {ent.kode_entitas: ent for ent in doc.entitas}
        payload["entitas"] = []
        ordered_codes = ["3", "7", "8"]
        
        for idx, kode in enumerate(ordered_codes):
            ent = entitas_map.get(kode)
            if ent:
                ent_item = {
                    "alamatEntitas": ent.get("alamat_entitas") or "",
                    "kodeEntitas": kode,
                    "namaEntitas": ent.get("nama_entitas") or "",
                    "seriEntitas": idx + 1, # Integer
                    "nomorIdentitas": ent.get("nomor_identitas") or "",
                    "nibEntitas": ent.get("nib_entitas") or "",
                    "kodeJenisIdentitas": get_kode_identitas(ent.get("kode_jenis_identitas")),
                    "kodeStatus": ent.get("kode_status") or "10",
                    "kodeJenisApi": ent.get("kode_jenis_api") or "01",
                    "nomorIjinEntitas": ent.get("nomor_ijin_entitas") or "-",
                    "tanggalIjinEntitas": fmt_date(ent.get("tanggal_ijin_entitas")) or fmt_date(doc.get("tanggal_pernyataan")) or frappe.utils.nowdate()
                }
                payload["entitas"].append(ent_item)

        # 3. Map Dokumen
        payload["dokumen"] = get_child_data(doc, "dokumen", {
            "kodeDokumen": "kode_dokumen",
            "nomorDokumen": "nomor_dokumen",
            "seriDokumen": "seri",
            "tanggalDokumen": "tanggal_dokumen"
        })

        # 4. Map Pengangkut
        payload["pengangkut"] = []
        for p in (doc.get("pengangkut") or []):
             payload["pengangkut"].append({
                "namaPengangkut": p.get("nama_pengangkut") or "",
                "nomorPengangkut": p.get("nomor_pengangkut") or "",
                "seriPengangkut": str(p.get("seri_pengangkut") or (p.idx)) # String required
             })

        # 5. Map Kemasan
        payload["kemasan"] = []
        for kem in (doc.get("kemasan") or []):
            payload["kemasan"].append({
                "jumlahKemasan": cint(kem.get("jumlah_kemasan")), # Integer required
                "kodeJenisKemasan": kem.get("kode_kemasan") or "",
                "merkKemasan": clean_merk_tipe(kem.get("merek_kemasan")),
                "seriKemasan": cint(kem.get("seri")) or 0,
            })

        # 6. Map Kontainer
        payload["kontainer"] = get_child_data(doc, "kontainer", {
            "seriKontainer": "seri",
            "nomorKontainer": "nomor_kontainer",
            "kodeUkuranKontainer": "kode_ukuran_kontainer",
            "kodeJenisKontainer": "kode_jenis_kontainer",
            "kodeTipeKontainer": "kode_tipe_kontainer",
        })

        # 7. Map Pungutan
        payload["pungutan"] = []
        for pung in (doc.get("pungutan") or []):
            payload["pungutan"].append({
                "idPungutan": "",
                "kodeFasilitasTarif": pung.kode_fasilitas_tarif or "1",
                "kodeJenisPungutan": get_kode_pungutan(pung.kode_jenis_pungutan),
                "nilaiPungutan": round_decimal(pung.nilai_pungutan, 2),
            })

        # 8. Map Barang V1
        barang_list = []
        barangs = frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc")
        total_netto = 0.0
        for brg in barangs:
            brg_item = {
                "cif": round_decimal(brg.get("cif"), 2),
                "cifRupiah": round_decimal(brg.get("cif_rupiah"), 2),
                "hargaEkspor": round_decimal(brg.get("harga_ekspor"), 2),
                "hargaPenyerahan": round_decimal(brg.get("harga_penyerahan"), 4),
                "hargaPerolehan": round_decimal(brg.get("harga_perolehan"), 2),
                "isiPerKemasan": round_decimal(brg.get("isi_per_kemasan"), 2),
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4),
                "kodeBarang": brg.get("kode_barang") or "",
                "kodeDokumen": "27", # Default to 27 or empty? Schema check needed.
                "kodeKategoriBarang": brg.get("kode_kategori_barang") or "",
                "kodeSatuanBarang": brg.get("kode_satuan") or "",
                "merk": clean_merk_tipe(brg.get("merek")),
                "ndpbm": round_decimal(brg.get("ndpbm"), 4) or 1.0,
                "netto": round_decimal(brg.get("netto"), 4),
                "nilaiBarang": round_decimal(brg.get("nilai_barang"), 2),
                "nilaiJasa": round_decimal(brg.get("nilai_jasa"), 2),
                "posTarif": brg.get("hs") or "",
                "seriBarang": str(brg.get("seri_barang") or 0), # String required
                "spesifikasiLain": brg.get("spesifikasi_lain") or "",
                "tipe": clean_merk_tipe(brg.get("tipe")),
                "uangMuka": 0,
                "ukuran": brg.get("ukuran") or "",
                "uraian": brg.get("uraian") or "",
            }
            
            # BAHAN BAKU 
            brg_item["bahanBaku"] = []
            bahan_bakus = frappe.get_all("BAHAN BAKU", filters={"parent_barang": brg.get("name")}, fields=["*"], order_by="seri_bahan_baku asc")
            for bb in bahan_bakus:
                bb_doc = frappe.get_doc("BAHAN BAKU", bb.get("name"))
                bb_item = {
                    "cif": round_decimal(bb.get("cif"), 2),
                    "cifRupiah": round_decimal(bb.get("cif_rupiah"), 2),
                    "hargaPenyerahan": round_decimal(bb.get("harga_penyerahan"), 4),
                    "hargaPerolehan": round_decimal(bb.get("harga_perolehan"), 2),
                    "jumlahSatuan": round_decimal(bb.get("jumlah_satuan"), 4),
                    "kodeAsalBahanBaku": bb.get("kode_asal_bahan_baku") or "0",
                    "kodeBarang": bb.get("kode_barang") or "",
                    "kodeDokAsal": bb.get("kode_dokumen_asal") or "27",
                    "kodeKantor": bb.get("kode_kantor_asal") or doc.get("kode_kantor") or "",
                    "kodeSatuanBarang": bb.get("kode_satuan") or "",
                    "merkBarang": clean_merk_tipe(bb.get("merek")),
                    "ndpbm": round_decimal(bb.get("ndpbm"), 4) or 1.0,
                    "netto": round_decimal(bb.get("netto"), 4),
                    "nilaiJasa": 0,
                    "nomorAjuDokAsal": bb.get("nomor_aju_asal") or "",
                    "nomorDaftarDokAsal": bb.get("nomor_daftar_asal") or "",
                    "posTarif": bb.get("hs") or "",
                    "seriBahanBaku": cint(bb.get("seri_bahan_baku")) or 0,
                    "seriBarang": cint(brg.get("seri_barang")) or 0,
                    "seriBarangDokAsal": cint(bb.get("seri_barang_asal")) or 0,
                    "seriIjin": 0,
                    "spesifikasiLainBarang": bb.get("spesifikasi_lain") or "",
                    "tanggalDaftarDokAsal": fmt_date(bb.get("tanggal_daftar_asal")) or fmt_date(doc.get("tanggal_pernyataan")) or frappe.utils.nowdate(),
                    "tipeBarang": clean_merk_tipe(bb.get("tipe")),
                    "ukuranBarang": bb.get("ukuran") or "",
                    "uraianBarang": bb.get("uraian") or "",
                }
                
                # BahanBakuTarif
                bb_item["bahanBakuTarif"] = []
                for bbt in bb_doc.get("bahan_tarif") or []:
                    bb_item["bahanBakuTarif"].append({
                        "seriBahanBaku": cint(bb.get("seri_bahan_baku")) or 0,
                        "kodeJenisPungutan": get_kode_pungutan(bbt.kode_pungutan),
                        "kodeAsalBahanBaku": bbt.kode_asal_bahan_baku or bb.get("kode_asal_bahan_baku") or "0",
                        "kodeFasilitasTarif": bbt.kode_fasilitas or "5",
                        "nilaiBayar": round_decimal(bbt.nilai_bayar, 2),
                        "nilaiFasilitas": round_decimal(bbt.nilai_fasilitas, 2),
                        "nilaiSudahDilunasi": round_decimal(bbt.nilai_sudah_dilunasi, 2) or 0,
                        "tarif": round_decimal(bbt.tarif, 2),
                        "tarifFasilitas": round_decimal(bbt.tarif_fasilitas, 2),
                        "jumlahSatuan": round_decimal(bbt.jumlah_satuan, 4),
                        "kodeJenisTarif": bbt.kode_tarif or "1",
                        "jumlahKemasan": 0,
                    })
                
                brg_item["bahanBaku"].append(bb_item)

            total_netto += round_decimal(brg.get("netto"), 4)
            barang_list.append(brg_item)

        payload["barang"] = barang_list
        payload["netto"] = round_decimal(total_netto, 4)
        
        return payload
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get CEISA BC27 JSON Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist(allow_guest=True)
def get_ceisa_bc20_json(nomor_aju):
    # Implementation similar to bc27 but with different specific fields or structure if needed
    # For now, reusing the logic derived from api.py, which seems to have separate functions.
    # The extraction logic is identical to bc27_json above but I should double check if there are differences.
    # Looking at lines 865+ in api.py, it looks nearly identical but might have subtle differences.
    # I'll perform the same logic as above.
    
    try:
        doc = frappe.get_doc("HEADER V21", nomor_aju)

        # 1. Map Header Fields - Same as above 
        payload = {
            "nomorAju": doc.get("nomoraju") or doc.name or "",
            "tanggalAju": fmt_date(doc.get("tanggal_pernyataan")),
            "asalData": "S",  # Schema requires constant "S"
            "asuransi": round_decimal(doc.get("asuransi"), 2),  # multipleOf 0.01
            "bruto": round_decimal(doc.get("bruto"), 4),  # multipleOf 0.0001
            "cif": round_decimal(doc.get("cif"), 2),  # multipleOf 0.01
            "disclaimer": doc.get("disclaimer") or "1",
            "fob": round_decimal(doc.get("fob"), 2),  # multipleOf 0.01
            "freight": round_decimal(doc.get("freight"), 2),  # multipleOf 0.01
            "jabatanTtd": doc.get("jabatan_pernyataan") or "",
            "jumlahKontainer": len( (doc.get("kontainer") or [])), 
            "jumlahTandaPengaman": cint(doc.get("jumlah_tanda_pengaman")) if hasattr(doc, 'jumlah_tanda_pengaman') else 0,
            "kodeAsuransi": doc.get("kode_asuransi") or "LN",
            "kodeCaraBayar": doc.get("kode_cara_bayar") or "",
            "kodeDokumen": "20",  # Schema requires constant "20" for BC 2.0
            "kodeIncoterm": doc.get("kode_incoterm") or "",
            "kodeJenisNilai": doc.get("kode_jenis_nilai") or "",
            "kodeJenisProsedur": doc.get("kode_jenis_pib") or "",
            "kodeKantor": doc.get("kode_kantor") or "",
            "kodePelMuat": doc.get("kode_pelabuhan_muat") or "",
            "kodePelTujuan": doc.get("kode_pelabuhan_tujuan") or "",
            "kodeTps": doc.get("kode_tps") or "",
            "kodeValuta": doc.get("kode_valuta") or "",
            "kotaTtd": doc.get("kota_pernyataan") or "",
            "namaTtd": doc.get("nama_pernyataan") or "",
            "ndpbm": round_decimal(doc.get("ndpbm"), 4) or 1.0,  # Should not be 0
            "netto": 0.0, # Will be calculated from barang
            "nilaiMaklon": round_decimal(doc.get("nilai_maklon"), 2),  # multipleOf 0.01
            "seri": 1, 
            "tanggalTtd": fmt_date(doc.get("tanggal_pernyataan")),
            "totalDanaSawit": round_decimal(doc.get("total_dana_sawit"), 2),  # multipleOf 0.01
            "biayaPengurang": round_decimal(doc.get("biaya_pengurang"), 2),  # multipleOf 0.01
            "biayaTambahan": round_decimal(doc.get("biaya_tambahan"), 2),  # multipleOf 0.01
            "flagVd": doc.get("flag_vd") or "T",
            "hargaPenyerahan": round_decimal(doc.get("harga_penyerahan"), 4),  # multipleOf 0.0001
            "kodeJenisImpor": doc.get("kode_jenis_impor") or "",
            "kodeJenisEkspor": (doc.get("kode_jenis_ekspor") or "") if hasattr(doc, 'kode_jenis_ekspor') else "",
            "kodeTutupPu": doc.get("kode_tutup_pu") or "11",
            "nilaiBarang": round_decimal(doc.get("nilai_barang"), 2),  # multipleOf 0.01
            "nilaiIncoterm": round_decimal(doc.get("nilai_incoterm"), 2),  # multipleOf 0.01
            "nomorBc11": doc.get("nomor_bc11") or "",
            "posBc11": doc.get("nomor_pos") or "",
            "subposBc11": doc.get("nomor_sub_pos") or "",
            "tanggalBc11": fmt_date(doc.get("tanggal_bc11")),
            "tanggalTiba": fmt_date(doc.get("tanggal_tiba")),
            "volume": round_decimal(doc.get("volume"), 4),  # multipleOf 0.0001
            "vd": round_decimal(doc.get("vd"), 4),  # multipleOf 0.0001
        }


        # 2. Map Entitas - sorted by kodeEntitas in BC20 Schema order: 1, 7, 9, 10, 11, 4, ...
        # Then assign sequential seriEntitas (1, 2, 3, ...)
        entitas_raw = doc.get("entitas") or []

        # Build lookup: kodeEntitas -> list of entitas rows
        entitas_by_kode = {}
        for ent in entitas_raw:
            kode = get_kode_entitas(ent.get("kode_entitas"))
            entitas_by_kode.setdefault(kode, []).append(ent)

        # Required order per BC20 schema
        KODE_ORDER = ["1", "7", "9", "10", "11", "4"]

        # Build sorted list: required order first, then any remaining
        sorted_entitas = []
        seen_kodes = set()
        for kode in KODE_ORDER:
            for ent in entitas_by_kode.get(kode, []):
                sorted_entitas.append((kode, ent))
            seen_kodes.add(kode)
        # Append any remaining kodes not in KODE_ORDER
        for kode, ents in entitas_by_kode.items():
            if kode not in seen_kodes:
                for ent in ents:
                    sorted_entitas.append((kode, ent))

        payload["entitas"] = []
        for seri, (kode, ent) in enumerate(sorted_entitas, start=1):
            ent_item = {
                "alamatEntitas": ent.get("alamat_entitas") or "",
                "kodeEntitas": kode,
                "namaEntitas": ent.get("nama_entitas") or "",
                "seriEntitas": seri,
            }

            if kode == "1":  # Importir
                ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                ent_item["kodeJenisApi"] = ent.get("kode_jenis_api") or ""
                ent_item["kodeStatus"] = ent.get("kode_status") or ""
                ent_item["nibEntitas"] = ent.get("nib_entitas") or ""
                ent_item["nomorIdentitas"] = ent.get("nomor_identitas") or ""
            elif kode == "7":  # Pemilik Barang
                ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                ent_item["nomorIdentitas"] = ent.get("nomor_identitas") or ""
                ent_item["kodeAfiliasi"] = get_kode_afiliasi(ent.get("kode_afiliasi"))
            elif kode == "9":  # Pengirim
                ent_item["kodeNegara"] = ent.get("kode_negara") or "ID"
            elif kode == "10":  # Penjual
                ent_item["kodeNegara"] = ent.get("kode_negara") or "ID"
            elif kode == "11":  # Pemusatan
                ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                ent_item["nomorIdentitas"] = ent.get("nomor_identitas") or ""
            elif kode == "4":  # PPJK
                ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                ent_item["nomorIdentitas"] = ent.get("nomor_identitas") or ""

            payload["entitas"].append(ent_item)

        payload["kemasan"] = get_child_data(doc, "kemasan", {
            "jumlahKemasan": "jumlah_kemasan",
            "kodeJenisKemasan": "kode_kemasan",  # DocType uses 'kode_kemasan'
            "merkKemasan": "merek_kemasan",
            "seriKemasan": "seri"  # DocType uses 'seri' not 'seri_kemasan'
        })

        payload["dokumen"] = get_child_data(doc, "dokumen", {
            "kodeDokumen": "kode_dokumen",
            "nomorDokumen": "nomor_dokumen",
            "seriDokumen": "seri",
            "tanggalDokumen": "tanggal_dokumen"
        })

        payload["pengangkut"] = get_child_data(doc, "pengangkut", {
            "kodeBendera": "kode_bendera",
            "namaPengangkut": "nama_pengangkut",
            "nomorPengangkut": "nomor_pengangkut",
            "kodeCaraAngkut": "kode_cara_angkut",
            "seriPengangkut": "seri_pengangkut"
        })
        for p in payload["pengangkut"]:
            if not p.get("seriPengangkut"):
                p["seriPengangkut"] = 1

        
        payload["kontainer"] = get_child_data(doc, "kontainer", {
            "kodeTipeKontainer": "kode_tipe_kontainer",
            "kodeUkuranKontainer": "kode_ukuran_kontainer",
            "nomorKontainer": "nomor_kontainer",
            "seriKontainer": "seri_kontainer",
            "kodeJenisKontainer": "kode_jenis_kontainer"
        })

        # 3. Map Barang V1
        barang_list = []
        barangs = frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc")
        
        total_netto = 0.0

        for brg in barangs:
            brg_netto = round_decimal(brg.get("netto"), 4)
            total_netto += brg_netto

            brg_item = {
                "asuransi": round_decimal(brg.get("asuransi"), 2),
                "bruto": round_decimal(brg.get("bruto"), 4),
                "cif": round_decimal(brg.get("cif"), 2),
                "cifRupiah": round_decimal(brg.get("cif_rupiah"), 2),
                "diskon": round_decimal(brg.get("diskon"), 2),
                "fob": round_decimal(brg.get("fob"), 2),
                "freight": round_decimal(brg.get("freight"), 2),
                "hargaEkspor": round_decimal(brg.get("harga_ekspor"), 2),
                "hargaPatokan": round_decimal(brg.get("harga_patokan"), 2),
                "hargaPenyerahan": round_decimal(brg.get("harga_penyerahan"), 2),
                "hargaPerolehan": round_decimal(brg.get("harga_perolehan"), 2),
                "hargaSatuan": round_decimal(brg.get("harga_satuan"), 2),
                "hjeCukai": round_decimal(brg.get("hje_cukai"), 2),
                "isiPerKemasan": round_decimal(brg.get("isi_per_kemasan"), 2),
                "jumlahBahanBaku": cint(brg.get("jumlah_bahan_baku")) or 0,
                "jumlahDilekatkan": cint(brg.get("jumlah_dilekatkan")) or 0,
                "jumlahKemasan": round_decimal(brg.get("jumlah_kemasan"), 2),
                "jumlahPitaCukai": cint(brg.get("jumlah_pita_cukai")) or 0,
                "jumlahRealisasi": round_decimal(brg.get("jumlah_realisasi"), 2),
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4),
                "kapasitasSilinder": cint(brg.get("kapasitas_silinder")) or 0,
                "kodeJenisKemasan": brg.get("kode_kemasan") or "",
                "kodeKondisiBarang": brg.get("kode_kondisi_barang") or "1",
                "kodeNegaraAsal": brg.get("kode_negara_asal") or "",
                "kodeSatuanBarang": brg.get("kode_satuan") or "",
                "merk": clean_merk_tipe(brg.get("merek")),
                "ndpbm": round_decimal(brg.get("ndpbm"), 4),
                "netto": brg_netto,
                "nilaiBarang": round_decimal(brg.get("nilai_barang"), 2),
                "nilaiDanaSawit": round_decimal(brg.get("nilai_dana_sawit"), 2),
                "nilaiDevisa": round_decimal(brg.get("nilai_devisa"), 2),
                "nilaiTambah": round_decimal(brg.get("nilai_tambah"), 2),
                "pernyataanLartas": brg.get("pernyataan_lartas") or "T",
                "persentaseImpor": round_decimal(brg.get("persentase_impor"), 2),
                "posTarif": brg.get("hs") or "",
                "saldoAkhir": round_decimal(brg.get("saldo_akhir"), 2),
                "saldoAwal": round_decimal(brg.get("saldo_awal"), 2),
                "seriBarang": cint(brg.get("seri_barang")) or 0,
                "seriBarangDokAsal": cint(brg.get("seri_barang_asal")) or 0,
                "seriIjin": cint(brg.get("seri_izin")) or 0,
                "tahunPembuatan": cint(brg.get("tahun_pembuatan")) or 0,
                "tarifCukai": round_decimal(brg.get("tarif_cukai"), 2),
                "tipe": clean_merk_tipe(brg.get("tipe")),
                "uraian": brg.get("uraian") or "",
                "volume": round_decimal(brg.get("volume"), 4),
                "metodePenentuanNilai": brg.get("metode_penentuan_nilai") or "Metode 1",
                "alasanMetodePenentuanNilai": brg.get("alasan_metode_penentuan_nilai") or None,
                "statementPerbedaanHarga": brg.get("statement_perbedaan_harga") or "T",
            }
            
            # Fetch Child Tables for this Barang
            brg_doc = frappe.get_doc("BARANG V1", brg.get("name")) 
            
            # 3a. BARANG TARIF - Sorted to have BM at index 0 (Schema requirement)
            tarif_raw = []
            for trf in brg_doc.get("barang_tarif") or []:
                tarif_raw.append({
                    "tarif": round_decimal(trf.get("tarif"), 2),
                    "nilaiBayar": round_decimal(trf.get("nilai_bayar"), 2),
                    "seriBarang": cint(trf.get("seri_barang")) or 0,
                    "kodeKemasan": "",
                    "jumlahSatuan": round_decimal(trf.get("jumlah_satuan"), 4),
                    "jumlahKemasan": 0,
                    "kodeJenisTarif": trf.get("kode_tarif") or "",
                    "nilaiFasilitas": round_decimal(trf.get("nilai_fasilitas"), 2),
                    "tarifFasilitas": round_decimal(trf.get("tarif_fasilitas"), 2),
                    "kodeSatuanBarang": trf.get("kode_satuan") or "",
                    "kodeJenisPungutan": trf.get("kode_pungutan") or "",
                    "kodeKomoditiCukai": "",
                    "kodeFasilitasTarif": trf.get("kode_fasilitas") or "",
                    "nilaiSudahDilunasi": round_decimal(trf.get("nilai_sudah_dilunasi"), 2),
                    "kodeSubKomoditiCukai": ""
                })
            
            # Sort: BM first, then Others
            brg_item["barangTarif"] = sorted(tarif_raw, key=lambda x: 0 if x.get("kodeJenisPungutan") == "BM" else 1)

            # 3b. BARANG DOKUMEN
            brg_item["barangDokumen"] = []
            for dok in brg_doc.get("barang_dokumen") or []:
                brg_item["barangDokumen"].append({
                    "seriDokumen": dok.get("seri_dokumen"),
                    "seriIzin": dok.get("seri_izin")
                })
                
            # 3c. BARANG SPEK KHUSUS
            brg_item["barangSpekKhusus"] = []
            for spek in brg_doc.get("barang_spek_khusus") or []:
                brg_item["barangSpekKhusus"].append({
                    "seriBarangSpekKhusus": spek.idx,
                    "kodeSpekKhusus": cint(spek.kode_spek_khusus),
                    "uraianBarangSpekKhusus": spek.uraian_spek_khusus
                })
                
            # 3d. BARANG VD (Mandatory in Schema)
            brg_item["barangVd"] = []
            for vd in brg_doc.get("barang_vd") or []:
                brg_item["barangVd"].append({
                    "kodeJenisVd": vd.get("kode_jenis_vd"),
                    "nilaiBarangVd": round_decimal(vd.get("nilai_barang_vd"), 4)
                })
                
            # 3e. BARANG PEMILIK
            brg_item["barangPemilik"] = []
            for pml in brg_doc.get("barang_pemilik") or []:
                brg_item["barangPemilik"].append({
                    "seriBarang": cint(pml.seri_barang),
                    "seriBarangPemilik": cint(pml.seri_barang_pemilik),
                    "seriEntitas": cint(pml.seri_entitas)
                })

            barang_list.append(brg_item)

        payload["barang"] = barang_list
        payload["netto"] = round_decimal(total_netto, 4)

        # Add komponen biaya (informasiKomponenBiaya)
        payload["informasiKomponenBiaya"] = []
        for kb in (doc.get("komponen_biaya") or []):
            payload["informasiKomponenBiaya"].append({
                "jenisNilai": kb.jenisnilai,
                "hargaInvoice": kb.hargainvoice,
                "pembayaranTidakLangsung": kb.pembayarantidaklangsung,
                "diskon": kb.diskon,
                "komisiPenjualan": kb.komisipenjualan,
                "biayaPengemasan": kb.biayapengemasan,
                "biayaPengepakan": kb.biayapengepakan,
                "assist": kb.assist,
                "royalti": kb.royalti,
                "proceeds": kb.proceeds,
                "biayaTransportasi": kb.biayatransportasi,
                "biayaPemuatan": kb.biayapemuatan,
                "asuransi": kb.asuransi,
                "garansi": kb.garansi,
                "biayaKepentinganSendiri": kb.biayakepentingansendiri,
                "biayaPascaImpor": kb.biayapascaimpor,
                "biayaPajakInternal": kb.biayapajakinternal,
                "bunga": kb.bunga,
                "deviden": kb.deviden
            })
        
        # Clean up fields that CEISA rejects if null (must be omitted if empty)
        if payload.get("tanggalBc11") is None:
            payload.pop("tanggalBc11", None)
            
        return payload

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get CEISA BC20 JSON Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist(allow_guest=True)
def get_ceisa_bc23_json(nomor_aju):
    """Export HEADER V21 to BC23 (TPB Import) JSON format"""
    try:
        doc = frappe.get_doc("HEADER V21", nomor_aju)
        
        # 1. Map Header Fields (BC23 specific)
        payload = {
            "asalData": "S",
            "asuransi": round_decimal(doc.get("asuransi"), 2),
            "bruto": round_decimal(doc.get("bruto"), 4),
            "cif": round_decimal(doc.get("cif"), 2),
            "fob": round_decimal(doc.get("fob"), 2),
            "freight": round_decimal(doc.get("freight"), 2),
            "hargaPenyerahan": round_decimal(doc.get("harga_penyerahan"), 4),
            "jabatanTtd": doc.get("jabatan_pernyataan") or "",
            "jumlahKontainer": len(doc.get("kontainer") or []),
            "kodeAsuransi": doc.get("kode_asuransi") or "LN",
            "kodeDokumen": "23",
            "kodeIncoterm": doc.get("kode_incoterm") or "",
            "kodeKantor": doc.get("kode_kantor") or "",
            "kodeKantorBongkar": doc.get("kode_kantor_bongkar") or "",
            "kodePelBongkar": doc.get("kode_pelabuhan_bongkar") or "",
            "kodePelMuat": doc.get("kode_pelabuhan_muat") or "",
            "kodePelTransit": doc.get("kode_pelabuhan_transit") or "",
            "kodeTps": doc.get("kode_tps") or "",
            "kodeTujuanTpb": doc.get("kode_tujuan_tpb") or "",
            "kodeTutupPu": doc.get("kode_tutup_pu") or "11",
            "kodeValuta": doc.get("kode_valuta") or "",
            "kotaTtd": doc.get("kota_pernyataan") or "",
            "namaTtd": doc.get("nama_pernyataan") or "",
            "ndpbm": round_decimal(doc.get("ndpbm"), 4) or 1.0,
            "netto": 0.0, # Will be calculated from barang
            "nik": "",
            "nilaiBarang": round_decimal(doc.get("nilai_barang"), 2),
            "nomorAju": doc.get("nomoraju") or doc.name or "",
            "nomorBc11": doc.get("nomor_bc11") or "",
            "posBc11": doc.get("nomor_pos") or "",
            "seri": 0,
            "subposBc11": doc.get("nomor_sub_pos") or "",
            "tanggalBc11": fmt_date(doc.get("tanggal_bc11")),
            "tanggalTiba": fmt_date(doc.get("tanggal_tiba")),
            "tanggalTtd": fmt_date(doc.get("tanggal_pernyataan")),
            "biayaTambahan": round_decimal(doc.get("biaya_tambahan"), 2),
            "biayaPengurang": round_decimal(doc.get("biaya_pengurang"), 2),
            "kodeKenaPajak": doc.get("kode_jasa_kena_pajak") or "",
        }

        # 2. Map Entitas
        payload["entitas"] = []
        for ent in (doc.get("entitas") or []):
            ent_item = {
                "alamatEntitas": ent.get("alamat_entitas") or "",
                "kodeEntitas": get_kode_entitas(ent.get("kode_entitas")),
                "namaEntitas": ent.get("nama_entitas") or "",
                "seriEntitas": cint(ent.get("seri")) or 0,
            }
            if ent.get("kode_entitas") == "3":
                ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                ent_item["nibEntitas"] = ent.get("nib_entitas") or ""
                ent_item["nomorIdentitas"] = ent.get("nomor_identitas") or ""
                ent_item["nomorIjinEntitas"] = ent.get("nomor_ijin_entitas") or ""
                # Omit if empty instead of sending null or ""
                tgl_ijin = fmt_date(ent.get("tanggal_ijin_entitas"))
                if tgl_ijin:
                    ent_item["tanggalIjinEntitas"] = tgl_ijin
            elif ent.get("kode_entitas") == "5":
                ent_item["kodeNegara"] = ent.get("kode_negara") or ""
            elif ent.get("kode_entitas") == "7":
                ent_item["kodeJenisApi"] = ent.get("kode_jenis_api") or ""
                ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                ent_item["kodeStatus"] = ent.get("kode_status") or "10"
                ent_item["nomorIdentitas"] = ent.get("nomor_identitas") or ""
                ent_item["nomorIjinEntitas"] = ent.get("nomor_ijin_entitas") or ""
                tgl_ijin = fmt_date(ent.get("tanggal_ijin_entitas"))
                if tgl_ijin:
                    ent_item["tanggalIjinEntitas"] = tgl_ijin
            payload["entitas"].append(ent_item)
        
        # Sort entitas: 3 (Pengusaha TPB), 5 (Pemasok), 7 (Pemilik Barang)
        payload["entitas"] = sorted(payload["entitas"], key=lambda x: {"3": 0, "5": 1, "7": 2}.get(x.get("kodeEntitas"), 99))

        # 3. Map Kemasan
        payload["kemasan"] = []
        for kem in (doc.get("kemasan") or []):
            payload["kemasan"].append({
                "jumlahKemasan": cint(kem.get("jumlah_kemasan")), # Must be integer for BC23
                "kodeJenisKemasan": kem.get("kode_kemasan") or "",
                "seriKemasan": cint(kem.get("seri")) or 0,
                "merkKemasan": clean_merk_tipe(kem.get("merek_kemasan")),
            })

        # 4. Map Kontainer
        payload["kontainer"] = get_child_data(doc, "kontainer", {
            "kodeTipeKontainer": "kode_tipe_kontainer",
            "kodeUkuranKontainer": "kode_ukuran_kontainer",
            "nomorKontainer": "nomor_kontainer",
            "seriKontainer": "seri",
            "kodeJenisKontainer": "kode_jenis_kontainer",
        })

        # 5. Map Dokumen (Positional: 0=Invoice, 1=BL/AWB, 2=Others)
        all_docs = get_child_data(doc, "dokumen", {
            "kodeDokumen": "kode_dokumen",
            "nomorDokumen": "nomor_nomor_dokumen" if "nomor_nomor_dokumen" in [f.fieldname for f in doc.meta.get_table_fields()] else "nomor_dokumen",
            "seriDokumen": "seri",
            "tanggalDokumen": "tanggal_dokumen"
        })
        
        # In case the child table field name is different in some environments
        for d in all_docs:
            if not d.get("nomorDokumen") and doc.get("dokumen") and len(doc.get("dokumen")) > 0:
                 # Fallback if get_child_data mapping failed for some reason
                 pass

        invoice_docs = [d for d in all_docs if d.get("kodeDokumen") == "380"]
        bl_awb_docs = [d for d in all_docs if d.get("kodeDokumen") in ["705", "740"]]
        other_docs = [d for d in all_docs if d.get("kodeDokumen") not in ["380", "705", "740"]]
        
        payload["dokumen"] = invoice_docs + bl_awb_docs + other_docs

        # 6. Map Pengangkut
        payload["pengangkut"] = get_child_data(doc, "pengangkut", {
            "kodeBendera": "kode_bendera",
            "namaPengangkut": "nama_pengangkut",
            "nomorPengangkut": "nomor_pengangkut",
            "kodeCaraAngkut": "kode_cara_angkut",
            "seriPengangkut": "seri_pengangkut"
        })

        # 7. Map Barang V1
        barang_list = []
        barangs = frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc")
        
        total_netto = 0.0
        for brg in barangs:
            brg_netto = round_decimal(brg.get("netto"), 4)
            total_netto += brg_netto
            
            brg_item = {
                "idBarang": "",
                "asuransi": round_decimal(brg.get("asuransi"), 2),
                "cif": round_decimal(brg.get("cif"), 2),
                "diskon": round_decimal(brg.get("diskon"), 2),
                "fob": round_decimal(brg.get("fob"), 2),
                "freight": round_decimal(brg.get("freight"), 2),
                "hargaEkspor": round_decimal(brg.get("harga_ekspor"), 2),
                "hargaPenyerahan": round_decimal(brg.get("harga_penyerahan"), 4),
                "hargaSatuan": round_decimal(brg.get("harga_satuan"), 2),
                "isiPerKemasan": round_decimal(brg.get("isi_per_kemasan"), 2),
                "jumlahKemasan": round_decimal(brg.get("jumlah_kemasan"), 2),
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4),
                "kodeBarang": brg.get("kode_barang") or "",
                "kodeDokumen": "",
                "kodeKategoriBarang": brg.get("kode_kategori_barang") or "",
                "kodeJenisKemasan": brg.get("kode_kemasan") or "",
                "kodeNegaraAsal": brg.get("kode_negara_asal") or "ID", # Should not be empty if pattern is enforced
                "kodePerhitungan": brg.get("kode_perhitungan") or "0",
                "kodeSatuanBarang": brg.get("kode_satuan") or "",
                "merk": clean_merk_tipe(brg.get("merek")),
                "netto": brg_netto,
                "nilaiBarang": round_decimal(brg.get("nilai_barang"), 2),
                "nilaiTambah": round_decimal(brg.get("nilai_tambah"), 2),
                "posTarif": brg.get("hs") or "",
                "seriBarang": cint(brg.get("seri_barang")) or 0,
                "spesifikasiLain": brg.get("spesifikasi_lain") or "",
                "tipe": clean_merk_tipe(brg.get("tipe")),
                "ukuran": brg.get("ukuran") or "",
                "uraian": brg.get("uraian") or "",
                "ndpbm": round_decimal(brg.get("ndpbm"), 4) or 1.0,
                "cifRupiah": round_decimal(brg.get("cif_rupiah"), 2),
                "hargaPerolehan": round_decimal(brg.get("harga_perolehan"), 2),
                "kodeAsalBahanBaku": brg.get("kode_asal_barang") or "0",
            }
            
            brg_doc = frappe.get_doc("BARANG V1", brg.get("name"))
            
            # BARANG TARIF
            brg_item["barangTarif"] = []
            for trf in brg_doc.get("barang_tarif") or []:
                brg_item["barangTarif"].append({
                    "kodeJenisTarif": trf.get("kode_tarif") or "1",
                    "jumlahSatuan": round_decimal(trf.get("jumlah_satuan"), 4),
                    "kodeFasilitasTarif": trf.get("kode_fasilitas") or "1",
                    "kodeSatuanBarang": trf.get("kode_satuan") or "",
                    "kodeJenisPungutan": get_kode_pungutan(trf.get("kode_pungutan")),
                    "nilaiBayar": round_decimal(trf.get("nilai_bayar"), 2),
                    "nilaiFasilitas": round_decimal(trf.get("nilai_fasilitas"), 2),
                    "nilaiSudahDilunasi": round_decimal(trf.get("nilai_sudah_dilunasi"), 2) or 0,
                    "seriBarang": cint(brg.get("seri_barang")) or 0,
                    "tarif": round_decimal(trf.get("tarif"), 2),
                    "tarifFasilitas": round_decimal(trf.get("tarif_fasilitas"), 2),
                })
            
            # Sort tarif: BM, PPH, PPN
            brg_item["barangTarif"] = sorted(brg_item["barangTarif"], key=lambda x: {"BM": 0, "PPH": 1, "PPN": 2}.get(x.get("kodeJenisPungutan"), 99))

            # BARANG DOKUMEN
            brg_item["barangDokumen"] = get_child_data(brg_doc, "barang_dokumen", {
                "seriDokumen": "seri_dokumen",
            })

            barang_list.append(brg_item)

        payload["barang"] = barang_list
        payload["netto"] = round_decimal(total_netto, 4)
        
        # Clean up fields that CEISA rejects if null
        if payload.get("tanggalBc11") is None:
            payload.pop("tanggalBc11", None)

        return payload

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get CEISA BC23 JSON Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist(allow_guest=True)
def get_ceisa_bc25_json(nomor_aju):
    """Export HEADER V21 to BC25 (TPB Internal Transfer) JSON format"""
    try:
        doc = frappe.get_doc("HEADER V21", nomor_aju)
        
        # 1. Map Header Fields
        payload = {
            "asalData": "S",
            "bruto": round_decimal(doc.get("bruto"), 4),
            "cif": round_decimal(doc.get("cif"), 2),
            "dasarPengenaanPajak": round_decimal(doc.get("dasar_pengenaan_pajak"), 2),
            "disclaimer": doc.get("disclaimer") or "1",
            "kodeJenisTpb": doc.get("kode_jenis_tpb") or "",
            "hargaPenyerahan": round_decimal(doc.get("harga_penyerahan"), 4),
            "idPengguna": "",
            "jabatanTtd": doc.get("jabatan_pernyataan") or "",
            "jumlahKontainer": len(doc.get("kontainer") or []),
            "kodeCaraBayar": doc.get("kode_cara_bayar") or "",
            "kodeDokumen": "25",
            "kodeKantor": doc.get("kode_kantor") or "",
            "kodeLokasiBayar": doc.get("kode_lokasi_bayar") or "",
            "kodeTujuanPengiriman": doc.get("kode_tujuan_pengiriman") or "",
            "kodeValuta": doc.get("kode_valuta") or "",
            "kotaTtd": doc.get("kota_pernyataan") or "",
            "namaTtd": doc.get("nama_pernyataan") or "",
            "ndpbm": round_decimal(doc.get("ndpbm"), 4),
            "netto": 0.0,  # Will be calculated from barang
            "nomorAju": doc.get("nomoraju") or doc.name or "",
            "seri": 0,
            "tanggalAju": fmt_date(doc.get("tanggal_pernyataan")),
            "tanggalTtd": fmt_date(doc.get("tanggal_pernyataan")),
            "volume": round_decimal(doc.get("volume"), 4),
            "ppnPajak": round_decimal(doc.get("ppn_pajak"), 2),
            "ppnbmPajak": round_decimal(doc.get("ppnbm_pajak"), 2),
            "tarifPpnPajak": round_decimal(doc.get("tarif_ppn_pajak"), 2),
            "tarifPpnbmPajak": round_decimal(doc.get("tarif_ppnbm_pajak"), 2),
        }

        # 2. Map Entitas (Strict Ordering BC25: 3=Pengusaha TPB, 7=Pemilik, 8=Penerima)
        doc_entitas = doc.get("entitas") or []
        entitas_dict = {}
        for ent in doc_entitas:
            kode = get_kode_entitas(ent.get("kode_entitas"))
            if kode:
                entitas_dict[kode] = ent

        ordered_codes = ["3", "7", "8"]
        remaining_codes = [get_kode_entitas(e.kode_entitas) for e in doc_entitas if get_kode_entitas(e.kode_entitas) not in ordered_codes]
        all_codes_to_process = ordered_codes + remaining_codes

        payload["entitas"] = []
        seri_count = 1
        processed_codes = set()
        
        for kode in all_codes_to_process:
            if kode in processed_codes: continue
            ent = entitas_dict.get(kode)
            if not ent: continue
            
            ent_item = {
                "alamatEntitas": ent.get("alamat_entitas") or "",
                "kodeEntitas": kode,
                "namaEntitas": ent.get("nama_entitas") or "",
                "seriEntitas": seri_count,
            }
            
            if kode in ["3", "7", "8"]:
                ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                ent_item["kodeStatus"] = ent.get("kode_status") or ""
                ent_item["nomorIdentitas"] = ent.get("nomor_identitas") or ""
                
                if kode == "3":
                    ent_item["kodeJenisApi"] = ent.get("kode_jenis_api") or ""
                    ent_item["nibEntitas"] = ent.get("nib_entitas") or ""
                    ent_item["nomorIjinEntitas"] = ent.get("nomor_ijin_entitas") or ""
                    ent_item["tanggalIjinEntitas"] = fmt_date(ent.get("tanggal_ijin_entitas"))
                
                elif kode == "8":
                    ent_item["kodeJenisApi"] = ent.get("kode_jenis_api") or ""
                    ent_item["niperEntitas"] = ent.get("niper_entitas") or ""
            
            else:
                ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                ent_item["nomorIdentitas"] = ent.get("nomor_identitas") or ""

            payload["entitas"].append(ent_item)
            processed_codes.add(kode)
            seri_count += 1

        # 3. Map Kemasan
        payload["kemasan"] = []
        for kem in (doc.get("kemasan") or []):
            payload["kemasan"].append({
                "jumlahKemasan": cint(kem.get("jumlah_kemasan")),
                "kodeJenisKemasan": kem.get("kode_kemasan") or "",
                "merkKemasan": clean_merk_tipe(kem.get("merek_kemasan")),
                "seriKemasan": cint(kem.get("seri")) or 0,
            })

        # 4. Map Kontainer
        payload["kontainer"] = get_child_data(doc, "kontainer", {
            "kodeJenisKontainer": "kode_jenis_kontainer",
            "kodeTipeKontainer": "kode_tipe_kontainer",
            "kodeUkuranKontainer": "kode_ukuran_kontainer",
            "nomorKontainer": "nomor_kontainer",
            "seriKontainer": "seri",
        })

        # 5. Map Dokumen
        payload["dokumen"] = get_child_data(doc, "dokumen", {
            "kodeDokumen": "kode_dokumen",
            "nomorDokumen": "nomor_dokumen",
            "seriDokumen": "seri",
            "tanggalDokumen": "tanggal_dokumen",
            "idDokumen": "id_dokumen",
            "kodeFasilitas": "kode_fasilitas",
            "kodeIjin": "kode_ijin"
        })

        # 6. Map Pengangkut
        payload["pengangkut"] = []
        for peng in (doc.get("pengangkut") or []):
            payload["pengangkut"].append({
                "namaPengangkut": peng.nama_pengangkut or "",
                "nomorPengangkut": peng.nomor_pengangkut or "",
                "kodeCaraAngkut": peng.kode_cara_angkut or "",
                "seriPengangkut": peng.seri_pengangkut or 0,
            })

        # 7. Map Barang V1
        barang_list = []
        barangs = frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc")
        total_netto = 0.0
        for brg in barangs:
            brg_item = {
                "cif": round_decimal(brg.get("cif"), 2),
                "cifRupiah": round_decimal(brg.get("cif_rupiah"), 2),
                "diskon": round_decimal(brg.get("diskon"), 2),
                "fob": round_decimal(brg.get("fob"), 2),
                "freight": round_decimal(brg.get("freight"), 2),
                "hargaEkspor": round_decimal(brg.get("harga_ekspor"), 2),
                "hargaPenyerahan": round_decimal(brg.get("harga_penyerahan"), 4),
                "hargaPerolehan": round_decimal(brg.get("harga_perolehan"), 2),
                "isiPerKemasan": round_decimal(brg.get("isi_per_kemasan"), 2),
                "jumlahKemasan": round_decimal(brg.get("jumlah_kemasan"), 2),
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4),
                "kodeBarang": brg.get("kode_barang") or "",
                "kodeDokumen": "25",
                "kodeDokAsal": brg.get("kode_dokumen_asal") or "",
                "kodeGunaBarang": brg.get("kode_guna_barang") or "",
                "kodeJenisKemasan": brg.get("kode_kemasan") or "",
                "kodeKategoriBarang": brg.get("kode_kategori_barang") or "",
                "kodeKondisiBarang": brg.get("kode_kondisi_barang") or "",
                "kodePerhitungan": brg.get("kode_perhitungan") or "",
                "kodeSatuanBarang": brg.get("kode_satuan") or "",
                "merk": clean_merk_tipe(brg.get("merek")),
                "ndpbm": round_decimal(brg.get("ndpbm"), 4) or 1.0,
                "netto": round_decimal(brg.get("netto"), 4),
                "nilaiBarang": round_decimal(brg.get("nilai_barang"), 2),
                "posTarif": brg.get("hs") or "",
                "seriBarang": cint(brg.get("seri_barang")) or 0,
                "spesifikasiLain": brg.get("spesifikasi_lain") or "",
                "tipe": clean_merk_tipe(brg.get("tipe")),
                "ukuran": brg.get("ukuran") or "",
                "uraian": brg.get("uraian") or "",
                "volume": round_decimal(brg.get("volume"), 4),
            }
            
            brg_doc = frappe.get_doc("BARANG V1", brg.get("name"))
            
            # BARANG TARIF
            brg_item["barangTarif"] = []
            for trf in brg_doc.get("barang_tarif") or []:
                brg_item["barangTarif"].append({
                    "kodeJenisTarif": trf.get("kode_tarif") or "",
                    "jumlahSatuan": round_decimal(trf.get("jumlah_satuan"), 4),
                    "kodeFasilitasTarif": trf.get("kode_fasilitas") or "",
                    "kodeSatuanBarang": trf.get("kode_satuan") or "",
                    "kodeJenisPungutan": get_kode_pungutan(trf.get("kode_pungutan")),
                    "nilaiBayar": round_decimal(trf.get("nilai_bayar"), 2),
                    "nilaiFasilitas": round_decimal(trf.get("nilai_fasilitas"), 2),
                    "nilaiSudahDilunasi": round_decimal(trf.get("nilai_sudah_dilunasi"), 2) or 0,
                    "seriBarang": cint(brg.get("seri_barang")) or 0,
                    "tarif": round_decimal(trf.get("tarif"), 2),
                    "tarifFasilitas": round_decimal(trf.get("tarif_fasilitas"), 2),
                })
            
            # Sort tarif BC25: BM, PPH, PPN
            brg_item["barangTarif"] = sorted(brg_item["barangTarif"], key=lambda x: {"BM": 0, "PPH": 1, "PPN": 2}.get(x.get("kodeJenisPungutan"), 99))

            # BARANG DOKUMEN
            brg_item["barangDokumen"] = get_child_data(brg_doc, "barang_dokumen", {
                "seriDokumen": "seri_dokumen",
            })

            # BAHAN BAKU
            brg_item["bahanBaku"] = []
            bahan_bakus = frappe.get_all("BAHAN BAKU", filters={"parent_barang": brg.get("name")}, fields=["*"], order_by="seri_bahan_baku asc")
            for bb in bahan_bakus:
                bb_doc = frappe.get_doc("BAHAN BAKU", bb.get("name"))
                bb_item = {
                    "cif": round_decimal(bb.get("cif"), 2),
                    "cifRupiah": round_decimal(bb.get("cif_rupiah"), 2),
                    "hargaPenyerahan": round_decimal(bb.get("harga_penyerahan"), 4),
                    "hargaPerolehan": round_decimal(bb.get("harga_perolehan"), 2),
                    "jumlahSatuan": round_decimal(bb.get("jumlah_satuan"), 4),
                    "kodeSatuanBarang": bb.get("kode_satuan") or "",
                    "kodeAsalBahanBaku": bb.get("kode_asal_bahan_baku") or "",
                    "kodeBarang": bb.get("kode_barang") or "",
                    "kodeDokAsal": bb.get("kode_dokumen_asal") or "",
                    "kodeKantor": bb.get("kode_kantor_asal") or "",
                    "merkBarang": bb.get("merek") or "",
                    "ndpbm": round_decimal(bb.get("ndpbm"), 4),
                    "nomorAjuDokAsal": bb.get("nomor_aju_asal") or "",
                    "nomorDaftarDokAsal": bb.get("nomor_daftar_asal") or "",
                    "posTarif": bb.get("hs") or "",
                    "seriBahanBaku": bb.get("seri_bahan_baku") or 0,
                    "seriBarang": brg.get("seri_barang") or 0,
                    "seriBarangDokAsal": bb.get("seri_barang_asal") or 0,
                    "seriIjin": 0,
                    "spesifikasiLainBarang": bb.get("spesifikasi_lain") or "",
                    "tanggalDaftarDokAsal": fmt_date(bb.get("tanggal_daftar_asal")) or "",
                    "tipeBarang": bb.get("tipe") or "",
                    "ukuranBarang": bb.get("ukuran") or "",
                    "uraianBarang": bb.get("uraian") or "",
                }
                
                # BahanBakuDokumen
                bb_item["bahanBakuDokumen"] = []
                for bbd in bb_doc.get("bahan_baku_dokumen") or []:
                    bb_item["bahanBakuDokumen"].append({"seriDokumen": bbd.seri_dokumen or 0})
                
                # BahanBakuTarif
                bb_item["bahanBakuTarif"] = []
                for bbt in bb_doc.get("bahan_tarif") or []:
                    bb_item["bahanBakuTarif"].append({
                        "kodeJenisTarif": bbt.kode_tarif or "",
                        "jumlahSatuan": round_decimal(bbt.jumlah_satuan, 4),
                        "kodeFasilitasTarif": bbt.kode_fasilitas or "",
                        "kodeJenisPungutan": bbt.kode_pungutan or "",
                        "nilaiBayar": round_decimal(bbt.nilai_bayar, 2),
                        "nilaiFasilitas": round_decimal(bbt.nilai_fasilitas, 2),
                        "nilaiSudahDilunasi": cint(bbt.nilai_sudah_dilunasi) or 0,
                        "seriBahanBaku": bb.get("seri_bahan_baku") or 0,
                        "tarif": round_decimal(bbt.tarif, 2),
                        "tarifFasilitas": round_decimal(bbt.tarif_fasilitas, 2),
                    })
                brg_item["bahanBaku"].append(bb_item)

            total_netto += round_decimal(brg.get("netto"), 4)
            barang_list.append(brg_item)

        payload["barang"] = barang_list
        payload["netto"] = round_decimal(total_netto, 4)
        return payload

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get CEISA BC25 JSON Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_ceisa_bc30_json(nomor_aju):
    """Export HEADER V21 to BC30 (Export) JSON format"""
    try:
        doc = frappe.get_doc("HEADER V21", nomor_aju)
        
        # 1. Map Header Fields
        payload = {
            "asalData": "S",
            "asuransi": round_decimal(doc.get("asuransi"), 2),
            "bruto": round_decimal(doc.get("bruto"), 4),
            "cif": round_decimal(doc.get("cif"), 2),
            "disclaimer": doc.get("disclaimer") or "1",
            "flagCurah": doc.get("flag_curah") or "2",
            "flagMigas": doc.get("flag_migas") or "2",
            "fob": round_decimal(doc.get("fob"), 2),
            "freight": round_decimal(doc.get("freight"), 2),
            "idPengguna": "",
            "jabatanTtd": doc.get("jabatan_pernyataan") or "",
            "jumlahKontainer": len(doc.get("kontainer") or []),
            "kesiapanBarang": [],
            "kodeAsuransi": doc.get("kode_asuransi") or "DN",
            "kodeCaraBayar": doc.get("kode_cara_bayar") or "",
            "kodeCaraDagang": doc.get("kode_cara_dagang") or "",
            "kodeDokumen": "30",
            "kodeIncoterm": doc.get("kode_incoterm") or "",
            "kodeJenisProsedur": doc.get("kode_jenis_prosedur") or "",
            "kodeJenisEkspor": doc.get("kode_jenis_ekspor") or "",
            "kodeJenisNilai": doc.get("kode_jenis_nilai") or "",
            "kodeKantor": doc.get("kode_kantor") or "",
            "kodeKantorEkspor": doc.get("kode_kantor_ekspor") or doc.get("kode_kantor") or "",
            "kodeKantorMuat": doc.get("kode_kantor_muat") or "",
            "kodeKantorPeriksa": doc.get("kode_kantor_periksa") or "",
            "kodeKategoriEkspor": doc.get("kode_kategori_export") or doc.get("kode_kategori_ekspor") or "",
            "kodeLokasi": doc.get("kode_lokasi") or "1",
            "kodeNegaraTujuan": doc.get("kode_negara_tujuan") or "",
            "kodePelEkspor": doc.get("kode_pelabuhan_ekspor") or "",
            "kodePelMuat": doc.get("kode_pelabuhan_muat") or "",
            "kodePelTujuan": doc.get("kode_pelabuhan_tujuan") or "",
            "kodePembayar": doc.get("kode_pembayar") or "",
            "kodeTps": doc.get("kode_tps") or "",
            "kodeValuta": doc.get("kode_valuta") or "",
            "kotaTtd": doc.get("kota_pernyataan") or "",
            "namaTtd": doc.get("nama_pernyataan") or "",
            "ndpbm": round_decimal(doc.get("ndpbm"), 4),
            "netto": round_decimal(doc.get("netto"), 4),
            "nilaiMaklon": round_decimal(doc.get("nilai_maklon"), 2),
            "nomorAju": doc.get("nomoraju") or doc.name or "",
            "seri": 0,
            "tanggalAju": fmt_date(doc.get("tanggal_pernyataan")),
            "tanggalEkspor": fmt_date(doc.get("tanggal_ekspor")),
            "tanggalPeriksa": fmt_date(doc.get("tanggal_periksa")),
            "tanggalTtd": fmt_date(doc.get("tanggal_pernyataan")),
            "totalDanaSawit": round_decimal(doc.get("total_dana_sawit"), 2),
            "flagBarkir": doc.get("flag_barkir") or "T",
            "kodeJenisPengangkutan": doc.get("kode_jenis_pengangkutan") or "",
            "bankDevisa": [],
            "kesiapanBarang": []
        }

        # 1.1 Map Bank Devisa
        for bank in (doc.get("bank_devisa") or []):
            payload["bankDevisa"].append({
                "kodeBank": bank.get("kode_bank") or "",
                "namaBank": bank.get("nama_bank") or "",
                "seriBank": cint(bank.get("seri")) or 1,
            })
        if not payload["bankDevisa"]:
            payload["bankDevisa"].append({"kodeBank": "-", "namaBank": "-", "seriBank": 1})

        # 1.2 Map Kesiapan Barang
        for kb in (doc.get("kesiapan_barang") or []):
            payload["kesiapanBarang"].append({
                "kodeJenisBarang": kb.get("kodejenisbarang") or "1",
                "kodeJenisGudang": kb.get("kodejenisgudang") or "1",
                "namaPic": kb.get("namapic") or "-",
                "alamat": kb.get("alamat") or "-",
                "nomorTelpPic": kb.get("nomortelppic") or "-",
                "jumlahContainer20": cint(kb.get("jumlahcontainer20")),
                "jumlahContainer40": cint(kb.get("jumlahcontainer40")),
                "lokasiSiapPeriksa": kb.get("lokasisiapperiksa") or "-",
                "kodeCaraStuffing": kb.get("kodecarastuffing") or "8",
                "kodeJenisPartOf": kb.get("kodejenispartof") or "",
                "tanggalPkb": fmt_date(kb.get("tanggalpkb")),
                "waktuSiapPeriksa": kb.get("waktusiapperiksa").isoformat() if kb.get("waktusiapperiksa") else None
            })
        if not payload["kesiapanBarang"]:
             payload["kesiapanBarang"].append({
                "kodeJenisGudang": "2",
                "namaPic": "-",
                "alamat": "-",
                "nomorTelpPic": "-",
                "lokasiSiapPeriksa": "-",
                "tanggalPkb": fmt_date(doc.get("tanggal_pernyataan")) or frappe.utils.nowdate(),
                "waktuSiapPeriksa": str(fmt_date(doc.get("tanggal_pernyataan")) or frappe.utils.nowdate()) + "T00:00:00.000Z"
            })

        # 2. Map Entitas (Strict Ordering BC30: 2=Eksportir, 7=Pemilik, 8=Penerima)
        # Normalize and map all entities present in the document
        entitas_list = []
        doc_entitas = doc.get("entitas") or []
        
        # Build map with normalized codes
        entitas_dict = {}
        for ent in doc_entitas:
            kode = get_kode_entitas(ent.get("kode_entitas"))
            if kode:
                entitas_dict[kode] = ent

        # Ordered mandatory codes first, then the rest
        ordered_codes = ["2", "7", "8"]
        remaining_codes = [get_kode_entitas(e.kode_entitas) for e in doc_entitas if get_kode_entitas(e.kode_entitas) not in ordered_codes]
        all_codes_to_process = ordered_codes + remaining_codes

        payload["entitas"] = []
        seri_count = 1
        processed_codes = set()
        
        for kode in all_codes_to_process:
            if kode in processed_codes: continue
            ent = entitas_dict.get(kode)
            if not ent: continue
            
            ent_item = {
                "alamatEntitas": ent.get("alamat_entitas") or "",
                "kodeEntitas": kode,
                "namaEntitas": ent.get("nama_entitas") or "",
                "seriEntitas": seri_count,
            }
            
            # Identitas mapping for codes that require it (2, 7, 3, 5, 6 etc)
            if kode in ["2", "7", "3", "5"]:
                ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                ent_item["nomorIdentitas"] = ent.get("nomor_identitas") or ""
                if ent.get("nib_entitas"):
                    ent_item["nibEntitas"] = ent.get("nib_entitas")
            
            #elif kode == "6" :
            #   ent_item["kodeNegara"] = ent.get("kode_negara") or ""
            # Penerima (8) specific
            elif kode == "6" or kode == "8" :
                ent_item["kodeNegara"] = ent.get("kode_negara") or ""
            
            payload["entitas"].append(ent_item)
            processed_codes.add(kode)
            seri_count += 1

        # 3. Map Barang V1
        barang_list = []
        barangs = frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc")
        
        for brg in barangs:
            brg_item = {
                "fob": round_decimal(brg.get("fob"), 2),
                "hargaEkspor": round_decimal(brg.get("harga_ekspor"), 4),
                "hargaPatokan": round_decimal(brg.get("harga_patokan"), 4),
                "hargaPerolehan": round_decimal(brg.get("harga_perolehan"), 2),
                "hargaSatuan": round_decimal(brg.get("harga_satuan"), 2),
                "jumlahKemasan": cint(brg.get("jumlah_kemasan")),  # Must be integer
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4),
                "kodeAsalBahanBaku": brg.get("kode_asal_bahan_baku") or "",
                "kodeBarang": brg.get("kode_barang") or "",
                "kodeDaerahAsal": brg.get("kode_daerah_asal") or "",
                "kodeDokumen": "30",
                "kodeJenisKemasan": brg.get("kode_kemasan") or "",
                "kodeNegaraAsal": (brg.get("kode_negara_asal") or "").upper() or "ID",  # Must be uppercase 2-letter code
                "kodeSatuanBarang": brg.get("kode_satuan") or "",
                "merk": clean_merk_tipe(brg.get("merek")),
                "ndpbm": round_decimal(brg.get("ndpbm"), 4),
                "netto": round_decimal(brg.get("netto"), 4),
                "nilaiBarang": round_decimal(brg.get("nilai_barang"), 2),
                "nilaiDanaSawit": round_decimal(brg.get("nilai_dana_sawit"), 2),
                "posTarif": brg.get("hs") or "",
                "seriBarang": cint(brg.get("seri_barang")) or 0,
                "spesifikasiLain": brg.get("spesifikasi_lain") or "",
                "tipe": clean_merk_tipe(brg.get("tipe")),
                "ukuran": brg.get("ukuran") or "",
                "uraian": brg.get("uraian") or "",
                "kodeJenisEkspor": doc.get("kode_jenis_ekspor") or "",
            }
            
            # Fetch Child Tables for this Barang
            brg_doc = frappe.get_doc("BARANG V1", brg.get("name"))
            
            # BARANG TARIF
            brg_item["barangTarif"] = []
            for trf in brg_doc.get("barang_tarif") or []:
                brg_item["barangTarif"].append({
                    "kodeJenisTarif": trf.get("kode_tarif") or "",
                    "jumlahSatuan": round_decimal(trf.get("jumlah_satuan"), 4),
                    "kodeFasilitasTarif": trf.get("kode_fasilitas") or "",
                    "kodeSatuanBarang": trf.get("kode_satuan") or "",
                    "kodeJenisPungutan": get_kode_pungutan(trf.get("kode_pungutan")),
                    "nilaiBayar": round_decimal(trf.get("nilai_bayar"), 2),
                    "seriBarang": cint(brg.get("seri_barang")) or 0,
                    "tarif": round_decimal(trf.get("tarif"), 4),
                    "tarifFasilitas": round_decimal(trf.get("tarif_fasilitas"), 2),
                })

            # BARANG DOKUMEN
            brg_item["barangDokumen"] = get_child_data(brg_doc, "barang_dokumen", {
                "seriDokumen": "seri_dokumen",
                "seriIjin": "seri_izin",
            })

            # BARANG PEMILIK
            brg_item["barangPemilik"] = []
            # In BC30, this often maps to which owner entitas it belongs to
            # Defaulting to seri first owner if exists
            brg_item["barangPemilik"].append({"seriEntitas": 1})

            barang_list.append(brg_item)

        payload["barang"] = barang_list
        
        # 4. Map Kemasan
        payload["kemasan"] = []
        for kem in (doc.get("kemasan") or []):
            payload["kemasan"].append({
                "jumlahKemasan": cint(kem.get("jumlah_kemasan")),  # Must be integer
                "kodeJenisKemasan": kem.get("kode_kemasan") or "",
                "merkKemasan": clean_merk_tipe(kem.get("merek_kemasan")),
                "seriKemasan": cint(kem.get("seri")) or 0,
            })

        # 5. Map Kontainer
        payload["kontainer"] = get_child_data(doc, "kontainer", {
            "kodeJenisKontainer": "kode_jenis_kontainer",
            "kodeTipeKontainer": "kode_tipe_kontainer",
            "kodeUkuranKontainer": "kode_ukuran_kontainer",
            "nomorKontainer": "nomor_kontainer",
            "seriKontainer": "seri",
        })

        # 6. Map Dokumen
        payload["dokumen"] = get_child_data(doc, "dokumen", {
            "kodeDokumen": "kode_dokumen",
            "nomorDokumen": "nomor_dokumen",
            "seriDokumen": "seri",
            "tanggalDokumen": "tanggal_dokumen",
            "idDokumen": "id_dokumen",
            "kodeFasilitas": "kode_fasilitas",
            "kodeIjin": "kode_ijin"
        })

        # 7. Map Pengangkut
        payload["pengangkut"] = []
        for p in (doc.get("pengangkut") or []):
            payload["pengangkut"].append({
                "kodeBendera": p.get("kode_bendera") or "",
                "kodeCaraAngkut": p.get("kode_cara_angkut") or "1",
                "namaPengangkut": p.get("nama_pengangkut") or "",
                "nomorPengangkut": p.get("nomor_pengangkut") or "",
                "seriPengangkut": cint(p.get("seri_pengangkut") or p.idx)
            })
            
        return payload

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get CEISA BC30 JSON Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_ceisa_bc40_json(nomor_aju):
    """Export HEADER V21 to BC40 (TPB from TLDDP) JSON format"""
    try:
        doc = frappe.get_doc("HEADER V21", nomor_aju)
        payload = {
            "Declaration": {
                "asalData": "S",
                "asuransi": round_decimal(doc.get("asuransi"), 2),
                "bruto": round_decimal(doc.get("bruto"), 4),
                "cif": round_decimal(doc.get("cif"), 2),
                "kodeJenisTpb": doc.get("kode_jenis_tpb") or "",
                "freight": round_decimal(doc.get("freight"), 2),
                "hargaPenyerahan": round_decimal(doc.get("harga_penyerahan"), 4),
                "idPengguna": "",
                "jabatanTtd": doc.get("jabatan_pernyataan") or "",
                "jumlahKontainer": len(doc.get("kontainer") or []),
                "kodeDokumen": "40",
                "kodeKantor": doc.get("kode_kantor") or "",
                "kodeTujuanPengiriman": doc.get("kode_tujuan_pengiriman") or "",
                "kotaTtd": doc.get("kota_pernyataan") or "",
                "namaTtd": doc.get("nama_pernyataan") or "",
                "netto": round_decimal(doc.get("netto"), 4),
                "nik": "",
                "nomorAju": doc.get("nomoraju") or doc.name or "",
                "seri": 0,
                "tanggalAju": fmt_date(doc.get("tanggal_pernyataan")),
                "tanggalTtd": fmt_date(doc.get("tanggal_pernyataan")),
                "userPortal": "",
                "volume": round_decimal(doc.get("volume"), 4),
                "biayaTambahan": round_decimal(doc.get("biaya_tambahan"), 2),
                "biayaPengurang": round_decimal(doc.get("biaya_pengurang"), 2),
                "vd": round_decimal(doc.get("vd"), 4),
                "uangMuka": round_decimal(doc.get("uang_muka"), 4),
                "nilaiJasa": round_decimal(doc.get("nilai_jasa"), 4),
            }
        }
        decl = payload["Declaration"]

        # 2. Map Entitas (Strict Ordering BC40: 3=Pengusaha TPB, 7=Pemilik, 9=Pengirim)
        entitas_map = {ent.kode_entitas: ent for ent in doc.entitas}
        decl["entitas"] = []
        ordered_codes = ["3", "7", "9"]
        
        for idx, kode in enumerate(ordered_codes):
            ent = entitas_map.get(kode)
            if ent:
                ent_item = {
                    "alamatEntitas": ent.get("alamat_entitas") or "",
                    "kodeEntitas": kode,
                    "namaEntitas": ent.get("nama_entitas") or "",
                    "seriEntitas": idx + 1,
                }
                
                # Specific fields per entity type
                if kode == "3":  # Pengusaha TPB
                    ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                    ent_item["nibEntitas"] = ent.get("nib_entitas") or ""
                    ent_item["nomorIdentitas"] = ent.get("nomor_identitas") or ""
                    ent_item["nomorIjinEntitas"] = ent.get("nomor_ijin_entitas") or "-"
                    ent_item["tanggalIjinEntitas"] = fmt_date(ent.get("tanggal_ijin_entitas")) or fmt_date(doc.get("tanggal_pernyataan")) or frappe.utils.nowdate()
                
                elif kode in ["7", "9"]:  # Pemilik / Pengirim
                    ent_item["kodeJenisApi"] = ent.get("kode_jenis_api") or "01"
                    ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                    ent_item["kodeStatus"] = ent.get("kode_status") or "10"
                    ent_item["nibEntitas"] = ent.get("nib_entitas") or ""
                    ent_item["nomorIdentitas"] = ent.get("nomor_identitas") or ""
                
                decl["entitas"].append(ent_item)

        # 3. Map Child Tables
        decl["dokumen"] = get_child_data(doc, "dokumen", {
            "kodeDokumen": "kode_dokumen",
            "nomorDokumen": "nomor_dokumen",
            "seriDokumen": "seri",
            "tanggalDokumen": "tanggal_dokumen"
        })
        
        decl["pengangkut"] = get_child_data(doc, "pengangkut", {
            "namaPengangkut": "nama_pengangkut",
            "nomorPengangkut": "nomor_pengangkut",
            "seriPengangkut": "seri_pengangkut"
        })
        
        decl["kontainer"] = get_child_data(doc, "kontainer", {
            "kodeJenisKontainer": "kode_jenis_kontainer",
            "kodeTipeKontainer": "kode_tipe_kontainer",
            "kodeUkuranKontainer": "kode_ukuran_kontainer",
            "nomorKontainer": "nomor_kontainer",
            "seriKontainer": "seri"
        })
        
        decl["kemasan"] = []
        for kem in (doc.get("kemasan") or []):
            decl["kemasan"].append({
                "jumlahKemasan": cint(kem.get("jumlah_kemasan")),  # Must be integer
                "kodeJenisKemasan": kem.get("kode_kemasan") or "",
                "merkKemasan": clean_merk_tipe(kem.get("merek_kemasan")),
                "seriKemasan": cint(kem.get("seri")) or 0
            })
            
        decl["pungutan"] = []
        for pung in (doc.get("pungutan") or []):
            decl["pungutan"].append({
                "kodeFasilitasTarif": pung.get("kode_fasilitas_tarif") or "",
                "kodeJenisPungutan": get_kode_pungutan(pung.get("kode_jenis_pungutan")),
                "nilaiPungutan": round_decimal(pung.get("nilai_pungutan"), 2)
            })

        # 4. Map Barang
        decl["barang"] = []
        for brg in frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc"):
            brg_doc = frappe.get_doc("BARANG V1", brg.get("name"))
            brg_item = {
                "asuransi": round_decimal(brg.get("asuransi"), 2),
                "bruto": round_decimal(brg.get("bruto"), 4),
                "cif": round_decimal(brg.get("cif"), 2),
                "diskon": round_decimal(brg.get("diskon"), 2),
                "hargaEkspor": round_decimal(brg.get("harga_ekspor"), 4),
                "hargaPenyerahan": round_decimal(brg.get("harga_penyerahan"), 4),
                "hargaSatuan": round_decimal(brg.get("harga_satuan"), 4),
                "isiPerKemasan": round_decimal(brg.get("isi_per_kemasan"), 2),
                "jumlahKemasan": round_decimal(brg.get("jumlah_kemasan"), 2),
                "jumlahRealisasi": round_decimal(brg.get("jumlah_realisasi"), 4),
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4),
                "kodeBarang": brg.get("kode_barang") or "",
                "kodeDokumen": "40",
                "kodeJenisKemasan": brg.get("kode_kemasan") or "",
                "kodeSatuanBarang": brg.get("kode_satuan") or "",
                "merk": clean_merk_tipe(brg.get("merek")),
                "netto": round_decimal(brg.get("netto"), 4),
                "nilaiBarang": round_decimal(brg.get("nilai_barang"), 2),
                "posTarif": brg.get("hs") or "",
                "seriBarang": cint(brg.get("seri_barang")) or 0,
                "spesifikasiLain": brg.get("spesifikasi_lain") or "",
                "tipe": clean_merk_tipe(brg.get("tipe")),
                "ukuran": brg.get("ukuran") or "",
                "uraian": brg.get("uraian") or "",
                "volume": round_decimal(brg.get("volume"), 4),
                "cifRupiah": round_decimal(brg.get("cif_rupiah"), 2),
                "hargaPerolehan": round_decimal(brg.get("harga_perolehan"), 2),
                "kodeAsalBahanBaku": brg.get("kode_asal_bahan_baku") if brg.get("kode_asal_bahan_baku") in ["0", "1"] else "1",
                "ndpbm": round_decimal(brg.get("ndpbm"), 4),
                "nilaiJasa": round_decimal(brg.get("nilai_jasa"), 4),
                "uangMuka": round_decimal(brg.get("uang_muka"), 4),
            }
            
            # BARANG TARIF
            brg_item["barangTarif"] = []
            for t in brg_doc.get("barang_tarif") or []:
                brg_item["barangTarif"].append({
                    "kodeJenisTarif": t.get("kode_tarif") or "1",
                    "jumlahSatuan": round_decimal(t.get("jumlah_satuan"), 4),
                    "kodeFasilitasTarif": t.get("kode_fasilitas") or "3",
                    "kodeSatuanBarang": t.get("kode_satuan") or "",
                    "nilaiBayar": round_decimal(t.get("nilai_bayar"), 2),
                    "nilaiFasilitas": round_decimal(t.get("nilai_fasilitas"), 2),
                    "nilaiSudahDilunasi": round_decimal(t.get("nilai_sudah_dilunasi"), 2) or 0,
                    "seriBarang": cint(brg.get("seri_barang")) or 0,
                    "tarif": round_decimal(t.get("tarif"), 2),
                    "tarifFasilitas": round_decimal(t.get("tarif_fasilitas"), 2),
                    "kodeJenisPungutan": get_kode_pungutan(t.get("kode_pungutan"))
                })
            
            decl["barang"].append(brg_item)

        return payload
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get CEISA BC40 JSON Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_ceisa_bc41_json(nomor_aju):
    """Export HEADER V21 to BC41 (TPB release to TLDDP) JSON format"""
    try:
        doc = frappe.get_doc("HEADER V21", nomor_aju)
        
        # 1. Map Header
        payload = {
            "Declaration": {
                "asalData": "S",
                "asuransi": round_decimal(doc.get("asuransi"), 2),
                "bruto": round_decimal(doc.get("bruto"), 4),
                "cif": round_decimal(doc.get("cif"), 2),
                "kodeJenisTpb": doc.get("kode_jenis_tpb") or "1",
                "freight": round_decimal(doc.get("freight"), 2),
                "hargaPenyerahan": round_decimal(doc.get("harga_penyerahan"), 4),
                "jabatanTtd": doc.get("jabatan_pernyataan") or "",
                "jumlahKontainer": len(doc.get("kontainer") or []),
                "kodeDokumen": "41",
                "kodeKantor": doc.get("kode_kantor") or "",
                "kodeLokasiBayar": doc.get("kode_lokasi_bayar") or "0000",
                "kodePembayar": doc.get("kode_pembayar") or "1",
                "kodeTujuanPengiriman": doc.get("kode_tujuan_pengiriman") or "",
                "kotaTtd": doc.get("kota_pernyataan") or "",
                "namaTtd": doc.get("nama_pernyataan") or "",
                "netto": round_decimal(doc.get("netto"), 4),
                "nilaiBarang": round_decimal(doc.get("nilai_barang"), 2),
                "nomorAju": doc.get("nomoraju") or doc.name or "",
                "seri": 0,
                "tanggalAju": fmt_date(doc.get("tanggal_pernyataan")),
                "tanggalTtd": fmt_date(doc.get("tanggal_pernyataan")),
                "userPortal": "",
                "volume": round_decimal(doc.get("volume"), 4),
                "biayaTambahan": round_decimal(doc.get("biaya_tambahan"), 2),
                "biayaPengurang": round_decimal(doc.get("biaya_pengurang"), 2),
                "vd": round_decimal(doc.get("vd"), 4),
                "uangMuka": round_decimal(doc.get("uang_muka"), 4),
                "ppnPajak": round_decimal(doc.get("ppn_pajak"), 2),
                "ppnbmPajak": round_decimal(doc.get("ppnbm_pajak"), 2),
                "pphPajak": round_decimal(doc.get("pph_pajak"), 2),
                "totalDanaSawit": 0,
            }
        }
        decl = payload["Declaration"]

        # 2. Map Entitas (Strict Ordering BC41: 3, 7, 8)
        entitas_map = {ent.kode_entitas: ent for ent in doc.entitas}
        decl["entitas"] = []
        ordered_codes = ["3", "7", "8"]
        
        for idx, kode in enumerate(ordered_codes):
            ent = entitas_map.get(kode)
            if ent:
                ent_item = {
                    "alamatEntitas": ent.get("alamat_entitas") or "",
                    "kodeEntitas": kode,
                    "namaEntitas": ent.get("nama_entitas") or "",
                    "seriEntitas": idx + 1,
                    "nomorIdentitas": ent.get("nomor_identitas") or "",
                }
                if kode == "3":
                    ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                    ent_item["nibEntitas"] = ent.get("nib_entitas") or ""
                    ent_item["nomorIjinEntitas"] = ent.get("nomor_ijin_entitas") or "-"
                    ent_item["tanggalIjinEntitas"] = fmt_date(ent.get("tanggal_ijin_entitas")) or fmt_date(doc.get("tanggal_pernyataan")) or frappe.utils.nowdate()
                elif kode == "7":
                    ent_item["kodeJenisApi"] = ent.get("kode_jenis_api") or "01"
                    ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                    ent_item["kodeStatus"] = ent.get("kode_status") or "10"
                    ent_item["nomorIjinEntitas"] = ent.get("nomor_ijin_entitas") or "-"
                    ent_item["tanggalIjinEntitas"] = fmt_date(ent.get("tanggal_ijin_entitas")) or fmt_date(doc.get("tanggal_pernyataan")) or frappe.utils.nowdate()
                elif kode == "8":
                    ent_item["kodeJenisApi"] = ent.get("kode_jenis_api") or "01"
                    ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                    ent_item["kodeStatus"] = ent.get("kode_status") or "10"
                
                decl["entitas"].append(ent_item)

        # 3. Child Tables
        decl["dokumen"] = get_child_data(doc, "dokumen", {
            "kodeDokumen": "kode_dokumen",
            "nomorDokumen": "nomor_dokumen",
            "seriDokumen": "seri",
            "tanggalDokumen": "tanggal_dokumen"
        })
        
        decl["pengangkut"] = []
        for p in (doc.get("pengangkut") or []):
            decl["pengangkut"].append({
                "namaPengangkut": p.get("nama_pengangkut") or "",
                "nomorPengangkut": p.get("nomor_pengangkut") or "",
                "kodeCaraAngkut": p.get("kode_cara_angkut") or "1",
                "seriPengangkut": str(p.get("seri_pengangkut") or p.idx)
            })
            
        decl["kemasan"] = []
        for kem in (doc.get("kemasan") or []):
            decl["kemasan"].append({
                "jumlahKemasan": cint(kem.get("jumlah_kemasan")),
                "kodeJenisKemasan": kem.get("kode_kemasan") or "",
                "merkKemasan": clean_merk_tipe(kem.get("merek_kemasan")),
                "seriKemasan": cint(kem.get("seri") or kem.idx)
            })

        # 4. Map Barang
        decl["barang"] = []
        for brg in frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc"):
            brg_doc = frappe.get_doc("BARANG V1", brg.get("name"))
            brg_item = {
                "cif": round_decimal(brg.get("cif"), 2),
                "hargaEkspor": round_decimal(brg.get("harga_ekspor"), 4),
                "hargaPenyerahan": round_decimal(brg.get("harga_penyerahan"), 4),
                "isiPerKemasan": round_decimal(brg.get("isi_per_kemasan"), 2),
                "jumlahKemasan": cint(brg.get("jumlah_kemasan")),
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4),
                "kodeBarang": brg.get("kode_barang") or "",
                "kodeDokumen": "41",
                "kodeJenisKemasan": brg.get("kode_kemasan") or "",
                "kodeSatuanBarang": brg.get("kode_satuan") or "",
                "merk": clean_merk_tipe(brg.get("merek")),
                "netto": round_decimal(brg.get("netto"), 4),
                "nilaiBarang": round_decimal(brg.get("nilai_barang"), 2),
                "posTarif": brg.get("hs") or "",
                "seriBarang": cint(brg.get("seri_barang")) or 0,
                "spesifikasiLain": brg.get("spesifikasi_lain") or "",
                "tipe": clean_merk_tipe(brg.get("tipe")),
                "ukuran": brg.get("ukuran") or "",
                "uraian": brg.get("uraian") or "",
                "volume": round_decimal(brg.get("volume"), 4),
                "cifRupiah": round_decimal(brg.get("cif_rupiah"), 2),
                "hargaPerolehan": round_decimal(brg.get("harga_perolehan"), 2),
                "kodeAsalBahanBaku": brg.get("kode_asal_bahan_baku") if brg.get("kode_asal_bahan_baku") in ["0", "1"] else "1",
                "ndpbm": round_decimal(brg.get("ndpbm"), 4) or 1.0,
            }
            
            # BC41 requires bahanBaku
            brg_item["bahanBaku"] = []
            bahan_bakus = frappe.get_all("BAHAN BAKU", filters={"parent_barang": brg.get("name")}, fields=["*"], order_by="seri_bahan_baku asc")
            for bb in bahan_bakus:
                bb_doc = frappe.get_doc("BAHAN BAKU", bb.get("name"))
                bb_item = {
                    "cif": round_decimal(bb.get("cif"), 2),
                    "cifRupiah": round_decimal(bb.get("cif_rupiah"), 2),
                    "hargaPenyerahan": round_decimal(bb.get("harga_penyerahan"), 4),
                    "hargaPerolehan": round_decimal(bb.get("harga_perolehan"), 2),
                    "jumlahSatuan": round_decimal(bb.get("jumlah_satuan"), 4),
                    "kodeSatuanBarang": bb.get("kode_satuan") or "",
                    "kodeAsalBahanBaku": bb.get("kode_asal_bahan_baku") or "0",
                    "kodeBarang": bb.get("kode_barang") or "",
                    "kodeDokAsal": bb.get("kode_dokumen_asal") or "40",
                    "kodeDokumen": "41",
                    "kodeKantor": bb.get("kode_kantor_asal") or doc.get("kode_kantor") or "",
                    "ndpbm": round_decimal(bb.get("ndpbm"), 4) or 1.0,
                    "netto": round_decimal(bb.get("netto"), 4),
                    "nomorAjuDokAsal": bb.get("nomor_aju_asal") or "",
                    "nomorDaftarDokAsal": bb.get("nomor_daftar_asal") or "",
                    "posTarif": bb.get("hs") or "",
                    "seriBahanBaku": cint(bb.get("seri_bahan_baku")) or 0,
                    "seriBarang": cint(brg.get("seri_barang")) or 0,
                    "seriBarangDokAsal": cint(bb.get("seri_barang_asal")) or 0,
                    "seriIjin": 0,
                    "tanggalDaftarDokAsal": fmt_date(bb.get("tanggal_daftar_asal")) or fmt_date(doc.get("tanggal_pernyataan")) or frappe.utils.nowdate(),
                    "tipeBarang": clean_merk_tipe(bb.get("tipe")),
                    "ukuranBarang": bb.get("ukuran") or "",
                    "uraianBarang": bb.get("uraian") or "",
                    "nilaiJasa": 0,
                    "merkBarang": clean_merk_tipe(bb.get("merek")),
                }
                brg_item["bahanBaku"].append(bb_item)
            
            decl["barang"].append(brg_item)

        return payload
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get CEISA BC41 JSON Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_ceisa_bc33_json(nomor_aju):
    """Export HEADER V21 to BC33 (PLB) JSON format"""
    try:
        doc = frappe.get_doc("HEADER V21", nomor_aju)
        
        # 1. Map Header
        payload = {
            "Declaration": {
                "asalData": "S",
                "asuransi": round_decimal(doc.get("asuransi"), 2),
                "bruto": round_decimal(doc.get("bruto"), 4),
                "cif": round_decimal(doc.get("cif"), 2),
                "freight": round_decimal(doc.get("freight"), 2),
                "jabatanTtd": doc.get("jabatan_pernyataan") or "",
                "jumlahKontainer": len(doc.get("kontainer") or []),
                "kodeDokumen": "33",
                "kodeKantor": doc.get("kode_kantor") or "",
                "kotaTtd": doc.get("kota_pernyataan") or "",
                "namaTtd": doc.get("nama_pernyataan") or "",
                "netto": round_decimal(doc.get("netto"), 4),
                "nomorAju": doc.get("nomoraju") or doc.name or "",
                "seri": 1,
                "tanggalAju": fmt_date(doc.get("tanggal_pernyataan")) or frappe.utils.nowdate(),
                "tanggalTtd": fmt_date(doc.get("tanggal_pernyataan")) or frappe.utils.nowdate(),
                "volume": round_decimal(doc.get("volume"), 4),
                "flagCurah": str(doc.get("flag_curah") or "2"),
                "kodeCaraAngkutPlb": str(doc.get("kode_cara_angkut") or "1"),
                "kodeCaraBayar": str(doc.get("kode_cara_bayar") or "1"),
                "kodeCaraDagang": doc.get("kode_cara_dagang") or "1",
                "kodeJenisEkspor": doc.get("kode_jenis_ekspor") or "1",
                "kodeJenisProsedur": doc.get("kode_jenis_prosedur") or "1",
                "kodeKategoriEkspor": doc.get("kode_kategori_ekspor") or "1",
                "kodePelBongkar": doc.get("kode_pelabuhan_bongkar") or "",
                "kodePelMuat": doc.get("kode_pelabuhan_muat") or "",
                "kodePelTujuan": doc.get("kode_pelabuhan_tujuan") or "",
                "kodeValuta": doc.get("kode_valuta") or "USD",
                "ndpbm": round_decimal(doc.get("ndpbm"), 4) or 1.0,
                "kodeAsuransi": doc.get("kode_asuransi") or "1",
            }
        }
        decl = payload["Declaration"]

        # 2. Bank Devisa (Required for BC33)
        decl["bankDevisa"] = []
        for i, bank in enumerate(doc.get("bank_devisa") or []):
            decl["bankDevisa"].append({
                "kodeBank": bank.get("kode_bank") or "",
                "namaBank": bank.get("nama_bank") or "",
                "seriBank": i + 1
            })
        if not decl["bankDevisa"]:
            decl["bankDevisa"].append({"kodeBank": "-", "namaBank": "-", "seriBank": 1})

        # 3. Map Entitas (Strict Ordering BC33: 2=Eksportir, 3=Pengusaha, 7=Pemilik, 8=Penerima)
        entitas_map = {ent.kode_entitas: ent for ent in doc.entitas}
        decl["entitas"] = []
        # Mapping logic for mandatory slots if original codes missing
        e2 = entitas_map.get("2") or entitas_map.get("3") # Use Pengusaha if Eksportir missing
        e3 = entitas_map.get("3") or entitas_map.get("2")
        e7 = entitas_map.get("7") or e3
        e8 = entitas_map.get("8") or entitas_map.get("4") or e7 # Use Pembeli or Pemilik if Penerima missing
        
        ordered_ents = [("2", e2), ("3", e3), ("7", e7), ("8", e8)]
        
        for idx, (target_kode, ent) in enumerate(ordered_ents):
            if ent:
                ent_item = {
                    "alamatEntitas": ent.get("alamat_entitas") or "",
                    "kodeEntitas": target_kode,
                    "namaEntitas": ent.get("nama_entitas") or "",
                    "seriEntitas": idx + 1,
                    "nomorIdentitas": ent.get("nomor_identitas") or "",
                }
                if target_kode == "2": # Eksportir
                     ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                     ent_item["kodeStatus"] = ent.get("kode_status") or "10"
                elif target_kode == "3": # Pengusaha 
                    ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                    ent_item["nomorIjinEntitas"] = ent.get("nomor_ijin_entitas") or "-"
                elif target_kode in ["7", "8"]: # Pemilik / Penerima
                    ent_item["nomorIdentitas"] = ent.get("nomor_identitas") or ""
                
                decl["entitas"].append(ent_item)

        # 4. Child Tables
        decl["dokumen"] = get_child_data(doc, "dokumen", {
            "kodeDokumen": "kode_dokumen",
            "nomorDokumen": "nomor_dokumen",
            "seriDokumen": "seri",
            "tanggalDokumen": "tanggal_dokumen"
        })
        
        decl["pengangkut"] = []
        for p in (doc.get("pengangkut") or []):
            decl["pengangkut"].append({
                "namaPengangkut": p.get("nama_pengangkut") or "",
                "nomorPengangkut": p.get("nomor_pengangkut") or "",
                "kodeCaraAngkut": p.get("kode_cara_angkut") or "1",
                "seriPengangkut": str(p.get("seri_pengangkut") or p.idx)
            })
            
        decl["kemasan"] = []
        for kem in (doc.get("kemasan") or []):
            decl["kemasan"].append({
                "jumlahKemasan": cint(kem.get("jumlah_kemasan")),
                "kodeJenisKemasan": kem.get("kode_kemasan") or "",
                "merkKemasan": clean_merk_tipe(kem.get("merek_kemasan")),
                "seriKemasan": cint(kem.get("seri") or kem.idx)
            })

        # 5. Map Barang
        decl["barang"] = []
        for brg in frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc"):
            brg_item = {
                "cif": round_decimal(brg.get("cif"), 2),
                "fob": round_decimal(brg.get("fob") or brg.get("nilai_barang"), 2),
                "hargaEkspor": round_decimal(brg.get("harga_ekspor"), 4),
                "hargaPenyerahan": round_decimal(brg.get("harga_penyerahan"), 4),
                "isiPerKemasan": round_decimal(brg.get("isi_per_kemasan"), 2),
                "jumlahKemasan": cint(brg.get("jumlah_kemasan")),
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4),
                "kodeBarang": brg.get("kode_barang") or "",
                "kodeDokumen": "33",
                "kodeJenisKemasan": brg.get("kode_kemasan") or "",
                "kodeSatuanBarang": brg.get("kode_satuan") or "",
                "merk": clean_merk_tipe(brg.get("merek")),
                "netto": round_decimal(brg.get("netto"), 4),
                "nilaiBarang": round_decimal(brg.get("nilai_barang"), 2),
                "posTarif": brg.get("hs") or "",
                "seriBarang": cint(brg.get("seri_barang")) or 0,
                "spesifikasiLain": brg.get("spesifikasi_lain") or "",
                "tipe": clean_merk_tipe(brg.get("tipe")),
                "ukuran": brg.get("ukuran") or "",
                "uraian": brg.get("uraian") or "",
                "volume": round_decimal(brg.get("volume"), 4),
            }
            decl["barang"].append(brg_item)

        return payload
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get CEISA BC33 JSON Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
@frappe.whitelist()
def get_ceisa_bc262_json(nomor_aju):
    """Export HEADER V21 to BC262 (Pemasukan dari TPB Lain) JSON format"""
    try:
        doc = frappe.get_doc("HEADER V21", nomor_aju)
        
        # 1. Map Header
        payload = {
            "asalData": "S",
            "asuransi": round_decimal(doc.get("asuransi"), 2),
            "biayaPengurang": round_decimal(doc.get("biaya_pengurang"), 2),
            "biayaTambahan": round_decimal(doc.get("biaya_tambahan"), 2),
            "bruto": round_decimal(doc.get("bruto"), 4),
            "cif": round_decimal(doc.get("cif"), 2),
            "disclaimer": doc.get("disclaimer") or "1",
            "freight": round_decimal(doc.get("freight"), 2),
            "hargaPenyerahan": round_decimal(doc.get("harga_penyerahan"), 4),
            "jabatanTtd": doc.get("jabatan_pernyataan") or "",
            "kodeDokumen": "262",
            "kodeKantor": doc.get("kode_kantor") or "",
            "kodeTujuanPemasukan": doc.get("kode_tujuan_pemasukan") or doc.get("kode_tujuan_pengiriman") or "",
            "kodeValuta": doc.get("kode_valuta") or "",
            "kotaTtd": doc.get("kota_pernyataan") or "",
            "namaTtd": doc.get("nama_pernyataan") or "",
            "ndpbm": round_decimal(doc.get("ndpbm"), 4) or 1.0,
            "netto": 0.0,  # Will be calculated from barang
            "nik": "",
            "nilaiBarang": round_decimal(doc.get("nilai_barang"), 2),
            "nomorAju": doc.get("nomoraju") or doc.name or "",
            "seri": 1,
            "tanggalAju": fmt_date(doc.get("tanggal_pernyataan")),
            "tanggalTtd": fmt_date(doc.get("tanggal_pernyataan")),
            "uangMuka": round_decimal(doc.get("uang_muka"), 2),
            "vd": round_decimal(doc.get("vd"), 2),
        }

        # 2. Map Entitas (Strict Ordering BC262: 3=Pengusaha TPB, 7=Pemilik, 9=Pengirim)
        entitas_map = {ent.kode_entitas: ent for ent in doc.entitas}
        payload["entitas"] = []
        ordered_codes = ["3", "7", "9"]
        
        for idx, kode in enumerate(ordered_codes):
            ent = entitas_map.get(kode)
            if ent:
                ent_item = {
                    "alamatEntitas": ent.get("alamat_entitas") or "",
                    "kodeEntitas": kode,
                    "namaEntitas": ent.get("nama_entitas") or "",
                    "seriEntitas": idx + 1,
                    "nomorIdentitas": ent.get("nomor_identitas") or "",
                }
                
                # Specific fields per entity type based on Schema
                if kode == "3": # Pengusaha TPB
                    ent_item["kodeJenisApi"] = ent.get("kode_jenis_api") or "01"
                    ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                    ent_item["kodeStatus"] = ent.get("kode_status") or "10"
                    ent_item["nibEntitas"] = ent.get("nib_entitas") or ""
                    ent_item["nomorIjinEntitas"] = ent.get("nomor_ijin_entitas") or "-"
                    ent_item["tanggalIjinEntitas"] = fmt_date(ent.get("tanggal_ijin_entitas")) or fmt_date(doc.get("tanggal_pernyataan")) or frappe.utils.nowdate()
                
                elif kode == "7": # Pemilik
                    ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                    ent_item["kodeStatus"] = ent.get("kode_status") or "10"
                
                elif kode == "9": # Pengirim
                    ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                    ent_item["kodeStatus"] = ent.get("kode_status") or "10"

                payload["entitas"].append(ent_item)

        # 3. Map Dokumen
        payload["dokumen"] = get_child_data(doc, "dokumen", {
            "idDokumen": "",
            "kodeDokumen": "kode_dokumen",
            "kodeFasilitas": "kode_fasilitas",
            "nomorDokumen": "nomor_dokumen",
            "seriDokumen": "seri",
            "tanggalDokumen": "tanggal_dokumen"
        })

        # 4. Map Pengangkut
        payload["pengangkut"] = []
        for p in (doc.get("pengangkut") or []):
             payload["pengangkut"].append({
                "idPengangkut": "",
                "kodeCaraAngkut": p.get("kode_cara_angkut") or "1",
                "seriPengangkut": cint(p.get("seri_pengangkut") or (p.idx))
             })

        # 5. Map Kemasan
        payload["kemasan"] = []
        for kem in (doc.get("kemasan") or []):
            payload["kemasan"].append({
                "jumlahKemasan": round_decimal(kem.get("jumlah_kemasan"), 2),
                "kodeJenisKemasan": kem.get("kode_kemasan") or "",
                "merkKemasan": clean_merk_tipe(kem.get("merek_kemasan")),
                "seriKemasan": cint(kem.get("seri")) or 0,
            })

        # 6. Map Kontainer
        payload["kontainer"] = get_child_data(doc, "kontainer", {
            "kodeJenisKontainer": "kode_jenis_kontainer",
            "kodeTipeKontainer": "kode_tipe_kontainer",
            "kodeUkuranKontainer": "kode_ukuran_kontainer",
            "nomorKontainer": "nomor_kontainer",
            "seriKontainer": "seri",
        })

        # 7. Map Pungutan
        payload["pungutan"] = []
        for pung in (doc.get("pungutan") or []):
            payload["pungutan"].append({
                "idPungutan": "",
                "kodeFasilitasTarif": pung.kode_fasilitas_tarif or "1",
                "kodeJenisPungutan": get_kode_pungutan(pung.kode_jenis_pungutan),
                "nilaiPungutan": round_decimal(pung.nilai_pungutan, 2),
            })
        
        # 8. Map Jaminan
        payload["jaminan"] = []
        for jam in (doc.get("jaminan") or []):
             payload["jaminan"].append({
                "idJaminan": "",
                "kodeJenisJaminan": jam.get("kode_jenis_jaminan") or "",
                "nilaiJaminan": round_decimal(jam.get("nilai_jaminan"), 2),
                "nomorBpj": jam.get("nomor_bpj") or "",
                "nomorJaminan": jam.get("nomor_jaminan") or "",
                "penjamin": jam.get("penjamin") or "",
                "tanggalBpj": fmt_date(jam.get("tanggal_bpj")),
                "tanggalJaminan": fmt_date(jam.get("tanggal_jaminan")),
                "tanggalJatuhTempo": fmt_date(jam.get("tanggal_jatuh_tempo")),
             })

        # 9. Map Barang
        barang_list = []
        barangs = frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc")
        
        for brg in barangs:
            brg_item = {
                "cif": round_decimal(brg.get("cif"), 2),
                "cifRupiah": round_decimal(brg.get("cif_rupiah"), 2),
                "hargaEkspor": round_decimal(brg.get("harga_ekspor"), 2),
                "hargaPenyerahan": round_decimal(brg.get("harga_penyerahan"), 4),
                "hargaPerolehan": round_decimal(brg.get("harga_perolehan"), 2),
                "isiPerKemasan": round_decimal(brg.get("isi_per_kemasan"), 2),
                "jumlahKemasan": round_decimal(brg.get("jumlah_kemasan"), 2),
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4),
                "kodeAsalBahanBaku": brg.get("kode_asal_bahan_baku") or "1",
                "kodeAsalBarang": brg.get("kode_daerah_asal") or "1",
                "kodeBarang": brg.get("kode_barang") or "",
                "kodeDokumen": "262",
                "kodeJenisKemasan": brg.get("kode_kemasan") or "",
                "kodeNegaraAsal": brg.get("kode_negara_asal") or "ID",
                "kodeSatuanBarang": brg.get("kode_satuan") or "",
                "merk": clean_merk_tipe(brg.get("merek")),
                "ndpbm": round_decimal(brg.get("ndpbm"), 4) or 1.0,
                "netto": round_decimal(brg.get("netto"), 4),
                "nilaiBarang": round_decimal(brg.get("nilai_barang"), 2),
                "nilaiJasa": round_decimal(brg.get("nilai_jasa"), 2),
                "posTarif": brg.get("hs") or "",
                "seriBarang": cint(brg.get("seri_barang")) or 0,
                "spesifikasiLain": brg.get("spesifikasi_lain") or "",
                "tipe": clean_merk_tipe(brg.get("tipe")),
                "uangMuka": 0,
                "ukuran": brg.get("ukuran") or "",
                "uraian": brg.get("uraian") or "",
            }

            # BAHAN BAKU 
            brg_item["bahanBaku"] = []
            bahan_bakus = frappe.get_all("BAHAN BAKU", filters={"parent_barang": brg.get("name")}, fields=["*"], order_by="seri_bahan_baku asc")
            for bb in bahan_bakus:
                bb_doc = frappe.get_doc("BAHAN BAKU", bb.get("name"))
                bb_item = {
                    "cif": round_decimal(bb.get("cif"), 2),
                    "cifRupiah": round_decimal(bb.get("cif_rupiah"), 2),
                    "hargaPenyerahan": round_decimal(bb.get("harga_penyerahan"), 4),
                    "hargaPerolehan": round_decimal(bb.get("harga_perolehan"), 2),
                    "jumlahSatuan": round_decimal(bb.get("jumlah_satuan"), 4),
                    "kodeAsalBahanBaku": bb.get("kode_asal_bahan_baku") or "0",
                    "kodeBarang": bb.get("kode_barang") or "",
                    "kodeDokAsal": bb.get("kode_dokumen_asal") or "40",
                    "kodeDokumen": bb.get("kode_dokumen_asal") or "261",
                    "kodeKantor": bb.get("kode_kantor_asal") or doc.get("kode_kantor") or "",
                    "kodeSatuanBarang": bb.get("kode_satuan") or "",
                    "merkBarang": clean_merk_tipe(bb.get("merek")),
                    "ndpbm": round_decimal(bb.get("ndpbm"), 4) or 1.0,
                    "netto": round_decimal(bb.get("netto"), 4),
                    "nilaiJasa": 0,
                    "nomorAjuDokAsal": bb.get("nomor_aju_asal") or "",
                    "nomorDaftarDokAsal": bb.get("nomor_daftar_asal") or "",
                    "posTarif": bb.get("hs") or "",
                    "seriBahanBaku": cint(bb.get("seri_bahan_baku")) or 0,
                    "seriBarang": cint(brg.get("seri_barang")) or 0,
                    "seriBarangDokAsal": cint(bb.get("seri_barang_asal")) or 0,
                    "seriIjin": 0,
                    "spesifikasiLainBarang": bb.get("spesifikasi_lain") or "",
                    "tanggalDaftarDokAsal": fmt_date(bb.get("tanggal_daftar_asal")) or fmt_date(doc.get("tanggal_pernyataan")) or frappe.utils.nowdate(),
                    "tipeBarang": clean_merk_tipe(bb.get("tipe")),
                    "ukuranBarang": bb.get("ukuran") or "",
                    "uraianBarang": bb.get("uraian") or "",
                }
                
                # BahanBakuTarif
                bb_item["bahanBakuTarif"] = []
                for bbt in bb_doc.get("bahan_tarif") or []:
                     bb_item["bahanBakuTarif"].append({
                        "seriBahanBaku": cint(bb.get("seri_bahan_baku")) or 0,
                        "kodeJenisPungutan": get_kode_pungutan(bbt.kode_pungutan),
                        "kodeAsalBahanBaku": bbt.kode_asal_bahan_baku or bb.get("kode_asal_bahan_baku") or "0",
                        "kodeFasilitasTarif": bbt.kode_fasilitas or "5",
                        "kodeSatuanBarang": bb.get("kode_satuan") or "",
                        "nilaiBayar": round_decimal(bbt.nilai_bayar, 2),
                        "nilaiFasilitas": round_decimal(bbt.nilai_fasilitas, 2),
                        "nilaiSudahDilunasi": round_decimal(bbt.nilai_sudah_dilunasi, 2) or 0,
                        "tarif": round_decimal(bbt.tarif, 2),
                        "tarifFasilitas": round_decimal(bbt.tarif_fasilitas, 2),
                        "jumlahSatuan": round_decimal(bbt.jumlah_satuan, 4),
                        "kodeJenisTarif": bbt.kode_tarif or "1",
                        "jumlahKemasan": 0,
                    })

                brg_item["bahanBaku"].append(bb_item)
            
            barang_list.append(brg_item)

        payload["barang"] = barang_list
        payload["netto"] = round_decimal(sum(round_decimal(b.get("netto", 0), 4) for b in payload["barang"]), 4)
        return payload
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get CEISA BC262 JSON Error")
        return {"status": "error", "message": str(e)}



@frappe.whitelist()
def get_ceisa_bc261_json(nomor_aju):
    """Export HEADER V21 to BC261 (Pengeluaran ke TLDDP - Subkontrak) JSON format"""
    try:
        doc = frappe.get_doc("HEADER V21", nomor_aju)
        
        # 1. Map Header
        payload = {
            "asalData": "S",
            "asuransi": round_decimal(doc.get("asuransi"), 2),
            "biayaPengurang": round_decimal(doc.get("biaya_pengurang"), 2),
            "biayaTambahan": round_decimal(doc.get("biaya_tambahan"), 2),
            "bruto": round_decimal(doc.get("bruto"), 4),
            "cif": round_decimal(doc.get("cif"), 2),
            "disclaimer": doc.get("disclaimer") or "1",
            "freight": round_decimal(doc.get("freight"), 2),
            "hargaPenyerahan": round_decimal(doc.get("harga_penyerahan"), 4),
            "jabatanTtd": doc.get("jabatan_pernyataan") or "",
            "jumlahKontainer": len(doc.get("kontainer") or []),
            "kodeDokumen": "261",
            "kodeKantor": doc.get("kode_kantor") or "",
            "kodeTujuanPengiriman": doc.get("kode_tujuan_pengiriman") or "",
            "kodeValuta": doc.get("kode_valuta") or "",
            "kotaTtd": doc.get("kota_pernyataan") or "",
            "namaTtd": doc.get("nama_pernyataan") or "",
            "ndpbm": round_decimal(doc.get("ndpbm"), 4) or 1.0,
            "netto": 0.0,  # Will be calculated from barang
            "nik": "",
            "nilaiBarang": round_decimal(doc.get("nilai_barang"), 2),
            "nomorAju": doc.get("nomoraju") or doc.name or "",
            "seri": 1,
            "tanggalAju": fmt_date(doc.get("tanggal_pernyataan")),
            "tanggalTtd": fmt_date(doc.get("tanggal_pernyataan")),
            "tempatStuffing": doc.get("nama_tps") or doc.get("kota_pernyataan") or "-", # Required
            "tglAkhirBerlaku": fmt_date(doc.get("tanggal_pernyataan")), # Required, default to statement date
            "tglAwalBerlaku": fmt_date(doc.get("tanggal_pernyataan")),   # Required, default to statement date
            "totalDanaSawit": 0, # Required
            "uangMuka": round_decimal(doc.get("uang_muka"), 2),
            "vd": round_decimal(doc.get("vd"), 2),
        }

        # 2. Map Entitas (Strict Ordering BC261: 3=Pengusaha TPB, 7=Pemilik, 8=Penerima)
        entitas_map = {ent.kode_entitas: ent for ent in doc.entitas}
        payload["entitas"] = []
        ordered_codes = ["3", "7", "8"]
        
        for idx, kode in enumerate(ordered_codes):
            ent = entitas_map.get(kode)
            if ent:
                ent_item = {
                    "alamatEntitas": ent.get("alamat_entitas") or "",
                    "kodeEntitas": kode,
                    "namaEntitas": ent.get("nama_entitas") or "",
                    "seriEntitas": idx + 1,
                    "nomorIdentitas": ent.get("nomor_identitas") or "",
                }
                
                # Specific fields per entity type based on Schema
                if kode == "3": # Pengusaha TPB
                    ent_item["kodeJenisApi"] = ent.get("kode_jenis_api") or "01"
                    ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                    ent_item["kodeStatus"] = ent.get("kode_status") or "10"
                    ent_item["nibEntitas"] = ent.get("nib_entitas") or ""
                    ent_item["nomorIjinEntitas"] = ent.get("nomor_ijin_entitas") or "-"
                    ent_item["tanggalIjinEntitas"] = fmt_date(ent.get("tanggal_ijin_entitas")) or fmt_date(doc.get("tanggal_pernyataan")) or frappe.utils.nowdate()
                
                elif kode == "7": # Pemilik
                    ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                    ent_item["kodeStatus"] = ent.get("kode_status") or "10"
                
                elif kode == "8": # Penerima
                    ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                    ent_item["kodeStatus"] = ent.get("kode_status") or "10"

                payload["entitas"].append(ent_item)

        # 3. Map Dokumen
        payload["dokumen"] = get_child_data(doc, "dokumen", {
            "idDokumen": "",
            "kodeDokumen": "kode_dokumen",
            "kodeFasilitas": "kode_fasilitas",
            "nomorDokumen": "nomor_dokumen",
            "seriDokumen": "seri",
            "tanggalDokumen": "tanggal_dokumen"
        })

        # 4. Map Pengangkut
        payload["pengangkut"] = []
        for p in (doc.get("pengangkut") or []):
             payload["pengangkut"].append({
                "idPengangkut": "",
                "kodeCaraAngkut": p.get("kode_cara_angkut") or "1", # Default to 1 (Laut) or derived?
                "seriPengangkut": cint(p.get("seri_pengangkut") or (p.idx))
             })

        # 5. Map Kemasan
        payload["kemasan"] = []
        for kem in (doc.get("kemasan") or []):
            payload["kemasan"].append({
                "jumlahKemasan": round_decimal(kem.get("jumlah_kemasan"), 2),
                "kodeJenisKemasan": kem.get("kode_kemasan") or "",
                "merkKemasan": clean_merk_tipe(kem.get("merek_kemasan")),
                "seriKemasan": cint(kem.get("seri")) or 0,
            })

        # 6. Map Kontainer
        payload["kontainer"] = get_child_data(doc, "kontainer", {
            "kodeJenisKontainer": "kode_jenis_kontainer",
            "kodeTipeKontainer": "kode_tipe_kontainer",
            "kodeUkuranKontainer": "kode_ukuran_kontainer",
            "nomorKontainer": "nomor_kontainer",
            "seriKontainer": "seri",
        })

        # 7. Map Pungutan
        payload["pungutan"] = []
        for pung in (doc.get("pungutan") or []):
            payload["pungutan"].append({
                "idPungutan": "",
                "kodeFasilitasTarif": pung.kode_fasilitas_tarif or "1",
                "kodeJenisPungutan": get_kode_pungutan(pung.kode_jenis_pungutan),
                "nilaiPungutan": round_decimal(pung.nilai_pungutan, 2),
            })
        
        # 8. Map Jaminan
        payload["jaminan"] = []
        for jam in (doc.get("jaminan") or []):
             payload["jaminan"].append({
                "idJaminan": "",
                "kodeJenisJaminan": jam.get("kode_jenis_jaminan") or "",
                "nilaiJaminan": round_decimal(jam.get("nilai_jaminan"), 2),
                "nomorBpj": jam.get("nomor_bpj") or "",
                "nomorJaminan": jam.get("nomor_jaminan") or "",
                "penjamin": jam.get("penjamin") or "",
                "tanggalBpj": fmt_date(jam.get("tanggal_bpj")),
                "tanggalJaminan": fmt_date(jam.get("tanggal_jaminan")),
                "tanggalJatuhTempo": fmt_date(jam.get("tanggal_jatuh_tempo")),
             })

        # 9. Map Barang
        barang_list = []
        barangs = frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc")
        
        for brg in barangs:
            brg_item = {
                "cif": round_decimal(brg.get("cif"), 2),
                "cifRupiah": round_decimal(brg.get("cif_rupiah"), 2),
                "hargaEkspor": round_decimal(brg.get("harga_ekspor"), 2),
                "hargaPenyerahan": round_decimal(brg.get("harga_penyerahan"), 4),
                "hargaPerolehan": round_decimal(brg.get("harga_perolehan"), 2),
                "isiPerKemasan": round_decimal(brg.get("isi_per_kemasan"), 2),
                "jumlahKemasan": round_decimal(brg.get("jumlah_kemasan"), 2),
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4),
                "kodeAsalBahanBaku": brg.get("kode_asal_bahan_baku") or "1", # Required at barang level too
                "kodeAsalBarang": brg.get("kode_daerah_asal") or "1", # Assuming kode_daerah_asal or default
                "kodeBarang": brg.get("kode_barang") or "",
                "kodeDokumen": "261",
                "kodeJenisKemasan": brg.get("kode_kemasan") or "",
                "kodeNegaraAsal": brg.get("kode_negara_asal") or "ID",
                "kodeSatuanBarang": brg.get("kode_satuan") or "",
                "merk": clean_merk_tipe(brg.get("merek")),
                "ndpbm": round_decimal(brg.get("ndpbm"), 4) or 1.0,
                "netto": round_decimal(brg.get("netto"), 4),
                "nilaiBarang": round_decimal(brg.get("nilai_barang"), 2),
                "nilaiJasa": round_decimal(brg.get("nilai_jasa"), 2),
                "posTarif": brg.get("hs") or "",
                "seriBarang": cint(brg.get("seri_barang")) or 0,
                "spesifikasiLain": brg.get("spesifikasi_lain") or "",
                "tipe": clean_merk_tipe(brg.get("tipe")),
                "uangMuka": 0,
                "ukuran": brg.get("ukuran") or "",
                "uraian": brg.get("uraian") or "",
            }

            # BAHAN BAKU 
            brg_item["bahanBaku"] = []
            bahan_bakus = frappe.get_all("BAHAN BAKU", filters={"parent_barang": brg.get("name")}, fields=["*"], order_by="seri_bahan_baku asc")
            for bb in bahan_bakus:
                bb_doc = frappe.get_doc("BAHAN BAKU", bb.get("name"))
                bb_item = {
                    "cif": round_decimal(bb.get("cif"), 2),
                    "cifRupiah": round_decimal(bb.get("cif_rupiah"), 2),
                    "flagTis": "0", # Required
                    "hargaPenyerahan": round_decimal(bb.get("harga_penyerahan"), 4),
                    "hargaPerolehan": round_decimal(bb.get("harga_perolehan"), 2),
                    "isiPerKemasan": 0, # Required, default
                    "jumlahSatuan": round_decimal(bb.get("jumlah_satuan"), 4),
                    "kodeAsalBahanBaku": bb.get("kode_asal_bahan_baku") or "0",
                    "kodeBarang": bb.get("kode_barang") or "",
                    "kodeDokAsal": bb.get("kode_dokumen_asal") or "40",
                    "kodeDokumen": bb.get("kode_dokumen_asal") or "262", # Required field name: kodeDokumen
                    "kodeKantor": bb.get("kode_kantor_asal") or doc.get("kode_kantor") or "",
                    "kodeSatuanBarang": bb.get("kode_satuan") or "",
                    "merkBarang": clean_merk_tipe(bb.get("merek")),
                    "ndpbm": round_decimal(bb.get("ndpbm"), 4) or 1.0,
                    "netto": round_decimal(bb.get("netto"), 4),
                    "nilaiJasa": 0,
                    "nomorAjuDokAsal": bb.get("nomor_aju_asal") or "",
                    "nomorDaftarDokAsal": bb.get("nomor_daftar_asal") or "",
                    "nomorDokumen": bb.get("nomor_dokumen_asal") or "", 
                    "posTarif": bb.get("hs") or "",
                    "seriBahanBaku": cint(bb.get("seri_bahan_baku")) or 0,
                    "seriBarang": cint(brg.get("seri_barang")) or 0,
                    "seriBarangDokAsal": cint(bb.get("seri_barang_asal")) or 0,
                    "seriIjin": 0,
                    "spesifikasiLainBarang": bb.get("spesifikasi_lain") or "",
                    "tanggalDaftarDokAsal": fmt_date(bb.get("tanggal_daftar_asal")) or fmt_date(doc.get("tanggal_pernyataan")) or frappe.utils.nowdate(),
                    "tipeBarang": clean_merk_tipe(bb.get("tipe")),
                    "ukuranBarang": bb.get("ukuran") or "",
                    "uraianBarang": bb.get("uraian") or "",
                }
                
                # BahanBakuTarif
                bb_item["bahanBakuTarif"] = []
                for bbt in bb_doc.get("bahan_tarif") or []:
                     bb_item["bahanBakuTarif"].append({
                        "seriBahanBaku": cint(bb.get("seri_bahan_baku")) or 0,
                        "kodeJenisPungutan": get_kode_pungutan(bbt.kode_pungutan),
                        "kodeAsalBahanBaku": bbt.kode_asal_bahan_baku or bb.get("kode_asal_bahan_baku") or "0",
                        "kodeFasilitasTarif": bbt.kode_fasilitas or "5",
                        "kodeSatuanBarang": bb.get("kode_satuan") or "", # Required in tarif
                        "nilaiBayar": round_decimal(bbt.nilai_bayar, 2),
                        "nilaiFasilitas": round_decimal(bbt.nilai_fasilitas, 2),
                        "nilaiSudahDilunasi": round_decimal(bbt.nilai_sudah_dilunasi, 2) or 0,
                        "tarif": round_decimal(bbt.tarif, 2),
                        "tarifFasilitas": round_decimal(bbt.tarif_fasilitas, 2),
                        "jumlahSatuan": round_decimal(bbt.jumlah_satuan, 4),
                        "kodeJenisTarif": bbt.kode_tarif or "1",
                        "jumlahKemasan": 0,
                    })

                brg_item["bahanBaku"].append(bb_item)
            
            barang_list.append(brg_item)

        payload["barang"] = barang_list
        payload["netto"] = round_decimal(sum(round_decimal(b.get("netto", 0), 4) for b in payload["barang"]), 4)
        return payload
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get CEISA BC261 JSON Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_ceisa_bc16_json(nomor_aju):
    """Export HEADER V21 to BC16 (PLB Pemasukan) JSON format"""
    try:
        doc = frappe.get_doc("HEADER V21", nomor_aju)
        payload = {
            "asalData": "S",
            "nomorAju": doc.get("nomoraju") or "",
            "seri": 1, # Default to 1
            "kodeDokumen": "16",
            "kodeKantor": doc.get("kode_kantor") or "",
            "kodeKantorBongkar": doc.get("kode_kantor_bongkar") or "",
            "kodeTps": doc.get("kode_tps") or "",
            "kodeIncoterm": doc.get("kode_incoterm") or "",
            "cif": round_decimal(doc.get("cif"), 2),
            "kodeJenisNilai": doc.get("kode_jenis_nilai") or "",
            "kodePelMuat": doc.get("kode_pelabuhan_muat") or "",
            "kodePelTransit": doc.get("kode_pelabuhan_transit") or "",
            "kodePelBongkar": doc.get("kode_pelabuhan_bongkar") or "",
            "kodeValuta": doc.get("kode_valuta") or "",
            "bruto": round_decimal(doc.get("bruto"), 4),
            "netto": 0.0, # Will be calculated from items
            "kotaTtd": doc.get("kota_pernyataan") or "",
            "tanggalTtd": fmt_date(doc.get("tanggal_pernyataan")),
            "jabatanTtd": doc.get("jabatan_pernyataan") or "",
            "namaTtd": doc.get("nama_pernyataan") or "",
            "disclaimer": "1",
            "ndpbm": round_decimal(doc.get("ndpbm"), 4) or 1.0,
            "kodeTutupPu": doc.get("kode_tutup_pu") or "11",
            "nomorBc11": doc.get("nomor_bc11") or "",
            "posBc11": doc.get("nomor_pos") or "",
            "subposBc11": doc.get("nomor_sub_pos") or "",
            "tanggalBc11": fmt_date(doc.get("tanggal_bc11")),
            "tanggalTiba": fmt_date(doc.get("tanggal_tiba")),
        }
        
        # 2. Map Entitas (Strict Ordering: 10, 3, 7, 9)
        entitas_map = {ent.kode_entitas: ent for ent in doc.entitas}
        payload["entitas"] = []
        
        # BC16 Tuple-like Items: 0=Penjual(10), 1=Pengusaha PLB(3), 2=Pemilik Barang(7), 3=Pengirim(9)
        ordered_codes = ["10", "3", "7", "9"]
        for idx, kode in enumerate(ordered_codes):
            ent = entitas_map.get(kode)
            if ent:
                ent_item = {
                    "alamatEntitas": ent.get("alamat_entitas") or "",
                    "kodeEntitas": kode,
                    "namaEntitas": ent.get("nama_entitas") or "",
                    "seriEntitas": idx + 1,
                }
                if kode == "10":
                    ent_item["kodeNegara"] = ent.get("kode_negara") or "ID"
                elif kode == "3":
                    ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                    ent_item["nomorIdentitas"] = ent.get("nomor_identitas") or ""
                    ent_item["nomorIjinEntitas"] = ent.get("nomor_ijin_entitas") or ""
                    tgl_ijin = fmt_date(ent.get("tanggal_ijin_entitas"))
                    if tgl_ijin:
                        ent_item["tanggalIjinEntitas"] = tgl_ijin
                elif kode == "7":
                    ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                    ent_item["nomorIdentitas"] = ent.get("nomor_identitas") or ""
                    ent_item["kodeStatus"] = ent.get("kode_status") or "10"
                    if ent.get("nib_entitas"):
                        ent_item["nibEntitas"] = ent.get("nib_entitas")
                elif kode == "9":
                    ent_item["kodeNegara"] = ent.get("kode_negara") or "ID"
                payload["entitas"].append(ent_item)
            else:
                # Add placeholder if required entitas missing? 
                # Schema might fail if a required position is empty.
                pass

        # 3. Map Kemasan
        payload["kemasan"] = []
        for kem in (doc.get("kemasan") or []):
            payload["kemasan"].append({
                "jumlahKemasan": cint(kem.get("jumlah_kemasan")), # Must be integer
                "kodeJenisKemasan": kem.get("kode_kemasan") or "",
                "merkKemasan": clean_merk_tipe(kem.get("merek_kemasan")),
                "seriKemasan": cint(kem.get("seri")) or 1
            })

        # 4. Map Kontainer
        payload["kontainer"] = get_child_data(doc, "kontainer", {
            "kodeJenisKontainer": "kode_jenis_kontainer",
            "kodeTipeKontainer": "kode_tipe_kontainer",
            "kodeUkuranKontainer": "kode_ukuran_kontainer",
            "nomorKontainer": "nomor_kontainer",
            "seriKontainer": "seri"
        })

        # 5. Map Dokumen (Positional: 0=Invoice 380, etc.)
        all_docs = get_child_data(doc, "dokumen", {
                "kodeDokumen": "kode_dokumen",
                "nomorDokumen": "nomor_dokumen",
                "seriDokumen": "seri",
                "tanggalDokumen": "tanggal_dokumen"
            })
        invoice_docs = [d for d in all_docs if d.get("kodeDokumen") == "380"]
        bl_awb_docs = [d for d in all_docs if d.get("kodeDokumen") in ["705", "740"]]
        other_docs = [d for d in all_docs if d.get("kodeDokumen") not in ["380", "705", "740"]]
        payload["dokumen"] = invoice_docs + bl_awb_docs + other_docs

        # 6. Map Pengangkut (Mandatory for BC16)
        payload["pengangkut"] = get_child_data(doc, "pengangkut", {
            "kodeBendera": "kode_bendera",
            "namaPengangkut": "nama_pengangkut",
            "nomorPengangkut": "nomor_pengangkut",
            "kodeCaraAngkut": "kode_cara_angkut",
            "seriPengangkut": "seri_pengangkut"
        })
        if not payload["pengangkut"] and doc.get("pengangkut"):
             # Double check mapping if standard fails
             pass

        # 7. Map Barang
        barang_list = []
        total_netto = 0.0
        for brg in frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc"):
            brg_netto = round_decimal(brg.get("netto"), 4)
            total_netto += brg_netto
            
            brg_doc = frappe.get_doc("BARANG V1", brg.get("name"))
            brg_item = {
                "seriBarang": cint(brg.get("seri_barang")) or 0,
                "posTarif": brg.get("hs") or "",
                "kodeBarang": brg.get("kode_barang") or "",
                "uraian": brg.get("uraian") or "",
                "merk": clean_merk_tipe(brg.get("merek")),
                "tipe": clean_merk_tipe(brg.get("tipe")),
                "ukuran": brg.get("ukuran") or "",
                "spesifikasiLain": brg.get("spesifikasi_lain") or "",
                "kodeNegaraAsal": brg.get("kode_negara_asal") or "ID", # Regex pattern ^[A-Z]{2}$
                "kodeKategoriBarang": brg.get("kode_kategori_barang") or "",
                "cif": round_decimal(brg.get("cif"), 2),
                "cifRupiah": round_decimal(brg.get("cif_rupiah"), 2),
                "kodeJenisNilai": brg.get("kode_jenis_nilai") or "",
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4),
                "kodeSatuanBarang": brg.get("kode_satuan") or "",
                "netto": brg_netto,
                "jumlahKemasan": round_decimal(brg.get("jumlah_kemasan"), 2),
                "kodeJenisKemasan": brg.get("kode_kemasan") or "",
            }
            # BARANG TARIF
            brg_item["barangTarif"] = []
            for t in brg_doc.get("barang_tarif") or []:
                brg_item["barangTarif"].append({
                    "kodeJenisTarif": t.get("kode_tarif") or "1",
                    "jumlahSatuan": round_decimal(t.get("jumlah_satuan"), 4),
                    "kodeFasilitasTarif": t.get("kode_fasilitas") or "1",
                    "kodeSatuanBarang": t.get("kode_satuan") or "",
                    "kodeJenisPungutan": get_kode_pungutan(t.get("kode_pungutan")),
                    "nilaiBayar": round_decimal(t.get("nilai_bayar"), 2),
                    "seriBarang": cint(brg.get("seri_barang")) or 0,
                    "tarif": round_decimal(t.get("tarif"), 2),
                    "tarifFasilitas": round_decimal(t.get("tarif_fasilitas"), 2)
                })
            
            # Sort tarif: BM first
            brg_item["barangTarif"] = sorted(brg_item["barangTarif"], key=lambda x: {"BM": 0, "PPH": 1, "PPN": 2}.get(x.get("kodeJenisPungutan"), 99))
            
            barang_list.append(brg_item)
            
        payload["barang"] = barang_list
        payload["netto"] = round_decimal(total_netto, 4)
        
        # Clean up fields that CEISA rejects if null
        for field in ["tanggalBc11"]:
            if payload.get(field) is None:
                payload.pop(field, None)

        return payload
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get CEISA BC16 JSON Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_ceisa_bc28_json(nomor_aju):
    """Export HEADER V21 to BC28 (PLB Pengeluaran) JSON format"""
    try:
        doc = frappe.get_doc("HEADER V21", nomor_aju)
        payload = {
            "asalData": "S",
            "bruto": round_decimal(doc.get("bruto"), 4),
            "cif": round_decimal(doc.get("cif"), 2),
            "disclaimer": "1",
            "kodeCaraBayar": doc.get("kode_cara_bayar") or "",
            "kodeDokumen": "28",
            "kodeGudangAsal": doc.get("kode_tps") or "",
            "kodeIncoterm": doc.get("kode_incoterm") or "",
            "kodeJenisNilai": doc.get("kode_jenis_nilai") or "",
            "kodeJenisProsedur": doc.get("kode_jenis_prosedur") or "",
            "kodeJenisImpor": doc.get("kode_jenis_impor") or "",
            "kodeKantor": doc.get("kode_kantor") or "",
            "kodeValuta": doc.get("kode_valuta") or "",
            "kotaTtd": doc.get("kota_pernyataan") or "",
            "namaTtd": doc.get("nama_pernyataan") or "",
            "jabatanTtd": doc.get("jabatan_pernyataan") or "",
            "ndpbm": round_decimal(doc.get("ndpbm"), 4) or 1.0,
            "netto": 0.0,  # Will be calculated from barang
            "nik": doc.get("nik_identitas") or "",
            "nilaiBarang": round_decimal(doc.get("nilai_barang"), 2),
            "nomorAju": doc.get("nomoraju") or doc.name or "",
            "seri": 1,
            "tanggalTtd": fmt_date(doc.get("tanggal_pernyataan")),
            "volume": round_decimal(doc.get("volume"), 4),
        }
        
        # 2. Map Entitas (Strict Ordering for BC28: 1, 10, 3, 7)
        entitas_map = {ent.kode_entitas: ent for ent in doc.entitas}
        payload["entitas"] = []
        ordered_codes = ["1", "10", "3", "7"]
        
        for idx, kode in enumerate(ordered_codes):
            ent = entitas_map.get(kode)
            if ent:
                ent_item = {
                    "alamatEntitas": ent.get("alamat_entitas") or "",
                    "kodeEntitas": kode,
                    "namaEntitas": ent.get("nama_entitas") or "",
                    "seriEntitas": idx + 1,
                    "nomorIdentitas": ent.get("nomor_identitas") or "",
                }
                # BC28 Specific fields for certain entities
                if kode == "1": # Importir
                    ent_item["kodeJenisApi"] = ent.get("kode_jenis_api") or "01"
                    ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                    ent_item["kodeStatus"] = ent.get("kode_status") or "10"
                    ent_item["nibEntitas"] = ent.get("nib_entitas") or ""
                elif kode == "10": # Penjual
                    ent_item["kodeNegara"] = ent.get("kode_negara") or "ID"
                elif kode == "3": # Pengusaha PLB
                    ent_item["kodeJenisApi"] = ent.get("kode_jenis_api") or "01"
                    ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                    ent_item["kodeStatus"] = ent.get("kode_status") or "10"
                    ent_item["nibEntitas"] = ent.get("nib_entitas") or "0"
                    ent_item["nomorIjinEntitas"] = ent.get("nomor_ijin_entitas") or "-"
                    
                    # Mandatory field, fallback if empty
                    tgl_ijin = fmt_date(ent.get("tanggal_ijin_entitas"))
                    if not tgl_ijin:
                         tgl_ijin = fmt_date(doc.get("tanggal_pernyataan")) or frappe.utils.nowdate()
                    ent_item["tanggalIjinEntitas"] = tgl_ijin
                elif kode == "7": # Pemilik Barang
                    ent_item["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kode_jenis_identitas"))
                payload["entitas"].append(ent_item)

        # 3. Map Kemasan
        payload["kemasan"] = []
        for kem in (doc.get("kemasan") or []):
            payload["kemasan"].append({
                "jumlahKemasan": cint(kem.get("jumlah_kemasan")),
                "kodeJenisKemasan": kem.get("kode_kemasan") or "",
                "merkKemasan": clean_merk_tipe(kem.get("merek_kemasan")),
                "seriKemasan": cint(kem.get("seri")) or 1
            })

        # 4. Map Kontainer
        payload["kontainer"] = get_child_data(doc, "kontainer", {
            "kodeJenisKontainer": "kode_jenis_kontainer",
            "kodeTipeKontainer": "kode_tipe_kontainer",
            "kodeUkuranKontainer": "kode_ukuran_kontainer",
            "nomorKontainer": "nomor_kontainer",
            "seriKontainer": "seri"
        })

        # 5. Map Dokumen
        payload["dokumen"] = get_child_data(doc, "dokumen", {
            "kodeDokumen": "kode_dokumen",
            "nomorDokumen": "nomor_dokumen",
            "seriDokumen": "seri",
            "tanggalDokumen": "tanggal_dokumen"
        })
        
        # 6. Map Pengangkut (Mandatory for BC28)
        payload["pengangkut"] = get_child_data(doc, "pengangkut", {
            "kodeCaraAngkut": "kode_cara_angkut",
            "seriPengangkut": "seri_pengangkut"
        })
        if not payload["pengangkut"]:
            # Default if missing
            payload["pengangkut"] = [{
                "kodeCaraAngkut": doc.get("kode_cara_angkut") or "1",
                "seriPengangkut": 1
            }]

        # 7. Map Barang
        payload["barang"] = []
        for brg in frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc"):
            brg_doc = frappe.get_doc("BARANG V1", brg.get("name"))
            brg_item = {
                "cif": round_decimal(brg.get("cif"), 2),
                "jumlahKemasan": cint(brg.get("jumlah_kemasan")),
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4),
                "kodeBarang": brg.get("kode_barang") or "",
                "kodeJenisNilai": brg.get("kode_jenis_nilai") or "",
                "kodeJenisKemasan": brg.get("kode_kemasan") or "",
                "kodeNegaraAsal": brg.get("kode_negara_asal") or "ID",
                "kodePerhitungan": brg.get("kode_perhitungan") or "1",
                "kodeSatuanBarang": brg.get("kode_satuan") or "",
                "merk": clean_merk_tipe(brg.get("merek")),
                "netto": round_decimal(brg.get("netto"), 4),
                "nilaiBarang": round_decimal(brg.get("nilai_barang"), 2),
                "nilaiTambah": round_decimal(brg.get("nilai_tambah"), 2),
                "persentaseImpor": round_decimal(brg.get("persentase_impor"), 2),
                "posTarif": brg.get("hs") or "",
                "seriBarang": cint(brg.get("seri_barang")) or 1,
                "seriBarangDokAsal": cint(brg.get("seri_barang_asal")) or 1,
                "spesifikasiLain": brg.get("spesifikasi_lain") or "",
                "tipe": clean_merk_tipe(brg.get("tipe")),
                "ukuran": brg.get("ukuran") or "",
                "uraian": brg.get("uraian") or "",
                "volume": round_decimal(brg.get("volume"), 4),
                "ndpbm": round_decimal(brg.get("ndpbm"), 4) or round_decimal(doc.get("ndpbm"), 4) or 1.0,
                "cifRupiah": round_decimal(brg.get("cif_rupiah"), 2),
                "hargaPerolehan": round_decimal(brg.get("harga_perolehan"), 2),
                "kodeAsalBahanBaku": brg.get("kode_asal_bahan_baku") or "0",
                "kodeDokAsal": brg.get("kode_dokumen_asal") or "16",
                "kodeKantorAsal": brg.get("kode_kantor_asal") or doc.get("kode_kantor") or "",
                "nomorAjuDokAsal": brg.get("nomor_aju_asal") or "",
                "nomorDaftarDokAsal": brg.get("nomor_daftar_asal") or "",
            }
            tgl_daftar = fmt_date(brg.get("tanggal_daftar_asal")) or fmt_date(doc.get("tanggal_tiba"))
            if tgl_daftar:
                 brg_item["tanggalDaftarDokAsal"] = tgl_daftar
            # BARANG TARIF
            brg_item["barangTarif"] = []
            for t in brg_doc.get("barang_tarif") or []:
                brg_item["barangTarif"].append({
                    "kodeJenisTarif": t.get("kode_tarif") or "1",
                    "jumlahSatuan": round_decimal(t.get("jumlah_satuan"), 4),
                    "kodeFasilitasTarif": t.get("kode_fasilitas") or "1",
                    "kodeSatuanBarang": t.get("kode_satuan") or "",
                    "kodeJenisPungutan": get_kode_pungutan(t.get("kode_pungutan")),
                    "nilaiBayar": round_decimal(t.get("nilai_bayar"), 2),
                    "nilaiFasilitas": round_decimal(t.get("nilai_fasilitas"), 2),
                    "nilaiSudahDilunasi": round_decimal(t.get("nilai_sudah_dilunasi"), 2) or 0,
                    "seriBarang": cint(brg.get("seri_barang")) or 1,
                    "tarif": round_decimal(t.get("tarif"), 2),
                    "tarifFasilitas": round_decimal(t.get("tarif_fasilitas"), 2)
                })
            
            # 8. barangDokumen (Mandatory in BC28)
            brg_item["barangDokumen"] = []
            for d in brg_doc.get("barang_dokumen") or []:
                brg_item["barangDokumen"].append({
                    "seriDokumen": cint(d.get("seri")) or 1,
                    "seriIjin": cint(d.get("seri_ijin")) or 0
                })

            payload["barang"].append(brg_item)

        payload["netto"] = round_decimal(sum(round_decimal(b.get("netto", 0), 4) for b in payload["barang"]), 4)
        return payload
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get CEISA BC28 JSON Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_ceisa_p3bet_json(nomor_aju):
    """Export HEADER V21 to P3BET (331) JSON format"""
    try:
        doc = frappe.get_doc("HEADER V21", nomor_aju)
        payload = {
            "Declaration": {
                "asalData": "S",
                "asuransi": round_decimal(doc.get("asuransi"), 2),
                "bruto": round_decimal(doc.get("bruto"), 4),
                "cif": round_decimal(doc.get("cif"), 2),
                "disclaimer": doc.get("disclaimer") or "1",
                "freight": round_decimal(doc.get("freight"), 2),
                "jabatanTtd": doc.get("jabatan_pernyataan") or "",
                "jumlahKontainer": len(doc.get("kontainer") or []),
                "jumlahTandaPengaman": cint(doc.get("jumlah_tanda_pengaman")) or 0,
                "kodeAsuransi": doc.get("kode_asuransi") or "DN",
                "kodeDokumen": "331",
                "kodeGudangAsal": doc.get("kode_tps") or "",
                "kodeJenisTandaPengaman": doc.get("kode_jenis_tanda_pengaman") or "",
                "kodeKantor": doc.get("kode_kantor") or "",
                "kodeKantorMuat": doc.get("kode_kantor_muat") or "",
                "kodeNegaraTujuan": doc.get("kode_negara_tujuan") or "",
                "kodePelBongkar": doc.get("kode_pelabuhan_bongkar") or "",
                "kodePelMuat": doc.get("kode_pelabuhan_muat") or "",
                "kodePelTujuan": doc.get("kode_pelabuhan_tujuan") or "",
                "kodeTps": doc.get("kode_tps") or "",
                "kotaTtd": doc.get("kota_pernyataan") or "",
                "namaTtd": doc.get("nama_pernyataan") or "",
                "netto": round_decimal(doc.get("netto"), 4),
                "nilaiBarang": round_decimal(doc.get("nilai_barang"), 2),
                "nomorAju": doc.get("nomoraju") or doc.name or "",
                "seri": 0,
                "tanggalMuat": fmt_date(doc.get("tanggal_muat")),
                "tanggalTtd": fmt_date(doc.get("tanggal_pernyataan")),
                "tempatStuffing": doc.get("tempat_stuffing") or "",
            }
        }
        decl = payload["Declaration"]

        # 2. Map Entitas (3, 8, 7)
        decl["entitas"] = []
        for ent in (doc.get("entitas") or []):
            ent_item = {
                "alamatEntitas": ent.get("alamat_entitas") or "",
                "kodeEntitas": get_kode_entitas(ent.get("kode_entitas")),
                "namaEntitas": ent.get("nama_entitas") or "",
                "seriEntitas": cint(ent.get("seri")) or 0,
            }
            if ent.get("kode_entitas") == "3":
                ent_item.update({
                    "kodeJenisIdentitas": get_kode_identitas(ent.get("kode_jenis_identitas")),
                    "nomorIdentitas": ent.get("nomor_identitas") or "",
                    "nibEntitas": ent.get("nib_entitas") or "",
                    "nomorIjinEntitas": ent.get("nomor_ijin_entitas") or "",
                })
            elif ent.get("kode_entitas") == "8":
                ent_item.update({
                    "kodeNegara": ent.get("kode_negara") or "",
                })
            elif ent.get("kode_entitas") == "7":
                ent_item.update({
                    "kodeJenisIdentitas": get_kode_identitas(ent.get("kode_jenis_identitas")),
                    "kodeStatus": ent.get("kode_status") or "",
                    "nomorIdentitas": ent.get("nomor_identitas") or "",
                    "nibEntitas": ent.get("nib_entitas") or "",
                    "nomorIjinEntitas": ent.get("nomor_ijin_entitas") or "",
                    "tanggalIjinEntitas": fmt_date(ent.get("tanggal_ijin_entitas")),
                })
            decl["entitas"].append(ent_item)

        # 3. Map Child Tables
        decl["kemasan"] = []
        for k in (doc.get("kemasan") or []):
            decl["kemasan"].append({
                "jumlahKemasan": cint(k.get("jumlah_kemasan")),
                "kodeJenisKemasan": k.get("kode_kemasan") or "",
                "merkKemasan": clean_merk_tipe(k.get("merek_kemasan")),
                "seriKemasan": cint(k.get("seri")) or 0
            })
            
        decl["kontainer"] = get_child_data(doc, "kontainer", {
            "kodeJenisKontainer": "kode_jenis_kontainer",
            "kodeTipeKontainer": "kode_tipe_kontainer",
            "kodeUkuranKontainer": "kode_ukuran_kontainer",
            "nomorKontainer": "nomor_kontainer",
            "seriKontainer": "seri"
        })
        
        decl["dokumen"] = get_child_data(doc, "dokumen", {
            "kodeDokumen": "kode_dokumen",
            "nomorDokumen": "nomor_dokumen",
            "seriDokumen": "seri",
            "tanggalDokumen": "tanggal_dokumen"
        })
        
        decl["pengangkut"] = get_child_data(doc, "pengangkut", {
            "namaPengangkut": "nama_pengangkut",
            "nomorPengangkut": "nomor_pengangkut",
            "seriPengangkut": "seri_pengangkut",
            "kodeCaraAngkut": "kode_cara_angkut",
            "callSign": "call_sign"
        })

        # 4. Map Barang
        decl["barang"] = []
        for brg in frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc"):
            brg_doc = frappe.get_doc("BARANG V1", brg.get("name"))
            brg_item = {
                "cif": round_decimal(brg.get("cif"), 2),
                "jumlahKemasan": round_decimal(brg.get("jumlah_kemasan"), 2),
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4),
                "kodeBarang": brg.get("kode_barang") or "",
                "kodeDokumen": "331",
                "kodeJenisKemasan": brg.get("kode_kemasan") or "",
                "kodeSatuanBarang": brg.get("kode_satuan") or "",
                "merk": clean_merk_tipe(brg.get("merek")),
                "ndpbm": round_decimal(brg.get("ndpbm"), 4),
                "netto": round_decimal(brg.get("netto"), 4),
                "nilaiBarang": round_decimal(brg.get("nilai_barang"), 2),
                "nilaiDevisa": round_decimal(brg.get("nilai_devisa"), 2),
                "posTarif": brg.get("hs") or "",
                "seriBarang": cint(brg.get("seri_barang")) or 0,
                "spesifikasiLain": brg.get("spesifikasi_lain") or "",
                "tipe": clean_merk_tipe(brg.get("tipe")),
                "ukuran": brg.get("ukuran") or "",
                "uraian": brg.get("uraian") or "",
                "kodeKantorAsal": brg.get("kode_kantor_asal") or "",
                "kodeDokAsal": brg.get("kode_dokumen_asal") or "",
                "nomorDaftarDokAsal": brg.get("nomor_daftar_asal") or "",
                "seriBarangDokAsal": cint(brg.get("seri_barang_asal") or 0),
                "tanggalDaftarDokAsal": fmt_date(brg.get("tanggal_daftar_asal")),
                "nomorAjuDokAsal": brg.get("nomor_aju_asal") or "",
            }
            # BARANG TARIF
            brg_item["barangTarif"] = []
            for t in brg_doc.get("barang_tarif") or []:
                brg_item["barangTarif"].append({
                    "kodeJenisTarif": t.get("kode_tarif") or "1",
                    "jumlahSatuan": round_decimal(t.get("jumlah_satuan"), 4),
                    "kodeFasilitasTarif": t.get("kode_fasilitas") or "",
                    "kodeSatuanBarang": t.get("kode_satuan") or "",
                    "kodeJenisPungutan": get_kode_pungutan(t.get("kode_pungutan")),
                    "nilaiBayar": round_decimal(t.get("nilai_bayar"), 2),
                    "seriBarang": cint(brg.get("seri_barang")) or 0,
                    "tarif": round_decimal(t.get("tarif"), 2),
                    "tarifFasilitas": round_decimal(t.get("tarif_fasilitas"), 2)
                })
            # BARANG DOKUMEN
            brg_item["barangDokumen"] = get_child_data(brg_doc, "barang_dokumen", {
                "seriDokumen": "seri_dokumen",
                "seriIjin": "seri_izin"
            })
            # BARANG PEMILIK
            brg_item["barangPemilik"] = [{"seriEntitas": 1}]
            decl["barang"].append(brg_item)
        return payload
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get CEISA P3BET JSON Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_ceisa_ftz011_json(nomor_aju):
    """Export HEADER V21 to FTZ01-1 (PPFTZ from LDP) JSON format"""
    try:
        doc = frappe.get_doc("HEADER V21", nomor_aju)
        payload = {
            "Declaration": {
                "asalData": "S",
                "asuransi": round_decimal(doc.get("asuransi"), 2),
                "bruto": round_decimal(doc.get("bruto"), 4),
                "cif": round_decimal(doc.get("cif"), 2),
                "fob": round_decimal(doc.get("fob"), 2),
                "freight": round_decimal(doc.get("freight"), 2),
                "jabatanTtd": doc.get("jabatan_pernyataan") or "",
                "jumlahKontainer": len(doc.get("kontainer") or []),
                "kodeAsalBarangFtz": doc.get("kode_barang_asal_ftz") or "1",
                "kodeAsuransi": doc.get("kode_asuransi") or "DN",
                "kodeCaraBayar": doc.get("kode_cara_bayar") or "",
                "kodeCaraDagang": doc.get("kode_cara_dagang") or "",
                "kodeDokumen": "511",
                "kodeIncoterm": doc.get("kode_incoterm") or "",
                "kodeKantor": doc.get("kode_kantor") or "",
                "kodeJenisProsedur": doc.get("kode_jenis_prosedur") or "1",
                "kodeTujuanPemasukan": doc.get("kode_tujuan_pemasukan") or "1",
                "kodePelMuat": doc.get("kode_pelabuhan_muat") or "",
                "kodePelTransit": doc.get("kode_pelabuhan_transit") or "",
                "kodePelTujuan": doc.get("kode_pelabuhan_tujuan") or "",
                "kodeTps": doc.get("kode_tps") or "",
                "kodeValuta": doc.get("kode_valuta") or "IDR",
                "kotaTtd": doc.get("kota_pernyataan") or "",
                "namaTtd": doc.get("nama_pernyataan") or "",
                "ndpbm": round_decimal(doc.get("ndpbm"), 4),
                "netto": round_decimal(doc.get("netto"), 4),
                "nomorAju": doc.get("nomoraju") or doc.name or "",
                "nomorBc11": doc.get("nomor_bc11") or "",
                "posBc11": doc.get("nomor_pos") or "",
                "seri": 0,
                "subposBc11": doc.get("nomor_sub_pos") or "",
                "tanggalBc11": fmt_date(doc.get("tanggal_bc11")),
                "tanggalTiba": fmt_date(doc.get("tanggal_tiba")),
                "tanggalTtd": fmt_date(doc.get("tanggal_pernyataan")),
                "volume": round_decimal(doc.get("volume"), 4),
                "biayaTambahan": round_decimal(doc.get("biaya_tambahan"), 2),
                "biayaPengurang": round_decimal(doc.get("biaya_pengurang"), 2),
                "entitas": get_child_data(doc, "entitas", {
                    "alamatEntitas": "alamat_entitas",
                    "kodeEntitas": "kode_entitas",
                    "kodeJenisApi": "kode_jenis_api",
                    "kodeJenisIdentitas": "kode_jenis_identitas",
                    "kodeNegara": "kode_negara",
                    "kodeStatus": "kode_status",
                    "namaEntitas": "nama_entitas",
                    "nomorIdentitas": "nomor_identitas",
                    "seriEntitas": "seri"
                }),
                "kemasan": get_child_data(doc, "kemasan", {
                    "jumlahKemasan": "jumlah_kemasan",
                    "kodeJenisKemasan": "kode_kemasan",
                    "merkKemasan": "merek_kemasan",
                    "seriKemasan": "seri"
                }),
                "kontainer": get_child_data(doc, "kontainer", {
                    "kodeJenisKontainer": "kode_jenis_kontainer",
                    "kodeTipeKontainer": "kode_tipe_kontainer",
                    "kodeUkuranKontainer": "kode_ukuran_kontainer",
                    "nomorKontainer": "nomor_kontainer",
                    "seriKontainer": "seri"
                }),
                "dokumen": get_child_data(doc, "dokumen", {
                    "kodeDokumen": "kode_dokumen",
                    "nomorDokumen": "nomor_dokumen",
                    "seriDokumen": "seri",
                    "tanggalDokumen": "tanggal_dokumen"
                }),
                "pengangkut": get_child_data(doc, "pengangkut", {
                    "namaPengangkut": "nama_pengangkut",
                    "nomorPengangkut": "nomor_pengangkut",
                    "seriPengangkut": "seri_pengangkut",
                    "kodeCaraAngkut": "kode_cara_angkut",
                    "kodeBendera": "kode_bendera"
                }),
                "barang": []
            }
        }
        for brg in frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc"):
            brg_doc = frappe.get_doc("BARANG V1", brg.get("name"))
            brg_item = {
                "idBarang": "",
                "asuransi": round_decimal(brg.get("asuransi"), 2),
                "bruto": round_decimal(brg.get("bruto"), 4),
                "cif": round_decimal(brg.get("cif"), 2),
                "fob": round_decimal(brg.get("fob"), 2),
                "freight": round_decimal(brg.get("freight"), 2),
                "hargaPenyerahan": round_decimal(brg.get("harga_penyerahan"), 4),
                "hargaSatuan": round_decimal(brg.get("harga_satuan"), 4),
                "isiPerKemasan": round_decimal(brg.get("isi_per_kemasan"), 2),
                "jumlahKemasan": round_decimal(brg.get("jumlah_kemasan"), 2),
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4),
                "kodeJenisKemasan": brg.get("kode_kemasan") or "",
                "kodeNegaraAsal": brg.get("kode_negara_asal") or "",
                "kodeSatuanBarang": brg.get("kode_satuan") or "",
                "merk": clean_merk_tipe(brg.get("merek")),
                "netto": round_decimal(brg.get("netto"), 4),
                "posTarif": brg.get("hs") or "",
                "seriBarang": cint(brg.get("seri_barang")) or 0,
                "spesifikasiLain": brg.get("spesifikasi_lain") or "",
                "tipe": clean_merk_tipe(brg.get("tipe")),
                "ukuran": brg.get("ukuran") or "",
                "uraian": brg.get("uraian") or "",
                "volume": round_decimal(brg.get("volume"), 4),
                "ndpbm": round_decimal(brg.get("ndpbm"), 4),
                "cifRupiah": round_decimal(brg.get("cif_rupiah"), 2),
                "kodeAsalBahanBaku": brg.get("kode_dokumen_asal") or "",
                "barangTarif": []
            }
            # BARANG TARIF
            for t in brg_doc.get("barang_tarif") or []:
                brg_item["barangTarif"].append({
                    "kodeJenisTarif": t.get("kode_tarif") or "1",
                    "jumlahSatuan": round_decimal(t.get("jumlah_satuan"), 4),
                    "kodeFasilitasTarif": t.get("kode_fasilitas") or "",
                    "kodeSatuanBarang": t.get("kode_satuan") or "",
                    "kodeJenisPungutan": get_kode_pungutan(t.get("kode_pungutan")),
                    "nilaiBayar": round_decimal(t.get("nilai_bayar"), 2),
                    "nilaiFasilitas": round_decimal(t.get("nilai_fasilitas"), 2),
                    "nilaiSudahDilunasi": round_decimal(t.get("nilai_sudah_dilunasi"), 2) or 0,
                    "seriBarang": cint(brg.get("seri_barang")) or 0,
                    "tarif": round_decimal(t.get("tarif"), 2),
                    "tarifFasilitas": round_decimal(t.get("tarif_fasilitas"), 2)
                })
            payload["Declaration"]["barang"].append(brg_item)
        return payload
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get CEISA FTZ011 JSON Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_ceisa_ftz012_json(nomor_aju):
    """Export HEADER V21 to FTZ01-2 (PPFTZ to LDP) JSON format"""
    try:
        doc = frappe.get_doc("HEADER V21", nomor_aju)
        payload = {
            "Declaration": {
                "asalData": "S",
                "asuransi": round_decimal(doc.get("asuransi"), 2),
                "bruto": round_decimal(doc.get("bruto"), 4),
                "cif": round_decimal(doc.get("cif"), 2),
                "fob": round_decimal(doc.get("fob"), 2),
                "freight": round_decimal(doc.get("freight"), 2),
                "jabatanTtd": doc.get("jabatan_pernyataan") or "",
                "jumlahKontainer": len(doc.get("kontainer") or []),
                "kodeAsalBarangFtz": doc.get("kode_barang_asal_ftz") or "1",
                "kodeAsuransi": doc.get("kode_asuransi") or "DN",
                "kodeCaraBayar": doc.get("kode_cara_bayar") or "",
                "kodeCaraDagang": doc.get("kode_cara_dagang") or "",
                "kodeDokumen": "512",
                "kodeIncoterm": doc.get("kode_incoterm") or "",
                "kodeKantor": doc.get("kode_kantor") or "",
                "kodeJenisProsedur": doc.get("kode_jenis_prosedur") or "1",
                "kodeKategoriKeluarFtz": doc.get("kode_kategori_keluar_ftz") or "",
                "kodePelMuat": doc.get("kode_pelabuhan_muat") or "",
                "kodePelTransit": doc.get("kode_pelabuhan_transit") or "",
                "kodePelTujuan": doc.get("kode_pelabuhan_tujuan") or "",
                "kodeTps": doc.get("kode_tps") or "",
                "kodeTujuanPengiriman": doc.get("kode_tujuan_pengiriman") or "",
                "kodeValuta": doc.get("kode_valuta") or "IDR",
                "kotaTtd": doc.get("kota_pernyataan") or "",
                "namaTtd": doc.get("nama_pernyataan") or "",
                "ndpbm": round_decimal(doc.get("ndpbm"), 4),
                "netto": round_decimal(doc.get("netto"), 4),
                "nomorAju": doc.get("nomoraju") or doc.name or "",
                "seri": 0,
                "tanggalTtd": fmt_date(doc.get("tanggal_pernyataan")),
                "volume": round_decimal(doc.get("volume"), 4),
                "biayaTambahan": round_decimal(doc.get("biaya_tambahan"), 2),
                "biayaPengurang": round_decimal(doc.get("biaya_pengurang"), 2),
                "entitas": get_child_data(doc, "entitas", {
                    "alamatEntitas": "alamat_entitas",
                    "kodeEntitas": "kode_entitas",
                    "kodeJenisApi": "kode_jenis_api",
                    "kodeJenisIdentitas": "kode_jenis_identitas",
                    "kodeNegara": "kode_negara",
                    "kodeStatus": "kode_status",
                    "namaEntitas": "nama_entitas",
                    "nomorIdentitas": "nomor_identitas",
                    "seriEntitas": "seri"
                }),
                "kemasan": get_child_data(doc, "kemasan", {
                    "jumlahKemasan": "jumlah_kemasan",
                    "kodeJenisKemasan": "kode_kemasan",
                    "merkKemasan": "merek_kemasan",
                    "seriKemasan": "seri"
                }),
                "kontainer": get_child_data(doc, "kontainer", {
                    "kodeJenisKontainer": "kode_jenis_kontainer",
                    "kodeTipeKontainer": "kode_tipe_kontainer",
                    "kodeUkuranKontainer": "kode_ukuran_kontainer",
                    "nomorKontainer": "nomor_kontainer",
                    "seriKontainer": "seri"
                }),
                "dokumen": get_child_data(doc, "dokumen", {
                    "kodeDokumen": "kode_dokumen",
                    "nomorDokumen": "nomor_dokumen",
                    "seriDokumen": "seri",
                    "tanggalDokumen": "tanggal_dokumen"
                }),
                "pengangkut": get_child_data(doc, "pengangkut", {
                    "namaPengangkut": "nama_pengangkut",
                    "nomorPengangkut": "nomor_pengangkut",
                    "seriPengangkut": "seri_pengangkut",
                    "kodeCaraAngkut": "kode_cara_angkut",
                    "kodeBendera": "kode_bendera"
                }),
                "barang": []
            }
        }
        for brg in frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc"):
            brg_doc = frappe.get_doc("BARANG V1", brg.get("name"))
            brg_item = {
                "idBarang": "",
                "asuransi": round_decimal(brg.get("asuransi"), 2),
                "bruto": round_decimal(brg.get("bruto"), 4),
                "cif": round_decimal(brg.get("cif"), 2),
                "fob": round_decimal(brg.get("fob"), 2),
                "freight": round_decimal(brg.get("freight"), 2),
                "hargaPenyerahan": round_decimal(brg.get("harga_penyerahan"), 4),
                "hargaSatuan": round_decimal(brg.get("harga_satuan"), 4),
                "isiPerKemasan": round_decimal(brg.get("isi_per_kemasan"), 2),
                "jumlahKemasan": round_decimal(brg.get("jumlah_kemasan"), 2),
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4),
                "kodeJenisKemasan": brg.get("kode_kemasan") or "",
                "kodeNegaraAsal": brg.get("kode_negara_asal") or "",
                "kodeSatuanBarang": brg.get("kode_satuan") or "",
                "merk": clean_merk_tipe(brg.get("merek")),
                "netto": round_decimal(brg.get("netto"), 4),
                "posTarif": brg.get("hs") or "",
                "seriBarang": cint(brg.get("seri_barang")) or 0,
                "spesifikasiLain": brg.get("spesifikasi_lain") or "",
                "tipe": clean_merk_tipe(brg.get("tipe")),
                "ukuran": brg.get("ukuran") or "",
                "uraian": brg.get("uraian") or "",
                "volume": round_decimal(brg.get("volume"), 4),
                "ndpbm": round_decimal(brg.get("ndpbm"), 4),
                "cifRupiah": round_decimal(brg.get("cif_rupiah"), 2),
                "kodeAsalBahanBaku": brg.get("kode_dokumen_asal") or "",
                "barangTarif": []
            }
            # BARANG TARIF
            for t in brg_doc.get("barang_tarif") or []:
                brg_item["barangTarif"].append({
                    "kodeJenisTarif": t.get("kode_tarif") or "1",
                    "jumlahSatuan": round_decimal(t.get("jumlah_satuan"), 4),
                    "kodeFasilitasTarif": t.get("kode_fasilitas") or "",
                    "kodeSatuanBarang": t.get("kode_satuan") or "",
                    "kodeJenisPungutan": get_kode_pungutan(t.get("kode_pungutan")),
                    "nilaiBayar": round_decimal(t.get("nilai_bayar"), 2),
                    "nilaiFasilitas": round_decimal(t.get("nilai_fasilitas"), 2),
                    "nilaiSudahDilunasi": round_decimal(t.get("nilai_sudah_dilunasi"), 2) or 0,
                    "seriBarang": cint(brg.get("seri_barang")) or 0,
                    "tarif": round_decimal(t.get("tarif"), 2),
                    "tarifFasilitas": round_decimal(t.get("tarif_fasilitas"), 2)
                })
            payload["Declaration"]["barang"].append(brg_item)
        return payload
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get CEISA FTZ012 JSON Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_ceisa_ftz013_json(nomor_aju):
    """Export HEADER V21 to FTZ01-3 (PPFTZ to TLDDP) JSON format"""
    try:
        doc = frappe.get_doc("HEADER V21", nomor_aju)
        payload = {
            "Declaration": {
                "asalData": "S",
                "status": "1",
                "asuransi": round_decimal(doc.get("asuransi"), 2),
                "bruto": round_decimal(doc.get("bruto"), 4),
                "cif": round_decimal(doc.get("cif"), 2),
                "fob": round_decimal(doc.get("fob"), 2),
                "freight": round_decimal(doc.get("freight"), 2),
                "jabatanTtd": doc.get("jabatan_pernyataan") or "",
                "jumlahKontainer": len(doc.get("kontainer") or []),
                "kodeAsalBarangFtz": doc.get("kode_barang_asal_ftz") or "1",
                "kodeAsuransi": doc.get("kode_asuransi") or "DN",
                "kodeCaraBayar": doc.get("kode_cara_bayar") or "",
                "kodeCaraDagang": doc.get("kode_cara_dagang") or "",
                "kodeDokumen": "513",
                "kodeIncoterm": doc.get("kode_incoterm") or "",
                "kodeKantor": doc.get("kode_kantor") or "",
                "kodeKategoriBarangFtz": doc.get("kode_kategori_barang_ftz") or "",
                "kodeKategoriKeluarFtz": doc.get("kode_kategori_keluar_ftz") or "",
                "kodePelMuat": doc.get("kode_pelabuhan_muat") or "",
                "kodePelTransit": doc.get("kode_pelabuhan_transit") or "",
                "kodePelTujuan": doc.get("kode_pelabuhan_tujuan") or "",
                "kodeTps": doc.get("kode_tps") or "",
                "kodeTujuanPengiriman": doc.get("kode_tujuan_pengiriman") or "",
                "kodeTujuanPengeluaran": doc.get("kode_tujuan_pengeluaran") or "",
                "kodeTutupPu": doc.get("kode_tutup_pu") or "",
                "kodeValuta": doc.get("kode_valuta") or "",
                "kotaTtd": doc.get("kota_pernyataan") or "",
                "namaTransaksiLainnyaFtz": doc.get("nama_transaksi_lainnya_ftz") or "",
                "namaTtd": doc.get("nama_pernyataan") or "",
                "ndpbm": round_decimal(doc.get("ndpbm"), 4),
                "netto": round_decimal(doc.get("netto"), 4),
                "nomorAju": doc.get("nomoraju") or doc.name or "",
                "nomorBc11": doc.get("nomor_bc11") or "",
                "posBc11": doc.get("nomor_pos") or "",
                "seri": 0,
                "subposBc11": doc.get("nomor_sub_pos") or "",
                "tanggalBc11": fmt_date(doc.get("tanggal_bc11")),
                "tanggalTiba": fmt_date(doc.get("tanggal_tiba")),
                "tanggalTtd": fmt_date(doc.get("tanggal_pernyataan")),
                "volume": round_decimal(doc.get("volume"), 4),
                "biayaTambahan": round_decimal(doc.get("biaya_tambahan"), 2),
                "biayaPengurang": round_decimal(doc.get("biaya_pengurang"), 2),
                "entitas": get_child_data(doc, "entitas", {
                    "alamatEntitas": "alamat_entitas",
                    "kodeEntitas": "get_kode_entitas", # uses special logic in loop below
                    "kodeJenisApi": "kode_jenis_api",
                    "kodeJenisIdentitas": "kode_jenis_identitas",
                    "kodeNegara": "kode_negara",
                    "kodeStatus": "kode_status",
                    "namaEntitas": "nama_entitas",
                    "nomorIdentitas": "nomor_identitas",
                    "seriEntitas": "seri"
                }),
                "kemasan": get_child_data(doc, "kemasan", {
                    "jumlahKemasan": "jumlah_kemasan",
                    "kodeJenisKemasan": "kode_kemasan",
                    "merkKemasan": "merek_kemasan",
                    "seriKemasan": "seri"
                }),
                "kontainer": get_child_data(doc, "kontainer", {
                    "kodeJenisKontainer": "kode_jenis_kontainer",
                    "kodeTipeKontainer": "kode_tipe_kontainer",
                    "kodeUkuranKontainer": "kode_ukuran_kontainer",
                    "nomorKontainer": "nomor_kontainer",
                    "seriKontainer": "seri"
                }),
                "dokumen": get_child_data(doc, "dokumen", {
                    "kodeDokumen": "kode_dokumen",
                    "nomorDokumen": "nomor_dokumen",
                    "seriDokumen": "seri",
                    "tanggalDokumen": "tanggal_dokumen"
                }),
                "pengangkut": get_child_data(doc, "pengangkut", {
                    "namaPengangkut": "nama_pengangkut",
                    "nomorPengangkut": "nomor_pengangkut",
                    "seriPengangkut": "seri_pengangkut",
                    "kodeCaraAngkut": "kode_cara_angkut",
                    "kodeBendera": "kode_bendera"
                }),
                "barang": []
            }
        }
        decl = payload["Declaration"]
        
        # Adjust entitas codes manually if needed (get_child_data already handles some but let's be sure)
        for ent in decl["entitas"]:
             ent["kodeEntitas"] = get_kode_entitas(ent.get("kodeEntitas"))
             ent["kodeJenisIdentitas"] = get_kode_identitas(ent.get("kodeJenisIdentitas"))

        # Barang V1
        for brg in frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc"):
            brg_doc = frappe.get_doc("BARANG V1", brg.get("name"))
            brg_item = {
                "idBarang": "",
                "asuransi": round_decimal(brg.get("asuransi"), 2),
                "bruto": round_decimal(brg.get("bruto"), 4),
                "cif": round_decimal(brg.get("cif"), 2),
                "fob": round_decimal(brg.get("fob"), 2),
                "freight": round_decimal(brg.get("freight"), 2),
                "hargaPenyerahan": round_decimal(brg.get("harga_penyerahan"), 4),
                "hargaSatuan": round_decimal(brg.get("harga_satuan"), 4),
                "isiPerKemasan": round_decimal(brg.get("isi_per_kemasan"), 2),
                "jumlahKemasan": round_decimal(brg.get("jumlah_kemasan"), 2),
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4),
                "kodeJenisKemasan": brg.get("kode_kemasan") or "",
                "kodeNegaraAsal": brg.get("kode_negara_asal") or "",
                "kodeSatuanBarang": brg.get("kode_satuan") or "",
                "merk": clean_merk_tipe(brg.get("merek")),
                "netto": round_decimal(brg.get("netto"), 4),
                "posTarif": brg.get("hs") or "",
                "seriBarang": cint(brg.get("seri_barang")) or 0,
                "spesifikasiLain": brg.get("spesifikasi_lain") or "",
                "tipe": clean_merk_tipe(brg.get("tipe")),
                "ukuran": brg.get("ukuran") or "",
                "uraian": brg.get("uraian") or "",
                "volume": round_decimal(brg.get("volume"), 4),
                "ndpbm": round_decimal(brg.get("ndpbm"), 4),
                "cifRupiah": round_decimal(brg.get("cif_rupiah"), 2),
                "barangTarif": []
            }
            # BARANG TARIF
            for t in brg_doc.get("barang_tarif") or []:
                brg_item["barangTarif"].append({
                    "kodeJenisTarif": t.get("kode_tarif") or "1",
                    "jumlahSatuan": round_decimal(t.get("jumlah_satuan"), 4),
                    "kodeFasilitasTarif": t.get("kode_fasilitas") or "",
                    "kodeSatuanBarang": t.get("kode_satuan") or "",
                    "kodeJenisPungutan": get_kode_pungutan(t.get("kode_pungutan")),
                    "nilaiBayar": round_decimal(t.get("nilai_bayar"), 2),
                    "nilaiFasilitas": round_decimal(t.get("nilai_fasilitas"), 2),
                    "nilaiSudahDilunasi": round_decimal(t.get("nilai_sudah_dilunasi"), 2) or 0,
                    "seriBarang": cint(brg.get("seri_barang")) or 0,
                    "tarif": round_decimal(t.get("tarif"), 2),
                    "tarifFasilitas": round_decimal(t.get("tarif_fasilitas"), 2)
                })
            decl["barang"].append(brg_item)

        return payload
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get CEISA FTZ013 JSON Error")
        return {"status": "error", "message": str(e)}


# =====================================
# JSON Schema Validation Functions
# =====================================

BC20_SCHEMA_PATH = "/home/acer25/frappe-bench/base erp xls/BC20 SCHEMA"
BC23_SCHEMA_PATH = "/home/acer25/frappe-bench/base erp xls/BC23 SCHEMA"
BC25_SCHEMA_PATH = "/home/acer25/frappe-bench/base erp xls/BC25 SCHEMA"
BC27_SCHEMA_PATH = "/home/acer25/frappe-bench/base erp xls/BC27 SCHEMA"
BC30_SCHEMA_PATH = "/home/acer25/frappe-bench/base erp xls/BC30 SCHEMA"
BC33_SCHEMA_PATH = "/home/acer25/frappe-bench/base erp xls/BC33 SCHEMA"
BC40_SCHEMA_PATH = "/home/acer25/frappe-bench/base erp xls/BC40 SCHEMA"
BC41_SCHEMA_PATH = "/home/acer25/frappe-bench/base erp xls/BC41 SCHEMA"
BC262_SCHEMA_PATH = "/home/acer25/frappe-bench/base erp xls/BC262 SCHEMA"
FTZ013_SCHEMA_PATH = "/home/acer25/frappe-bench/base erp xls/FTZ01-3"
BC261_SCHEMA_PATH = "/home/acer25/frappe-bench/base erp xls/BC261 SCHEMA"
FTZ012_SCHEMA_PATH = "/home/acer25/frappe-bench/base erp xls/FTZ01-2"
FTZ011_SCHEMA_PATH = "/home/acer25/frappe-bench/base erp xls/FTZ01-1"
BC16_SCHEMA_PATH = "/home/acer25/frappe-bench/base erp xls/BC16 SCHEMA"
BC28_SCHEMA_PATH = "/home/acer25/frappe-bench/base erp xls/BC28 SCHEMA"
P3BET_SCHEMA_PATH = "/home/acer25/frappe-bench/base erp xls/P3BET SCHEMA"



# Load Schemas
def load_bc_schema(path):
    try:
        if not os.path.exists(path):
            frappe.log_error(f"Schema file not found: {path}", "Schema Load Error")
            return None
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Extract JSON block - skip documentation tags like {% hint %}
            # Find the first { that is not followed by %
            start = -1
            for i in range(len(content)):
                if content[i] == '{' and (i + 1 == len(content) or content[i+1] != '%'):
                    start = i
                    break
            
            end = content.rfind("}")
            if start != -1 and end != -1:
                content = content[start:end+1]
            return json.loads(content)
    except Exception as e:
        frappe.log_error(f"Failed to load schema {path}: {str(e)}", "Schema Load Error")
        return None

# Unified Validation Handler
def test_bc_json_schema(output_json_string, bc_type):
    import jsonschema
    from jsonschema import Draft7Validator
    
    schema_map = {
        "16": BC16_SCHEMA_PATH, "20": BC20_SCHEMA_PATH, "23": BC23_SCHEMA_PATH, "25": BC25_SCHEMA_PATH,
        "27": BC27_SCHEMA_PATH, "28": BC28_SCHEMA_PATH, "30": BC30_SCHEMA_PATH, "33": BC33_SCHEMA_PATH,
        "40": BC40_SCHEMA_PATH, "41": BC41_SCHEMA_PATH, "261": BC261_SCHEMA_PATH, "262": BC262_SCHEMA_PATH,
        "511": FTZ011_SCHEMA_PATH, "512": FTZ012_SCHEMA_PATH, "513": FTZ013_SCHEMA_PATH,
        "331": P3BET_SCHEMA_PATH
    }
    
    path = schema_map.get(bc_type)
    if not path: return {"valid": False, "error": f"Unsupported BC type: {bc_type}"}
    schema = load_bc_schema(path)
    if not schema: return {"valid": False, "error": f"Failed to load schema for BC{bc_type}"}
    
    try:
        data = json.loads(output_json_string)
    except Exception as e:
        return {"valid": False, "error": f"Invalid JSON: {str(e)}"}

    def custom_multipleOf(validator, multipleOf, instance, schema):
        if not isinstance(instance, (int, float, Decimal)):
            return
        try:
            val = Decimal(str(instance))
            mult = Decimal(str(multipleOf))
            if val % mult != 0:
                yield jsonschema.ValidationError(f"{instance} is not a multiple of {multipleOf}")
        except:
            yield jsonschema.ValidationError(f"Invalid numeric value for multipleOf check: {instance}")

    CustomValidator = jsonschema.validators.extend(Draft7Validator, {"multipleOf": custom_multipleOf})

    try:
        validator = CustomValidator(schema)
        errors = list(validator.iter_errors(data))
        if errors:
            formatted_errors = []
            for e in errors:
                try:
                    path_str = " → ".join(str(p) for p in e.absolute_path) if getattr(e, "absolute_path", None) else "Root"
                    formatted_errors.append({
                        "message": str(e.message) if hasattr(e, "message") else str(e),
                        "path": path_str
                    })
                except:
                    formatted_errors.append({"message": str(e), "path": "Unknown"})
            return {"valid": False, "errors": formatted_errors}
        return {"valid": True, "message": f"✅ JSON is BC{bc_type} Schema compliant"}
    except Exception as e:
        import traceback
        frappe.log_error(traceback.format_exc(), "Schema Validation Internal Error")
        return {"valid": False, "error": f"Internal Validation Error: {str(e)}"}

# Legacy compatibility wrappers
@frappe.whitelist()
def test_bc20_json_schema(output_json_string): return test_bc_json_schema(output_json_string, "20")

# API Export Validators
@frappe.whitelist()
def validate_bc20_export(nomor_aju):
    res = get_ceisa_bc20_json(nomor_aju)
    return test_bc_json_schema(json.dumps(res, default=str), "20") if not (isinstance(res, dict) and res.get("status") == "error") else {"valid": False, "error": res.get("message")}

@frappe.whitelist()
def validate_bc23_export(nomor_aju):
    res = get_ceisa_bc23_json(nomor_aju)
    return test_bc_json_schema(json.dumps(res, default=str), "23") if not (isinstance(res, dict) and res.get("status") == "error") else {"valid": False, "error": res.get("message")}

@frappe.whitelist()
def validate_bc25_export(nomor_aju):
    res = get_ceisa_bc25_json(nomor_aju)
    return test_bc_json_schema(json.dumps(res, default=str), "25") if not (isinstance(res, dict) and res.get("status") == "error") else {"valid": False, "error": res.get("message")}

@frappe.whitelist()
def validate_bc27_export(nomor_aju):
    res = get_ceisa_bc27_json(nomor_aju)
    return test_bc_json_schema(json.dumps(res, default=str), "27") if not (isinstance(res, dict) and res.get("status") == "error") else {"valid": False, "error": res.get("message")}

@frappe.whitelist()
def validate_bc30_export(nomor_aju):
    res = get_ceisa_bc30_json(nomor_aju)
    return test_bc_json_schema(json.dumps(res, default=str), "30") if not (isinstance(res, dict) and res.get("status") == "error") else {"valid": False, "error": res.get("message")}

@frappe.whitelist()
def validate_bc33_export(nomor_aju):
    res = get_ceisa_bc33_json(nomor_aju)
    return test_bc_json_schema(json.dumps(res, default=str), "33") if not (isinstance(res, dict) and res.get("status") == "error") else {"valid": False, "error": res.get("message")}

@frappe.whitelist()
def validate_bc40_export(nomor_aju):
    res = get_ceisa_bc40_json(nomor_aju)
    return test_bc_json_schema(json.dumps(res, default=str), "40") if not (isinstance(res, dict) and res.get("status") == "error") else {"valid": False, "error": res.get("message")}

@frappe.whitelist()
def validate_bc41_export(nomor_aju):
    res = get_ceisa_bc41_json(nomor_aju)
    return test_bc_json_schema(json.dumps(res, default=str), "41") if not (isinstance(res, dict) and res.get("status") == "error") else {"valid": False, "error": res.get("message")}

@frappe.whitelist()
def validate_bc262_export(nomor_aju):
    res = get_ceisa_bc262_json(nomor_aju)
    return test_bc_json_schema(json.dumps(res, default=str), "262") if not (isinstance(res, dict) and res.get("status") == "error") else {"valid": False, "error": res.get("message")}

@frappe.whitelist()
def validate_bc16_export(nomor_aju):
    res = get_ceisa_bc16_json(nomor_aju)
    return test_bc_json_schema(json.dumps(res, default=str), "16") if not (isinstance(res, dict) and res.get("status") == "error") else {"valid": False, "error": res.get("message")}

@frappe.whitelist()
def validate_bc28_export(nomor_aju):
    res = get_ceisa_bc28_json(nomor_aju)
    return test_bc_json_schema(json.dumps(res, default=str), "28") if not (isinstance(res, dict) and res.get("status") == "error") else {"valid": False, "error": res.get("message")}

@frappe.whitelist()
def validate_bc261_export(nomor_aju):
    res = get_ceisa_bc261_json(nomor_aju)
    return test_bc_json_schema(json.dumps(res, default=str), "261") if not (isinstance(res, dict) and res.get("status") == "error") else {"valid": False, "error": res.get("message")}

@frappe.whitelist()
def validate_ftz011_export(nomor_aju):
    res = get_ceisa_ftz011_json(nomor_aju)
    return test_bc_json_schema(json.dumps(res, default=str), "511") if not (isinstance(res, dict) and res.get("status") == "error") else {"valid": False, "error": res.get("message")}

@frappe.whitelist()
def validate_ftz012_export(nomor_aju):
    res = get_ceisa_ftz012_json(nomor_aju)
    return test_bc_json_schema(json.dumps(res, default=str), "512") if not (isinstance(res, dict) and res.get("status") == "error") else {"valid": False, "error": res.get("message")}

@frappe.whitelist()
def validate_p3bet_export(nomor_aju):
    res = get_ceisa_p3bet_json(nomor_aju)
    return test_bc_json_schema(json.dumps(res, default=str), "331") if not (isinstance(res, dict) and res.get("status") == "error") else {"valid": False, "error": res.get("message")}

@frappe.whitelist()
def validate_ftz013_export(nomor_aju):
    res = get_ceisa_ftz013_json(nomor_aju)
    return test_bc_json_schema(json.dumps(res, default=str), "513") if not (isinstance(res, dict) and res.get("status") == "error") else {"valid": False, "error": res.get("message")}


# =====================================
# CEISA Export Map (single source of truth)
# Used by: check_export_with_ceisa (below)
#          ceisa_integration.send_ceisa_document (imports this constant)
# =====================================

CEISA_EXPORT_MAP = {
    "16":  get_ceisa_bc16_json,
    "20":  get_ceisa_bc20_json,
    "23":  get_ceisa_bc23_json,
    "25":  get_ceisa_bc25_json,
    "27":  get_ceisa_bc27_json,
    "28":  get_ceisa_bc28_json,
    "30":  get_ceisa_bc30_json,
    "33":  get_ceisa_bc33_json,
    "40":  get_ceisa_bc40_json,
    "41":  get_ceisa_bc41_json,
    "261": get_ceisa_bc261_json,
    "262": get_ceisa_bc262_json,
    "511": get_ceisa_ftz011_json,
    "512": get_ceisa_ftz012_json,
    "513": get_ceisa_ftz013_json,
    "331": get_ceisa_p3bet_json,
}


# =====================================
# CEISA Live Document Check (via API)
# =====================================

@frappe.whitelist()
def check_export_with_ceisa(nomor_aju, bc_type):
    """
    Generate JSON for the given HEADER V21 document and validate it
    against the live CEISA /openapi/document/check endpoint.

    Args:
        nomor_aju  : Name/ID of the HEADER V21 document
        bc_type    : Document type code string, e.g. '20', '23', '25', '27',
                     '28', '30', '33', '40', '41', '261', '262', '16',
                     '511', '512', '513', '331'

    Returns:
        dict with keys: status, http_code, data  (from check_document)
             or        : valid=False + error message on generation failure
    """
    from singlecore_apps.api.ceisa_api.document import check_document

    bc_type = str(bc_type)
    fn = CEISA_EXPORT_MAP.get(bc_type)
    if not fn:
        return {"valid": False, "error": f"Unsupported BC type: {bc_type}"}

    res = fn(nomor_aju)
    if isinstance(res, dict) and res.get("status") == "error":
        return {"valid": False, "error": res.get("message", "Failed to generate JSON")}

    return check_document(res)
