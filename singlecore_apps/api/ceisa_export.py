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
            return float(d.get("quantize")(Decimal('0.01'), rounding=ROUND_HALF_UP))
        elif decimals == 4:
            return float(d.get("quantize")(Decimal('0.0001'), rounding=ROUND_HALF_UP))
        else:
            return float(round(flt(value), decimals))
    except:
        return 0.0

# Helper to format date
def fmt_date(date_obj):
    if not date_obj: return ""
    return str(date_obj)

# Helper to get child table data
def get_child_data(doc, child_table_name, fields_map):
    data = []
    for child in (doc.get(child_table_name) or []):
        item = {}
        for json_field, doc_field in fields_map.items():
            val = child.get(doc_field)
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
            "asalData": "S",  # Schema requires constant "S"
            "asuransi": round_decimal(doc.get("asuransi"), 2),
            "bruto": round_decimal(doc.get("bruto"), 4),
            "cif": round_decimal(doc.get("cif"), 2),
            "dasarPengenaanPajak": round_decimal(doc.get("dasar_pengenaan_pajak"), 2),
            "disclaimer": doc.get("disclaimer") or "1",
            "freight": round_decimal(doc.get("freight"), 2),
            "hargaPenyerahan": round_decimal(doc.get("harga_penyerahan"), 4),
            "jabatanTtd": doc.get("jabatan_pernyataan") or "",
            "jumlahKontainer": len( (doc.get("kontainer") or [])),
            "kodeDokumen": "27",  # Schema requires constant "27"
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
            "netto": round_decimal(doc.get("netto"), 4),
            "nik": "",  # NIK field - may need to be added to DocType
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

        # 2. Map Entitas (BC27 structure)
        payload["entitas"] = []
        for ent in (doc.get("entitas") or []):
            payload["entitas"].append({
                "alamatEntitas": ent.get("alamat_entitas") or "",
                "kodeEntitas": ent.get("kode_entitas") or "",
                "kodeJenisIdentitas": ent.get("kode_jenis_identitas") or "",
                "namaEntitas": ent.get("nama_entitas") or "",
                "nibEntitas": ent.get("nib_entitas") or "",
                "nomorIdentitas": ent.get("nomor_identitas") or "",
                "nomorIjinEntitas": ent.get("nomor_ijin_entitas") or "",
                "seriEntitas": ent.get("seri") or 0,
                "tanggalIjinEntitas": fmt_date(ent.get("tanggal_ijin_entitas")),
                "kodeJenisApi": ent.get("kode_jenis_api") or "",
                "kodeStatus": ent.get("kode_status") or "",
            })

        # 3. Map Dokumen
        payload["dokumen"] = []
        for dok in (doc.get("dokumen") or []):
            payload["dokumen"].append({
                "idDokumen": "",
                "kodeDokumen": dok.get("kode_dokumen") or "",
                "nomorDokumen": dok.get("nomor_dokumen") or "",
                "seriDokumen": dok.get("seri") or 0,
                "tanggalDokumen": fmt_date(dok.get("tanggal_dokumen")),
            })

        # 4. Map Pengangkut (BC27 - simpler structure)
        payload["pengangkut"] = []
        for peng in (doc.get("pengangkut") or []):
            payload["pengangkut"].append({
                "namaPengangkut": peng.nama_pengangkut or "",
                "nomorPengangkut": peng.nomor_pengangkut or "",
                "seriPengangkut": peng.seri_pengangkut or 0,
            })

        # 5. Map Kemasan
        payload["kemasan"] = []
        for kem in (doc.get("kemasan") or []):
            payload["kemasan"].append({
                "jumlahKemasan": round_decimal(kem.get("jumlah_kemasan"), 2),
                "kodeJenisKemasan": kem.get("kode_kemasan") or "",
                "merkKemasan": kem.get("merek_kemasan") or "",
                "seriKemasan": kem.get("seri") or 0,
            })

        # 6. Map Kontainer
        payload["kontainer"] = []
        for kon in (doc.get("kontainer") or []):
            payload["kontainer"].append({
                "seriKontainer": kon.get("seri") or 0,
                "nomorKontainer": kon.get("nomor_kontainer") or "",
                "kodeUkuranKontainer": kon.get("kode_ukuran_kontainer") or "",
                "kodeJenisKontainer": kon.get("kode_jenis_kontainer") or "",
                "kodeTipeKontainer": kon.get("kode_tipe_kontainer") or "",
            })

        # 7. Map Pungutan (BC27 specific)
        payload["pungutan"] = []
        for pung in (doc.get("pungutan") or []):
            payload["pungutan"].append({
                "idPungutan": "",
                "kodeFasilitasTarif": pung.kode_fasilitas_tarif or "",
                "kodeJenisPungutan": pung.kode_jenis_pungutan or "",
                "nilaiPungutan": round_decimal(pung.nilai_pungutan, 2),
            })

        # 8. Map Barang V1 (BC27 structure)
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
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4),
                "kodeBarang": brg.get("kode_barang") or "",
                "kodeDokumen": "",
                "kodeKategoriBarang": brg.get("kode_kategori_barang") or "",
                "kodeSatuanBarang": brg.get("kode_satuan") or "",
                "merk": brg.get("merek") or "",
                "ndpbm": round_decimal(brg.get("ndpbm"), 4),
                "netto": round_decimal(brg.get("netto"), 4),
                "nilaiBarang": round_decimal(brg.get("nilai_barang"), 2),
                "nilaiJasa": round_decimal(brg.get("nilai_jasa"), 2),
                "posTarif": brg.get("hs") or "",
                "seriBarang": brg.get("seri_barang") or 0,
                "spesifikasiLain": brg.get("spesifikasi_lain") or "",
                "tipe": brg.get("tipe") or "",
                "uangMuka": 0,  # Field may need to be added to DocType
                "ukuran": brg.get("ukuran") or "",
                "uraian": brg.get("uraian") or "",
            }
            
            # BAHAN BAKU (BC27 structure)
            brg_item["bahanBaku"] = []
            bahan_bakus = frappe.get_all("BAHAN BAKU", 
                filters={"parent_barang": brg.get("name")}, 
                fields=["*"],
                order_by="seri_bahan_baku asc"
            )
            for bb in bahan_bakus:
                bb_doc = frappe.get_doc("BAHAN BAKU", bb.get("name"))
                bb_item = {
                    "cif": round_decimal(bb.get("cif"), 2),
                    "cifRupiah": round_decimal(bb.get("cif_rupiah"), 2),
                    "hargaPenyerahan": round_decimal(bb.get("harga_penyerahan"), 4),
                    "hargaPerolehan": round_decimal(bb.get("harga_perolehan"), 2),
                    "jumlahSatuan": round_decimal(bb.get("jumlah_satuan"), 4),
                    "kodeAsalBahanBaku": bb.get("kode_asal_bahan_baku") or "",
                    "kodeBarang": bb.get("kode_barang") or "",
                    "kodeDokAsal": bb.get("kode_dokumen_asal") or "",
                    "kodeKantor": bb.get("kode_kantor_asal") or "",
                    "kodeSatuanBarang": bb.get("kode_satuan") or "",
                    "merkBarang": bb.get("merek") or "",
                    "ndpbm": round_decimal(bb.get("ndpbm"), 4),
                    "netto": round_decimal(bb.get("netto"), 4),
                    "nilaiJasa": 0,  # Field may need to be added
                    "nomorAjuDokAsal": bb.get("nomor_aju_asal") or "",
                    "nomorDaftarDokAsal": bb.get("nomor_daftar_asal") or "",
                    "posTarif": bb.get("hs") or "",
                    "seriBahanBaku": bb.get("seri_bahan_baku") or 0,
                    "seriBarang": brg.get("seri_barang") or 0,
                    "seriBarangDokAsal": bb.get("seri_barang_asal") or 0,
                    "seriIjin": 0,  # Field may need to be added
                    "spesifikasiLainBarang": bb.get("spesifikasi_lain") or "",
                    "tanggalDaftarDokAsal": fmt_date(bb.get("tanggal_daftar_asal")),
                    "tipeBarang": bb.get("tipe") or "",
                    "ukuranBarang": bb.get("ukuran") or "",
                    "uraianBarang": bb.get("uraian") or "",
                }
                
                # BahanBakuTarif
                bb_item["bahanBakuTarif"] = []
                for bbt in bb_doc.get("bahan_tarif") or []:
                    bb_item["bahanBakuTarif"].append({
                        "seriBahanBaku": bb.get("seri_bahan_baku") or 0,
                        "kodeJenisPungutan": bbt.kode_pungutan or "",
                        "kodeAsalBahanBaku": bbt.kode_asal_bahan_baku or bb.get("kode_asal_bahan_baku") or "",
                        "kodeFasilitasTarif": bbt.kode_fasilitas or "",
                        "nilaiBayar": round_decimal(bbt.nilai_bayar, 2),
                        "nilaiFasilitas": round_decimal(bbt.nilai_fasilitas, 2),
                        "nilaiSudahDilunasi": round_decimal(bbt.nilai_sudah_dilunasi, 2) or 0,
                        "tarif": round_decimal(bbt.tarif, 2),
                        "tarifFasilitas": round_decimal(bbt.tarif_fasilitas, 2),
                        "jumlahSatuan": round_decimal(bbt.jumlah_satuan, 4),
                        "kodeJenisTarif": bbt.kode_tarif or "",
                        "jumlahKemasan": 0,
                    })
                
                brg_item["bahanBaku"].append(bb_item)

            barang_list.append(brg_item)

        payload["barang"] = barang_list
        
        return {"Declaration": payload}

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
            "idPengguna": "",  # String, empty default
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
            "ndpbm": round_decimal(doc.get("ndpbm"), 4),  # multipleOf 0.0001
            "netto": round_decimal(doc.get("netto"), 4),  # multipleOf 0.0001
            "nilaiMaklon": round_decimal(doc.get("nilai_maklon"), 2),  # multipleOf 0.01
            "seri": 0, 
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

        # 2. Map Child Tables (Entitas, Kemasan, Dokumen, Pengangkut)
        payload["entitas"] = get_child_data(doc, "entitas", {
            "alamatEntitas": "alamat_entitas",
            "kodeEntitas": "kode_entitas",
            "kodeJenisIdentitas": "kode_jenis_identitas",
            "namaEntitas": "nama_entitas",
            "nibEntitas": "nib_entitas",
            "nomorIdentitas": "nomor_identitas",
            "kodeStatus": "kode_status",
            "seriEntitas": "seri",  # DocType uses 'seri' not 'seri_entitas'
            "kodeJenisApi": "kode_jenis_api",
            "kodeNegara": "kode_negara",
            "kodeAfiliasi": "kode_afiliasi"
        })

        payload["kemasan"] = get_child_data(doc, "kemasan", {
            "jumlahKemasan": "jumlah_kemasan",
            "kodeJenisKemasan": "kode_kemasan",  # DocType uses 'kode_kemasan'
            "merkKemasan": "merek_kemasan",
            "seriKemasan": "seri"  # DocType uses 'seri' not 'seri_kemasan'
        })

        payload["dokumen"] = get_child_data(doc, "dokumen", {
            "kodeDokumen": "kode_dokumen",
            "nomorDokumen": "nomor_dokumen",
            "seriDokumen": "seri_dokumen",
            "tanggalDokumen": "tanggal_dokumen"
        })

        payload["pengangkut"] = get_child_data(doc, "pengangkut", {
            "kodeBendera": "kode_bendera",
            "namaPengangkut": "nama_pengangkut",
            "nomorPengangkut": "nomor_pengangkut",
            "kodeCaraAngkut": "kode_cara_angkut",
            "seriPengangkut": "seri_pengangkut"
        })
        
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
        
        for brg in barangs:
            brg_item = {
                "cif": round_decimal(brg.get("cif"), 2),
                "cifRupiah": round_decimal(brg.get("cif_rupiah"), 2),
                "fob": round_decimal(brg.get("fob"), 2),
                "hargaEkspor": round_decimal(brg.get("harga_ekspor"), 2),
                "hargaPatokan": round_decimal(brg.get("harga_patokan"), 2),
                "hargaPerolehan": round_decimal(brg.get("harga_perolehan"), 2),
                "hargaSatuan": round_decimal(brg.get("harga_satuan"), 2),
                "jumlahKemasan": round_decimal(brg.get("jumlah_kemasan"), 2),  # multipleOf 0.01
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4),  # multipleOf 0.0001
                "kodeJenisKemasan": brg.get("kode_kemasan") or "",
                "kodeNegaraAsal": brg.get("kode_negara_asal") or "",
                "kodeSatuanBarang": brg.get("kode_satuan") or "",
                "merk": brg.get("merek") or "",
                "ndpbm": round_decimal(brg.get("ndpbm"), 4),
                "netto": round_decimal(brg.get("netto"), 4),  # multipleOf 0.0001
                "nilaiBarang": round_decimal(brg.get("nilai_barang"), 2),
                "nilaiDanaSawit": round_decimal(brg.get("nilai_dana_sawit"), 2),
                "posTarif": brg.get("hs") or "",
                "seriBarang": cint(brg.get("seri_barang")) or 0,
                "tipe": brg.get("tipe") or "",
                "uraian": brg.get("uraian") or "",
                "volume": round_decimal(brg.get("volume"), 4),  # multipleOf 0.0001
                "asuransi": round_decimal(brg.get("asuransi"), 2),
                "bruto": round_decimal(brg.get("bruto"), 4),  # multipleOf 0.0001
                "diskon": round_decimal(brg.get("diskon"), 2),
                "freight": round_decimal(brg.get("freight"), 2),
                "hargaPenyerahan": round_decimal(brg.get("harga_penyerahan"), 2),
                "hjeCukai": round_decimal(brg.get("hje_cukai"), 2),
                "isiPerKemasan": round_decimal(brg.get("isi_per_kemasan"), 2),  # multipleOf 0.01
                "jumlahBahanBaku": cint(brg.get("jumlah_bahan_baku")) or 0,
                "jumlahDilekatkan": cint(brg.get("jumlah_dilekatkan")) or 0,
                "jumlahPitaCukai": cint(brg.get("jumlah_pita_cukai")) or 0,
                "jumlahRealisasi": round_decimal(brg.get("jumlah_realisasi"), 2),
                "kapasitasSilinder": cint(brg.get("kapasitas_silinder")) or 0,
                "kodeKondisiBarang": brg.get("kode_kondisi_barang") or "",
                "nilaiDevisa": round_decimal(brg.get("nilai_devisa"), 2),
                "nilaiTambah": round_decimal(brg.get("nilai_tambah"), 2),
                "pernyataanLartas": brg.get("pernyataan_lartas") or "T",
                "persentaseImpor": round_decimal(brg.get("persentase_impor"), 2),
                "saldoAkhir": round_decimal(brg.get("saldo_akhir"), 2),
                "saldoAwal": round_decimal(brg.get("saldo_awal"), 2),
                "seriBarangDokAsal": cint(brg.get("seri_barang_asal")) or 0,
                "seriIjin": cint(brg.get("seri_izin")) or 0,
                "tahunPembuatan": cint(brg.get("tahun_pembuatan")) or 0,
                "tarifCukai": round_decimal(brg.get("tarif_cukai"), 2),
                "metodePenentuanNilai": brg.get("metode_penentuan_nilai") or "Metode 1",
                "alasanMetodePenentuanNilai": brg.get("alasan_metode_penentuan_nilai") if hasattr(brg, 'alasan_metode_penentuan_nilai') else None,
                "statementPerbedaanHarga": brg.get("statement_perbedaan_harga") or "T",
            }
            
            # Fetch Child Tables for this Barang
            # BARANG TARIF
            brg_doc = frappe.get_doc("BARANG V1", brg.get("name")) # Need doc to get child tables easily
            
            brg_item["barangTarif"] = []
            for trf in brg_doc.get("barang_tarif") or []:
                brg_item["barangTarif"].append({
                    "tarif": round_decimal(trf.get("tarif"), 2),  # multipleOf 0.01
                    "nilaiBayar": round_decimal(trf.get("nilai_bayar"), 2),  # multipleOf 0.01
                    "seriBarang": cint(trf.get("seri_barang")) or 0,
                    "kodeKemasan": "",  # Not in BARANG TARIF
                    "jumlahSatuan": round_decimal(trf.get("jumlah_satuan"), 4),  # multipleOf 0.0001
                    "jumlahKemasan": 0,  # Not in BARANG TARIF
                    "kodeJenisTarif": trf.get("kode_tarif") or "",
                    "nilaiFasilitas": round_decimal(trf.get("nilai_fasilitas"), 2),  # multipleOf 0.01
                    "tarifFasilitas": round_decimal(trf.get("tarif_fasilitas"), 2),  # multipleOf 0.01
                    "kodeSatuanBarang": trf.get("kode_satuan") or "",
                    "kodeJenisPungutan": trf.get("kode_pungutan") or "",
                    "kodeKomoditiCukai": "",  # Not in BARANG TARIF
                    "kodeFasilitasTarif": trf.get("kode_fasilitas") or "",
                    "nilaiSudahDilunasi": round_decimal(trf.get("nilai_sudah_dilunasi"), 2),
                    "kodeSubKomoditiCukai": ""  # Not in BARANG TARIF
                })

            # BARANG DOKUMEN
            brg_item["barangDokumen"] = []
            for dok in brg_doc.get("barang_dokumen") or []:
                brg_item["barangDokumen"].append({
                    "seriDokumen": dok.get("seri_dokumen"),
                    "seriIzin": dok.get("seri_izin")
                })
                
            # BARANG SPEK KHUSUS
            brg_item["barangSpekKhusus"] = []
            for spek in brg_doc.get("barang_spek_khusus") or []:
                brg_item["barangSpekKhusus"].append({
                    "seriBarangSpekKhusus": spek.idx,  # Use row index as seri
                    "kodeSpekKhusus": cint(spek.kode_spek_khusus),  # Cast to int (valid: 1-19, 1001-1020)
                    "uraianBarangSpekKhusus": spek.uraian_spek_khusus  # Note: double underscore in fieldname
                })
                
            # BARANG VD
            brg_item["barangVd"] = []
            for vd in brg_doc.get("barang_vd") or []:
                brg_item["barangVd"].append({
                    "kodeJenisVd": vd.kode_jenis_vd,
                    "nilaiBarangVd": vd.nilai_barang  # Schema uses nilaiBarangVd
                })
                
            # BARANG PEMILIK
            brg_item["barangPemilik"] = []
            for pem in brg_doc.get("barang_pemilik") or []:
                brg_item["barangPemilik"].append({
                    "seriBarang": pem.seri_barang,  # Already exists in BARANG ENTITAS
                    "seriBarangPemilik": pem.seri_barang_pemilik,  # Already exists
                    "seriEntitas": pem.seri_entitas  # Already exists
                })

            barang_list.append(brg_item)

        payload["barang"] = barang_list
        
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
        
        return {"Declaration": payload}

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
            "asalData": "S",  # Schema requires constant "S"
            "asuransi": round_decimal(doc.get("asuransi"), 2),
            "bruto": round_decimal(doc.get("bruto"), 4),
            "cif": round_decimal(doc.get("cif"), 2),
            "fob": round_decimal(doc.get("fob"), 2),
            "freight": round_decimal(doc.get("freight"), 2),
            "hargaPenyerahan": round_decimal(doc.get("harga_penyerahan"), 4),
            "jabatanTtd": doc.get("jabatan_pernyataan") or "",
            "jumlahKontainer": len( (doc.get("kontainer") or [])),
            "kodeAsuransi": doc.get("kode_asuransi") or "LN",
            "kodeDokumen": "23",  # Schema requires constant "23"
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
            "ndpbm": round_decimal(doc.get("ndpbm"), 4),
            "netto": round_decimal(doc.get("netto"), 4),
            "nik": "",  # NIK/API field
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

        # 2. Map Entitas (BC23 structure)
        payload["entitas"] = []
        for ent in (doc.get("entitas") or []):
            ent_item = {
                "alamatEntitas": ent.get("alamat_entitas") or "",
                "kodeEntitas": ent.get("kode_entitas") or "",
                "namaEntitas": ent.get("nama_entitas") or "",
                "seriEntitas": ent.get("seri") or 0,
            }
            # Add fields based on entitas type
            if ent.get("kode_entitas") == "3":  # Pengusaha TPB
                ent_item["kodeJenisIdentitas"] = ent.get("kode_jenis_identitas") or ""
                ent_item["nibEntitas"] = ent.get("nib_entitas") or ""
                ent_item["nomorIdentitas"] = ent.get("nomor_identitas") or ""
                ent_item["nomorIjinEntitas"] = ent.get("nomor_ijin_entitas") or ""
                ent_item["tanggalIjinEntitas"] = fmt_date(ent.get("tanggal_ijin_entitas"))
            elif ent.get("kode_entitas") == "5":  # Pemasok
                ent_item["kodeNegara"] = ent.get("kode_negara") or ""
            elif ent.get("kode_entitas") == "7":  # Pemilik Barang
                ent_item["kodeJenisApi"] = ent.get("kode_jenis_api") or ""
                ent_item["kodeJenisIdentitas"] = ent.get("kode_jenis_identitas") or ""
                ent_item["kodeStatus"] = ent.get("kode_status") or ""
                ent_item["nomorIdentitas"] = ent.get("nomor_identitas") or ""
                ent_item["nomorIjinEntitas"] = ent.get("nomor_ijin_entitas") or ""
                ent_item["tanggalIjinEntitas"] = fmt_date(ent.get("tanggal_ijin_entitas"))
            payload["entitas"].append(ent_item)

        # 3. Map Kemasan
        payload["kemasan"] = []
        for kem in (doc.get("kemasan") or []):
            payload["kemasan"].append({
                "jumlahKemasan": round_decimal(kem.get("jumlah_kemasan"), 2),
                "kodeJenisKemasan": kem.get("kode_kemasan") or "",
                "seriKemasan": kem.get("seri") or 0,
                "merkKemasan": kem.get("merek_kemasan") or "",
            })

        # 4. Map Kontainer
        payload["kontainer"] = []
        for kon in (doc.get("kontainer") or []):
            payload["kontainer"].append({
                "kodeTipeKontainer": kon.get("kode_tipe_kontainer") or "",
                "kodeUkuranKontainer": kon.get("kode_ukuran_kontainer") or "",
                "nomorKontainer": kon.get("nomor_kontainer") or "",
                "seriKontainer": kon.get("seri") or 0,
                "kodeJenisKontainer": kon.get("kode_jenis_kontainer") or "",
            })

        # 5. Map Dokumen
        payload["dokumen"] = []
        for dok in (doc.get("dokumen") or []):
            payload["dokumen"].append({
                "idDokumen": "",
                "kodeDokumen": dok.get("kode_dokumen") or "",
                "nomorDokumen": dok.get("nomor_dokumen") or "",
                "seriDokumen": dok.get("seri") or 0,
                "tanggalDokumen": fmt_date(dok.get("tanggal_dokumen")),
            })

        # 6. Map Pengangkut (BC23 includes kodeBendera and kodeCaraAngkut)
        payload["pengangkut"] = []
        for peng in (doc.get("pengangkut") or []):
            payload["pengangkut"].append({
                "kodeBendera": peng.kode_bendera or "",
                "namaPengangkut": peng.nama_pengangkut or "",
                "nomorPengangkut": peng.nomor_pengangkut or "",
                "kodeCaraAngkut": peng.kode_cara_angkut or "",
                "seriPengangkut": peng.seri_pengangkut or 0,
            })

        # 7. Map Barang V1 (BC23 structure)
        barang_list = []
        barangs = frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc")
        
        for brg in barangs:
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
                "kodeNegaraAsal": brg.get("kode_negara_asal") or "",
                "kodePerhitungan": brg.get("kode_perhitungan") or "",
                "kodeSatuanBarang": brg.get("kode_satuan") or "",
                "merk": brg.get("merek") or "",
                "netto": round_decimal(brg.get("netto"), 4),
                "nilaiBarang": round_decimal(brg.get("nilai_barang"), 2),
                "nilaiTambah": round_decimal(brg.get("nilai_tambah"), 2),
                "posTarif": brg.get("hs") or "",
                "seriBarang": brg.get("seri_barang") or 0,
                "spesifikasiLain": brg.get("spesifikasi_lain") or "",
                "tipe": brg.get("tipe") or "",
                "ukuran": brg.get("ukuran") or "",
                "uraian": brg.get("uraian") or "",
                "ndpbm": round_decimal(brg.get("ndpbm"), 4),
                "cifRupiah": round_decimal(brg.get("cif_rupiah"), 2),
                "hargaPerolehan": round_decimal(brg.get("harga_perolehan"), 2),
                "kodeAsalBahanBaku": brg.get("kode_asal_barang") or "",
            }
            
            # Fetch Child Tables for this Barang
            brg_doc = frappe.get_doc("BARANG V1", brg.get("name"))
            
            # BARANG TARIF (BC23 structure)
            brg_item["barangTarif"] = []
            for trf in brg_doc.get("barang_tarif") or []:
                brg_item["barangTarif"].append({
                    "kodeJenisTarif": trf.get("kode_tarif") or "",
                    "jumlahSatuan": round_decimal(trf.get("jumlah_satuan"), 4),
                    "kodeFasilitasTarif": trf.get("kode_fasilitas") or "",
                    "kodeSatuanBarang": trf.get("kode_satuan") or "",
                    "kodeJenisPungutan": trf.get("kode_pungutan") or "",
                    "nilaiBayar": round_decimal(trf.get("nilai_bayar"), 2),
                    "nilaiFasilitas": round_decimal(trf.get("nilai_fasilitas"), 2),
                    "nilaiSudahDilunasi": round_decimal(trf.get("nilai_sudah_dilunasi"), 2) or 0,
                    "seriBarang": brg.get("seri_barang") or 0,
                    "tarif": round_decimal(trf.get("tarif"), 2),
                    "tarifFasilitas": round_decimal(trf.get("tarif_fasilitas"), 2),
                })

            # BARANG DOKUMEN
            brg_item["barangDokumen"] = []
            for dok in brg_doc.get("barang_dokumen") or []:
                brg_item["barangDokumen"].append({
                    "seriDokumen": dok.get("seri_dokumen") or 0,
                })

            barang_list.append(brg_item)

        payload["barang"] = barang_list
        
        return {"Declaration": payload}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get CEISA BC23 JSON Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist(allow_guest=True)
def get_ceisa_bc25_json(nomor_aju):
    """Export HEADER V21 to BC25 (TPB Internal Transfer) JSON format"""
    try:
        doc = frappe.get_doc("HEADER V21", nomor_aju)
        
        # 1. Map Header Fields (BC25 specific)
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
            "netto": round_decimal(doc.get("netto"), 4),
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

        # 2. Map Entitas (BC25 structure - types 3, 7, 8)
        payload["entitas"] = []
        for ent in (doc.get("entitas") or []):
            ent_item = {
                "alamatEntitas": ent.get("alamat_entitas") or "",
                "kodeEntitas": ent.get("kode_entitas") or "",
                "namaEntitas": ent.get("nama_entitas") or "",
                "seriEntitas": ent.get("seri") or 0,
            }
            # Add fields based on entitas type
            if ent.get("kode_entitas") == "3":  # Pengusaha TPB
                ent_item["kodeJenisApi"] = ent.get("kode_jenis_api") or ""
                ent_item["kodeJenisIdentitas"] = ent.get("kode_jenis_identitas") or ""
                ent_item["kodeStatus"] = ent.get("kode_status") or ""
                ent_item["nibEntitas"] = ent.get("nib_entitas") or ""
                ent_item["nomorIdentitas"] = ent.get("nomor_identitas") or ""
                ent_item["nomorIjinEntitas"] = ent.get("nomor_ijin_entitas") or ""
                ent_item["tanggalIjinEntitas"] = fmt_date(ent.get("tanggal_ijin_entitas"))
            elif ent.get("kode_entitas") == "7":  # Pemilik Barang
                ent_item["kodeJenisIdentitas"] = ent.get("kode_jenis_identitas") or ""
                ent_item["kodeStatus"] = ent.get("kode_status") or ""
                ent_item["nomorIdentitas"] = ent.get("nomor_identitas") or ""
            elif ent.get("kode_entitas") == "8":  # Penerima Barang
                ent_item["kodeJenisApi"] = ent.get("kode_jenis_api") or ""
                ent_item["kodeJenisIdentitas"] = ent.get("kode_jenis_identitas") or ""
                ent_item["kodeStatus"] = ent.get("kode_status") or ""
                ent_item["niperEntitas"] = ent.get("niper_entitas") or ""
                ent_item["nomorIdentitas"] = ent.get("nomor_identitas") or ""
            payload["entitas"].append(ent_item)

        # 3. Map Kemasan
        payload["kemasan"] = []
        for kem in (doc.get("kemasan") or []):
            payload["kemasan"].append({
                "jumlahKemasan": round_decimal(kem.get("jumlah_kemasan"), 2),
                "kodeJenisKemasan": kem.get("kode_kemasan") or "",
                "merkKemasan": kem.get("merek_kemasan") or "",
                "seriKemasan": kem.get("seri") or 0,
            })

        # 4. Map Kontainer
        payload["kontainer"] = []
        for kon in (doc.get("kontainer") or []):
            payload["kontainer"].append({
                "kodeJenisKontainer": kon.get("kode_jenis_kontainer") or "",
                "kodeTipeKontainer": kon.get("kode_tipe_kontainer") or "",
                "kodeUkuranKontainer": kon.get("kode_ukuran_kontainer") or "",
                "nomorKontainer": kon.get("nomor_kontainer") or "",
                "seriKontainer": kon.get("seri") or 0,
            })

        # 5. Map Dokumen
        payload["dokumen"] = []
        for dok in (doc.get("dokumen") or []):
            payload["dokumen"].append({
                "idDokumen": "",
                "kodeDokumen": dok.get("kode_dokumen") or "",
                "nomorDokumen": dok.get("nomor_dokumen") or "",
                "seriDokumen": dok.get("seri") or 0,
                "tanggalDokumen": fmt_date(dok.get("tanggal_dokumen")),
            })

        # 6. Map Pengangkut (BC25 - no kodeBendera)
        payload["pengangkut"] = []
        for peng in (doc.get("pengangkut") or []):
            payload["pengangkut"].append({
                "namaPengangkut": peng.nama_pengangkut or "",
                "nomorPengangkut": peng.nomor_pengangkut or "",
                "kodeCaraAngkut": peng.kode_cara_angkut or "",
                "seriPengangkut": peng.seri_pengangkut or 0,
            })

        # 7. Map Barang V1 (BC25 structure)
        barang_list = []
        barangs = frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc")
        
        for brg in barangs:
            brg_item = {
                "bruto": round_decimal(brg.get("bruto"), 4),
                "cif": round_decimal(brg.get("cif"), 2),
                "diskon": round_decimal(brg.get("diskon"), 2),
                "fob": round_decimal(brg.get("fob"), 2),
                "freight": round_decimal(brg.get("freight"), 2),
                "hargaEkspor": round_decimal(brg.get("harga_ekspor"), 2),
                "hargaPenyerahan": round_decimal(brg.get("harga_penyerahan"), 4),
                "isiPerKemasan": round_decimal(brg.get("isi_per_kemasan"), 2),
                "jumlahKemasan": round_decimal(brg.get("jumlah_kemasan"), 2),
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4),
                "kodeBarang": brg.get("kode_barang") or "",
                "kodeGunaBarang": brg.get("kode_guna_barang") or "",
                "kodeKategoriBarang": brg.get("kode_kategori_barang") or "",
                "kodeJenisKemasan": brg.get("kode_kemasan") or "",
                "kodeKondisiBarang": brg.get("kode_kondisi_barang") or "",
                "kodePerhitungan": brg.get("kode_perhitungan") or "",
                "kodeSatuanBarang": brg.get("kode_satuan") or "",
                "merk": brg.get("merek") or "",
                "netto": round_decimal(brg.get("netto"), 4),
                "nilaiBarang": round_decimal(brg.get("nilai_barang"), 2),
                "posTarif": brg.get("hs") or "",
                "seriBarang": brg.get("seri_barang") or 0,
                "spesifikasiLain": brg.get("spesifikasi_lain") or "",
                "tipe": brg.get("tipe") or "",
                "ukuran": brg.get("ukuran") or "",
                "uraian": brg.get("uraian") or "",
                "ndpbm": round_decimal(brg.get("ndpbm"), 4),
                "cifRupiah": round_decimal(brg.get("cif_rupiah"), 2),
                "hargaPerolehan": round_decimal(brg.get("harga_perolehan"), 2),
                "kodeDokAsal": brg.get("kode_dokumen_asal") or "",
                "flag4tahun": brg.get("flag_4_tahun") or "",
            }
            
            # Fetch Child Tables for this Barang
            brg_doc = frappe.get_doc("BARANG V1", brg.get("name"))
            
            # BARANG TARIF (BC25 structure)
            brg_item["barangTarif"] = []
            for trf in brg_doc.get("barang_tarif") or []:
                brg_item["barangTarif"].append({
                    "seriBarang": brg.get("seri_barang") or 0,
                    "kodeJenisTarif": trf.get("kode_tarif") or "",
                    "jumlahSatuan": round_decimal(trf.get("jumlah_satuan"), 4),
                    "kodeFasilitasTarif": trf.get("kode_fasilitas") or "",
                    "kodeSatuanBarang": trf.get("kode_satuan") or "",
                    "kodeJenisPungutan": trf.get("kode_pungutan") or "",
                    "nilaiBayar": round_decimal(trf.get("nilai_bayar"), 2),
                    "nilaiFasilitas": round_decimal(trf.get("nilai_fasilitas"), 2),
                    "nilaiSudahDilunasi": cint(trf.get("nilai_sudah_dilunasi")) or 0,
                    "tarif": round_decimal(trf.get("tarif"), 2),
                    "tarifFasilitas": round_decimal(trf.get("tarif_fasilitas"), 2),
                })

            # BARANG DOKUMEN
            brg_item["barangDokumen"] = []
            for dok in brg_doc.get("barang_dokumen") or []:
                brg_item["barangDokumen"].append({
                    "seriDokumen": dok.get("seri_dokumen") or 0,
                    "seriIjin": dok.get("seri_izin") or 0,
                })

            # BAHAN BAKU (BC25 structure)
            brg_item["bahanBaku"] = []
            bahan_bakus = frappe.get_all("BAHAN BAKU", 
                filters={"parent_barang": brg.get("name")}, 
                fields=["*"],
                order_by="seri_bahan_baku asc"
            )
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
                    "tanggalDaftarDokAsal": fmt_date(bb.get("tanggal_daftar_asal")),
                    "tipeBarang": bb.get("tipe") or "",
                    "ukuranBarang": bb.get("ukuran") or "",
                    "uraianBarang": bb.get("uraian") or "",
                }
                
                # BahanBakuDokumen
                bb_item["bahanBakuDokumen"] = []
                for bbd in bb_doc.get("bahan_baku_dokumen") or []:
                    bb_item["bahanBakuDokumen"].append({
                        "seriDokumen": bbd.seri_dokumen or 0,
                    })
                
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

            barang_list.append(brg_item)

        payload["barang"] = barang_list
        
        return {"Declaration": payload}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get CEISA BC25 JSON Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_ceisa_bc30_json(nomor_aju):
    """Export HEADER V21 to BC30 (Export) JSON format"""
    try:
        doc = frappe.get_doc("HEADER V21", nomor_aju)
        
        # 1. Map Header Fields (BC30 specific)
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
        }

        for bank in (doc.get("bank_devisa") or []):
            payload["bankDevisa"].append({
                "kodeBank": bank.kode or "",
                "namaBank": bank.nama or "",
                "seriBank": bank.seri or 1,
            })

        # 2. Map Entitas (BC30 structure - types 2, 6, 7, 8, 4, 23)
        payload["entitas"] = []
        for ent in (doc.get("entitas") or []):
            ent_item = {
                "alamatEntitas": ent.get("alamat_entitas") or "",
                "kodeEntitas": ent.get("kode_entitas") or "",
                "namaEntitas": ent.get("nama_entitas") or "",
                "seriEntitas": ent.get("seri") or 0,
            }
            # Add fields based on entitas type
            if ent.get("kode_entitas") in ["2", "7", "4", "23"]:  # Eksportir, Pemilik, PPJK, Konsolidator
                ent_item["kodeJenisIdentitas"] = ent.get("kode_jenis_identitas") or ""
                ent_item["nomorIdentitas"] = ent.get("nomor_identitas") or ""
                if ent.get("nib_entitas"):
                    ent_item["nibEntitas"] = ent.get("nib_entitas")
                if ent.get("kode_entitas") == "23":
                    ent_item["kodeKategoriKonsolidator"] = ent.get("kode_kategori_konsolidator") or ""
            elif ent.get("kode_entitas") in ["8", "6"]:  # Penerima, Pembeli
                ent_item["kodeNegara"] = ent.get("kode_negara") or ""
            
            payload["entitas"].append(ent_item)

        # 3. Map Barang V1 (BC30 structure)
        barang_list = []
        barangs = frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc")
        
        for brg in barangs:
            brg_item = {
                "fob": round_decimal(brg.get("fob"), 2),
                "hargaEkspor": round_decimal(brg.get("harga_ekspor"), 4),
                "hargaPatokan": round_decimal(brg.get("harga_patokan"), 4),
                "hargaPerolehan": round_decimal(brg.get("harga_perolehan"), 2),
                "hargaSatuan": round_decimal(brg.get("harga_satuan"), 2),
                "jumlahKemasan": round_decimal(brg.get("jumlah_kemasan"), 2),
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4),
                "kodeAsalBahanBaku": brg.get("kode_asal_bahan_baku") or "",
                "kodeBarang": brg.get("kode_barang") or "",
                "kodeDaerahAsal": brg.get("kode_daerah_asal") or "",
                "kodeDokumen": "30",
                "kodeJenisKemasan": brg.get("kode_kemasan") or "",
                "kodeNegaraAsal": brg.get("kode_negara_asal") or "",
                "kodeSatuanBarang": brg.get("kode_satuan") or "",
                "merk": brg.get("merek") or "",
                "ndpbm": round_decimal(brg.get("ndpbm"), 4),
                "netto": round_decimal(brg.get("netto"), 4),
                "nilaiBarang": round_decimal(brg.get("nilai_barang"), 2),
                "nilaiDanaSawit": round_decimal(brg.get("nilai_dana_sawit"), 2),
                "posTarif": brg.get("hs") or "",
                "seriBarang": brg.get("seri_barang") or 0,
                "spesifikasiLain": brg.get("spesifikasi_lain") or "",
                "tipe": brg.get("tipe") or "",
                "ukuran": brg.get("ukuran") or "",
                "uraian": brg.get("uraian") or "",
                "kodeJenisEkspor": doc.get("kode_jenis_ekspor") or "",
            }
            
            # Fetch Child Tables for this Barang
            brg_doc = frappe.get_doc("BARANG V1", brg.get("name"))
            
            # BARANG TARIF (BC30 structure)
            brg_item["barangTarif"] = []
            for trf in brg_doc.get("barang_tarif") or []:
                brg_item["barangTarif"].append({
                    "kodeJenisTarif": trf.get("kode_tarif") or "",
                    "jumlahSatuan": round_decimal(trf.get("jumlah_satuan"), 4),
                    "kodeFasilitasTarif": trf.get("kode_fasilitas") or "",
                    "kodeSatuanBarang": trf.get("kode_satuan") or "",
                    "kodeJenisPungutan": trf.get("kode_pungutan") or "",
                    "nilaiBayar": round_decimal(trf.get("nilai_bayar"), 2),
                    "seriBarang": brg.get("seri_barang") or 0,
                    "tarif": round_decimal(trf.get("tarif"), 4),
                    "tarifFasilitas": round_decimal(trf.get("tarif_fasilitas"), 2),
                })

            # BARANG DOKUMEN
            brg_item["barangDokumen"] = []
            for b_dok in brg_doc.get("barang_dokumen") or []:
                brg_item["barangDokumen"].append({
                    "seriDokumen": b_dok.seri_dokumen or 0,
                    "seriIjin": b_dok.seri_izin or 0,
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
                "jumlahKemasan": round_decimal(kem.get("jumlah_kemasan"), 2),
                "kodeJenisKemasan": kem.get("kode_kemasan") or "",
                "merkKemasan": kem.get("merek_kemasan") or "",
                "seriKemasan": kem.get("seri") or 0,
            })

        # 5. Map Kontainer
        payload["kontainer"] = []
        for kon in (doc.get("kontainer") or []):
            payload["kontainer"].append({
                "kodeJenisKontainer": kon.get("kode_jenis_kontainer") or "",
                "kodeTipeKontainer": kon.get("kode_tipe_kontainer") or "",
                "kodeUkuranKontainer": kon.get("kode_ukuran_kontainer") or "",
                "nomorKontainer": kon.get("nomor_kontainer") or "",
                "seriKontainer": kon.get("seri") or 0,
            })

        # 6. Map Dokumen
        payload["dokumen"] = []
        for d_dok in (doc.get("dokumen") or []):
            payload["dokumen"].append({
                "kodeDokumen": d_dok.kode_dokumen or "",
                "nomorDokumen": d_dok.nomor_dokumen or "",
                "seriDokumen": d_dok.seri or 0,
                "tanggalDokumen": fmt_date(d_dok.tanggal_dokumen),
            })

        # 7. Map Pengangkut (BC30 structure)
        payload["pengangkut"] = []
        for peng in (doc.get("pengangkut") or []):
            payload["pengangkut"].append({
                "namaPengangkut": peng.nama_pengangkut or "",
                "nomorPengangkut": peng.nomor_pengangkut or "",
                "seriPengangkut": peng.seri_pengangkut or 0,
            })
            
        return {"Declaration": payload}

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
                "jumlahKontainer": len( (doc.get("kontainer") or [])),
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

        # Entitas (Types 3, 7, 9)
        decl["entitas"] = []
        for ent in (doc.get("entitas") or []):
            ent_item = {"alamatEntitas": ent.get("alamat_entitas") or "", "kodeEntitas": ent.get("kode_entitas") or "", "namaEntitas": ent.get("nama_entitas") or "", "nibEntitas": ent.get("nib_entitas") or "", "nomorIdentitas": ent.get("nomor_identitas") or "", "seriEntitas": ent.get("seri") or 0}
            if ent.get("kode_entitas") == "3":
                ent_item.update({"kodeJenisIdentitas": ent.get("kode_jenis_identitas") or "", "nomorIjinEntitas": ent.get("nomor_ijin_entitas") or "", "tanggalIjinEntitas": fmt_date(ent.get("tanggal_ijin_entitas"))})
            elif ent.get("kode_entitas") in ["7", "9"]:
                ent_item.update({"kodeJenisApi": ent.get("kode_jenis_api") or "", "kodeJenisIdentitas": ent.get("kode_jenis_identitas") or "", "kodeStatus": ent.get("kode_status") or ""})
            decl["entitas"].append(ent_item)

        # Child Tables (Global logic for most TPB docs)
        decl["dokumen"] = [{"kodeDokumen": d.get("kode_dokumen") or "", "nomorDokumen": d.get("nomor_dokumen") or "", "seriDokumen": d.get("seri") or 0, "tanggalDokumen": fmt_date(d.get("tanggal_dokumen"))} for d in (doc.get("dokumen") or [])]
        decl["pengangkut"] = [{"namaPengangkut": p.get("nama_pengangkut") or "", "nomorPengangkut": p.get("nomor_pengangkut") or "", "seriPengangkut": p.get("seri_pengangkut") or 0} for p in (doc.get("pengangkut") or [])]
        decl["kontainer"] = [{"kodeJenisKontainer": k.get("kode_jenis_kontainer") or "", "kodeTipeKontainer": k.get("kode_tipe_kontainer") or "", "kodeUkuranKontainer": k.get("kode_ukuran_kontainer") or "", "nomorKontainer": k.get("nomor_kontainer") or "", "seriKontainer": k.get("seri") or 0} for k in (doc.get("kontainer") or [])]
        decl["kemasan"] = [{"jumlahKemasan": round_decimal(k.get("jumlah_kemasan"), 2), "kodeJenisKemasan": k.get("kode_kemasan") or "", "merkKemasan": k.get("merek_kemasan") or "", "seriKemasan": k.get("seri") or 0} for k in (doc.get("kemasan") or [])]
        decl["pungutan"] = [{"kodeFasilitasTarif": p.get("kode_fasilitas_tarif") or "", "kodeJenisPungutan": p.get("kode_jenis_pungutan") or "PPN", "nilaiPungutan": round_decimal(p.get("nilai_pungutan"), 2)} for p in (doc.get("pungutan") or [])]

        # Barang
        decl["barang"] = []
        for brg in frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc"):
            brg_doc = frappe.get_doc("BARANG V1", brg.get("name"))
            brg_item = {
                "asuransi": round_decimal(brg.get("asuransi"), 2), "bruto": round_decimal(brg.get("bruto"), 4), "cif": round_decimal(brg.get("cif"), 2), "diskon": round_decimal(brg.get("diskon"), 2), "hargaEkspor": round_decimal(brg.get("harga_ekspor"), 4),
                "hargaPenyerahan": round_decimal(brg.get("harga_penyerahan"), 4), "hargaSatuan": round_decimal(brg.get("harga_satuan"), 4), "isiPerKemasan": round_decimal(brg.get("isi_per_kemasan"), 2), "jumlahKemasan": round_decimal(brg.get("jumlah_kemasan"), 2),
                "jumlahRealisasi": round_decimal(brg.get("jumlah_realisasi"), 4), "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4), "kodeBarang": brg.get("kode_barang") or "", "kodeDokumen": "40", "kodeJenisKemasan": brg.get("kode_kemasan") or "",
                "kodeSatuanBarang": brg.get("kode_satuan") or "", "merk": brg.get("merek") or "", "netto": round_decimal(brg.get("netto"), 4), "nilaiBarang": round_decimal(brg.get("nilai_barang"), 2), "posTarif": brg.get("hs") or "", "seriBarang": brg.get("seri_barang") or 0,
                "spesifikasiLain": brg.get("spesifikasi_lain") or "", "tipe": brg.get("tipe") or "", "ukuran": brg.get("ukuran") or "", "uraian": brg.get("uraian") or "", "volume": round_decimal(brg.get("volume"), 4), "cifRupiah": round_decimal(brg.get("cif_rupiah"), 2),
                "hargaPerolehan": round_decimal(brg.get("harga_perolehan"), 2), "kodeAsalBahanBaku": brg.get("kode_asal_bahan_baku") or "", "ndpbm": round_decimal(brg.get("ndpbm"), 4), "nilaiJasa": round_decimal(brg.get("nilai_jasa"), 4), "uangMuka": round_decimal(brg.get("uang_muka"), 4),
                "barangTarif": [{"kodeJenisTarif": t.get("kode_tarif") or "1", "jumlahSatuan": round_decimal(t.get("jumlah_satuan"), 4), "kodeFasilitasTarif": t.get("kode_fasilitas") or "3", "kodeSatuanBarang": t.get("kode_satuan") or "", "nilaiBayar": round_decimal(t.get("nilai_bayar"), 2), "nilaiFasilitas": round_decimal(t.get("nilai_fasilitas"), 2), "nilaiSudahDilunasi": round_decimal(t.get("nilai_sudah_dilunasi"), 2), "seriBarang": brg.get("seri_barang") or 0, "tarif": round_decimal(t.get("tarif"), 2), "tarifFasilitas": round_decimal(t.get("tarif_fasilitas"), 2), "kodeJenisPungutan": t.get("kode_pungutan") or "PPN"} for t in brg_doc.get("barang_tarif") or []]
            }
            decl["barang"].append(brg_item)

        return payload
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get CEISA BC40 JSON Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_ceisa_bc41_json(nomor_aju):
    """Export HEADER V21 to BC41 (TPB release to TLDDP) JSON format"""
    res = get_ceisa_bc40_json(nomor_aju)
    if "Declaration" in res:
        res["Declaration"]["kodeDokumen"] = "41"
        for brg in res["Declaration"]["barang"]: brg["kodeDokumen"] = "41"
    return res


@frappe.whitelist()
def get_ceisa_bc33_json(nomor_aju):
    """Export HEADER V21 to BC33 (PLB) JSON format"""
    res = get_ceisa_bc40_json(nomor_aju)
    if isinstance(res, dict) and "Declaration" in res:
        res["Declaration"]["kodeDokumen"] = "33"
        for brg in (res["Declaration"].get("barang") or []):
            brg["kodeDokumen"] = "33"
    return res


@frappe.whitelist()
@frappe.whitelist()
def get_ceisa_bc262_json(nomor_aju):
    """Export HEADER V21 to BC262 (Release to other TPB) JSON format"""
    res = get_ceisa_bc40_json(nomor_aju)
    if isinstance(res, dict) and "Declaration" in res:
        res["Declaration"]["kodeDokumen"] = "262"
        for brg in (res["Declaration"].get("barang") or []):
            brg["kodeDokumen"] = "262"
    return res


@frappe.whitelist()
def get_ceisa_bc261_json(nomor_aju):
    """Export HEADER V21 to BC261 (Pemberitahuan Pabean dari TPB ke TPB lainnya) JSON format"""
    res = get_ceisa_bc40_json(nomor_aju)
    if isinstance(res, dict) and "Declaration" in res:
        res["Declaration"]["kodeDokumen"] = "261"
        for brg in (res["Declaration"].get("barang") or []):
            brg["kodeDokumen"] = "261"
    return res


@frappe.whitelist()
def get_ceisa_bc16_json(nomor_aju):
    """Export HEADER V21 to BC16 (PLB Pemasukan) JSON format"""
    try:
        doc = frappe.get_doc("HEADER V21", nomor_aju)
        payload = {
            "asalData": "S", "nomorAju": doc.get("nomoraju") or "", "seri": 0, "kodeDokumen": "16",
            "kodeKantor": doc.get("kode_kantor") or "", "kodeKantorBongkar": doc.get("kode_kantor_bongkar") or "",
            "kodeTps": doc.get("kode_tps") or "", "kodeIncoterm": doc.get("kode_incoterm") or "", "cif": round_decimal(doc.get("cif"), 2),
            "kodeJenisNilai": doc.get("kode_jenis_nilai") or "", "kodePelMuat": doc.get("kode_pelabuhan_muat") or "",
            "kodePelTransit": doc.get("kode_pelabuhan_transit") or "", "kodePelBongkar": doc.get("kode_pelabuhan_bongkar") or "",
            "kodeValuta": doc.get("kode_valuta") or "", "bruto": round_decimal(doc.get("bruto"), 4), "netto": round_decimal(doc.get("netto"), 4),
            "kotaTtd": doc.get("kota_pernyataan") or "", "tanggalTtd": fmt_date(doc.get("tanggal_pernyataan")),
            "jabatanTtd": doc.get("jabatan_pernyataan") or "", "namaTtd": doc.get("nama_pernyataan") or "", "disclaimer": "1",
            "ndpbm": round_decimal(doc.get("ndpbm"), 4), "kodeTutupPu": doc.get("kode_tutup_pu") or "11",
            "nomorBc11": doc.get("nomor_bc11") or "", "posBc11": doc.get("nomor_pos") or "", "subposBc11": doc.get("nomor_sub_pos") or "",
            "tanggalBc11": fmt_date(doc.get("tanggal_bc11")), "tanggalTiba": fmt_date(doc.get("tanggal_tiba")),
        }
        payload["entitas"] = get_child_data(doc, "entitas", {
            "alamatEntitas": "alamat_entitas", "kodeEntitas": "kode_entitas", "kodeNegara": "kode_negara",
            "namaEntitas": "nama_entitas", "seriEntitas": "seri", "kodeJenisIdentitas": "kode_jenis_identitas",
            "nomorIdentitas": "nomor_identitas", "nibEntitas": "nib_entitas", "nomorIjinEntitas": "nomor_ijin_entitas",
            "tanggalIjinEntitas": "tanggal_ijin_entitas"
        })
        payload["kemasan"] = get_child_data(doc, "kemasan", {
            "jumlahKemasan": "jumlah_kemasan", "kodeJenisKemasan": "kode_jenis_kemasan", "merkKemasan": "merk_kemasan", "seriKemasan": "seri"
        })
        payload["kontainer"] = get_child_data(doc, "kontainer", {
            "kodeJenisKontainer": "kode_jenis_kontainer", "kodeTipeKontainer": "kode_tipe_kontainer", "kodeUkuranKontainer": "kode_ukuran_kontainer", "nomorKontainer": "nomor_kontainer", "seriKontainer": "seri"
        })
        payload["dokumen"] = [{"kodeDokumen": d.get("kode_dokumen") or "", "nomorDokumen": d.get("nomor_dokumen") or "", "seriDokumen": d.get("seri") or 0, "tanggalDokumen": fmt_date(d.get("tanggal_dokumen"))} for d in (doc.get("dokumen") or [])]
        
        payload["barang"] = []
        for brg in frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc"):
            brg_doc = frappe.get_doc("BARANG V1", brg.get("name"))
            brg_item = {
                "seriBarang": brg.get("seri_barang") or 0, "posTarif": brg.get("hs") or "", "kodeBarang": brg.get("kode_barang") or "",
                "uraian": brg.get("uraian") or "", "merk": brg.get("merek") or "", "tipe": brg.get("tipe") or "", "ukuran": brg.get("ukuran") or "",
                "spesifikasiLain": brg.get("spesifikasi_lain") or "", "kodeNegaraAsal": brg.get("kode_negara_asal") or "",
                "kodeKategoriBarang": brg.get("kode_kategori_barang") or "", "cif": round_decimal(brg.get("cif"), 2),
                "cifRupiah": round_decimal(brg.get("cif_rupiah"), 2), "kodeJenisNilai": brg.get("kode_jenis_nilai") or "",
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4), "kodeSatuanBarang": brg.get("kode_satuan") or "",
                "netto": round_decimal(brg.get("netto"), 4), "jumlahKemasan": round_decimal(brg.get("jumlah_kemasan"), 2),
                "kodeJenisKemasan": brg.get("kode_kemasan") or "",
                "barangTarif": [{"kodeJenisTarif": t.get("kode_tarif") or "1", "jumlahSatuan": round_decimal(t.get("jumlah_satuan"), 4), "kodeFasilitasTarif": t.get("kode_fasilitas") or "", "kodeSatuanBarang": t.get("kode_satuan") or "", "kodeJenisPungutan": t.get("kode_pungutan") or "", "nilaiBayar": round_decimal(t.get("nilai_bayar"), 2), "seriBarang": brg.get("seri_barang") or 0, "tarif": round_decimal(t.get("tarif"), 2), "tarifFasilitas": round_decimal(t.get("tarif_fasilitas"), 2)} for t in brg_doc.get("barang_tarif") or []]
            }
            payload["barang"].append(brg_item)
        return {"Declaration": payload}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get CEISA BC16 JSON Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_ceisa_bc28_json(nomor_aju):
    """Export HEADER V21 to BC28 (PLB Pengeluaran) JSON format"""
    try:
        doc = frappe.get_doc("HEADER V21", nomor_aju)
        payload = {
            "asalData": "S", "bruto": round_decimal(doc.get("bruto"), 4), "cif": round_decimal(doc.get("cif"), 2), "disclaimer": "1",
            "kodeCaraBayar": doc.get("kode_cara_bayar") or "", "kodeDokumen": "28", "kodeGudangAsal": doc.get("kode_tps") or "",
            "kodeIncoterm": doc.get("kode_incoterm") or "", "kodeJenisNilai": doc.get("kode_jenis_nilai") or "",
            "kodeJenisProsedur": doc.get("kode_jenis_prosedur") or "", "kodeJenisImpor": doc.get("kode_jenis_impor") or "",
            "kodeKantor": doc.get("kode_kantor") or "", "kodeValuta": doc.get("kode_valuta") or "", "kotaTtd": doc.get("kota_pernyataan") or "",
            "namaTtd": doc.get("nama_pernyataan") or "", "ndpbm": round_decimal(doc.get("ndpbm"), 4), "netto": round_decimal(doc.get("netto"), 4),
            "nik": "", "nilaiBarang": round_decimal(doc.get("nilai_barang"), 2), "nomorAju": doc.get("nomoraju") or "", "seri": 0,
            "tanggalTtd": fmt_date(doc.get("tanggal_pernyataan")), "volume": round_decimal(doc.get("volume"), 4),
        }
        payload["entitas"] = get_child_data(doc, "entitas", {
            "alamatEntitas": "alamat_entitas", "kodeEntitas": "kode_entitas", "kodeJenisApi": "kode_jenis_api",
            "kodeJenisIdentitas": "kode_jenis_identitas", "kodeStatus": "kode_status", "namaEntitas": "nama_entitas",
            "nibEntitas": "nib_entitas", "nomorIdentitas": "nomor_identitas", "seriEntitas": "seri",
            "kodeNegara": "kode_negara", "nomorIjinEntitas": "nomor_ijin_entitas", "tanggalIjinEntitas": "tanggal_ijin_entitas"
        })
        payload["kemasan"] = get_child_data(doc, "kemasan", {
            "jumlahKemasan": "jumlah_kemasan", "kodeJenisKemasan": "kode_jenis_kemasan", "merkKemasan": "merk_kemasan", "seriKemasan": "seri"
        })
        payload["kontainer"] = get_child_data(doc, "kontainer", {
            "kodeJenisKontainer": "kode_jenis_kontainer", "kodeTipeKontainer": "kode_tipe_kontainer", "kodeUkuranKontainer": "kode_ukuran_kontainer", "nomorKontainer": "nomor_kontainer", "seriKontainer": "seri"
        })
        payload["dokumen"] = [{"kodeDokumen": d.get("kode_dokumen") or "", "nomorDokumen": d.get("nomor_dokumen") or "", "seriDokumen": d.get("seri") or 0, "tanggalDokumen": fmt_date(d.get("tanggal_dokumen"))} for d in (doc.get("dokumen") or [])]
        
        payload["barang"] = []
        for brg in frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc"):
            brg_doc = frappe.get_doc("BARANG V1", brg.get("name"))
            brg_item = {
                "cif": round_decimal(brg.get("cif"), 2), "jumlahKemasan": round_decimal(brg.get("jumlah_kemasan"), 2),
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4), "kodeBarang": brg.get("kode_barang") or "",
                "kodeJenisNilai": brg.get("kode_jenis_nilai") or "", "kodeJenisKemasan": brg.get("kode_kemasan") or "", "kodeNegaraAsal": brg.get("kode_negara_asal") or "",
                "kodePerhitungan": brg.get("kode_perhitungan") or "", "kodeSatuanBarang": brg.get("kode_satuan") or "", "merk": brg.get("merek") or "",
                "netto": round_decimal(brg.get("netto"), 4), "nilaiBarang": round_decimal(brg.get("nilai_barang"), 2), "nilaiTambah": round_decimal(brg.get("nilai_tambah"), 2),
                "persentaseImpor": round_decimal(brg.get("persentase_impor"), 2), "posTarif": brg.get("hs") or "", "seriBarang": brg.get("seri_barang") or 0,
                "seriBarangDokAsal": cint(brg.get("seri_barang_asal")) or 0, "spesifikasiLain": brg.get("spesifikasi_lain") or "", "tipe": brg.get("tipe") or "",
                "ukuran": brg.get("ukuran") or "", "uraian": brg.get("uraian") or "", "ndpbm": round_decimal(brg.get("ndpbm"), 4), "cifRupiah": round_decimal(brg.get("cif_rupiah"), 2),
                "hargaPerolehan": round_decimal(brg.get("harga_perolehan"), 2), "kodeAsalBahanBaku": brg.get("kode_asal_barang") or "", "kodeDokAsal": brg.get("kode_dokumen_asal") or "",
                "kodeKantorAsal": brg.get("kode_kantor_asal") or "", "nomorAjuDokAsal": brg.get("nomor_aju_asal") or "", "nomorDaftarDokAsal": brg.get("nomor_daftar_asal") or "",
                "tanggalDaftarDokAsal": fmt_date(brg.get("tanggal_daftar_asal")),
                "barangTarif": [{"kodeJenisTarif": t.get("kode_tarif") or "1", "jumlahSatuan": round_decimal(t.get("jumlah_satuan"), 4), "kodeFasilitasTarif": t.get("kode_fasilitas") or "", "kodeSatuanBarang": t.get("kode_satuan") or "", "kodeJenisPungutan": t.get("kode_pungutan") or "BM", "nilaiBayar": round_decimal(t.get("nilai_bayar"), 2), "nilaiFasilitas": round_decimal(t.get("nilai_fasilitas"), 2), "nilaiSudahDilunasi": cint(t.get("nilai_sudah_dilunasi")), "seriBarang": brg.get("seri_barang") or 0, "tarif": round_decimal(t.get("tarif"), 2), "tarifFasilitas": round_decimal(t.get("tarif_fasilitas"), 2)} for t in brg_doc.get("barang_tarif") or []]
            }
            payload["barang"].append(brg_item)
        return {"Declaration": payload}
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

        # Entitas (Types 3, 8, 7)
        decl["entitas"] = []
        for ent in (doc.get("entitas") or []):
            ent_item = {
                "alamatEntitas": ent.get("get")("alamat_entitas") or "",
                "kodeEntitas": ent.get("get")("kode_entitas") or "",
                "namaEntitas": ent.get("get")("nama_entitas") or "",
                "seriEntitas": ent.get("get")("seri") or 0,
            }
            if ent.get("get")("kode_entitas") == "3":
                ent_item.update({
                    "kodeJenisIdentitas": ent.get("get")("kode_jenis_identitas") or "",
                    "nomorIdentitas": ent.get("get")("nomor_identitas") or "",
                    "nibEntitas": ent.get("get")("nib_entitas") or "",
                    "nomorIjinEntitas": ent.get("get")("nomor_ijin_entitas") or "",
                })
            elif ent.get("get")("kode_entitas") == "8":
                ent_item.update({
                    "kodeNegara": ent.get("get")("kode_negara") or "",
                })
            elif ent.get("get")("kode_entitas") == "7":
                ent_item.update({
                    "kodeJenisIdentitas": ent.get("get")("kode_jenis_identitas") or "",
                    "kodeStatus": ent.get("get")("kode_status") or "",
                    "nomorIdentitas": ent.get("get")("nomor_identitas") or "",
                    "nibEntitas": ent.get("get")("nib_entitas") or "",
                    "nomorIjinEntitas": ent.get("get")("nomor_ijin_entitas") or "",
                    "tanggalIjinEntitas": fmt_date(ent.get("get")("tanggal_ijin_entitas")),
                })
            decl["entitas"].append(ent_item)

        # Child Tables
        decl["kemasan"] = [{"jumlahKemasan": cint(k.get("get")("jumlah_kemasan")), "kodeJenisKemasan": k.get("get")("kode_kemasan") or "", "merkKemasan": k.get("get")("merek_kemasan") or "", "seriKemasan": k.get("get")("seri") or 0} for k in (doc.get("kemasan") or [])]
        decl["kontainer"] = [{"kodeJenisKontainer": k.get("get")("kode_jenis_kontainer") or "", "kodeTipeKontainer": k.get("get")("kode_tipe_kontainer") or "", "kodeUkuranKontainer": k.get("get")("kode_ukuran_kontainer") or "", "nomorKontainer": k.get("get")("nomor_kontainer") or "", "seriKontainer": k.get("get")("seri") or 0} for k in (doc.get("kontainer") or [])]
        decl["dokumen"] = [{"idDokumen": "", "kodeDokumen": d.get("get")("kode_dokumen") or "", "nomorDokumen": d.get("get")("nomor_dokumen") or "", "seriDokumen": d.get("get")("seri") or 0, "tanggalDokumen": fmt_date(d.get("get")("tanggal_dokumen")), "urlDokumen": ""} for d in (doc.get("dokumen") or [])]
        decl["pengangkut"] = [{"namaPengangkut": p.get("get")("nama_pengangkut") or "", "nomorPengangkut": p.get("get")("nomor_pengangkut") or "", "seriPengangkut": p.get("get")("seri_pengangkut") or 0, "kodeCaraAngkut": p.get("get")("kode_cara_angkut") or "", "callSign": p.get("get")("call_sign") or ""} for p in (doc.get("pengangkut") or [])]

        # Barang
        decl["barang"] = []
        for brg in frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc"):
            brg_doc = frappe.get_doc("BARANG V1", brg.get("get")("name"))
            brg_item = {
                "cif": round_decimal(brg.get("get")("cif"), 2),
                "jumlahKemasan": round_decimal(brg.get("get")("jumlah_kemasan"), 2),
                "jumlahSatuan": round_decimal(brg.get("get")("jumlah_satuan"), 4),
                "kodeBarang": brg.get("get")("kode_barang") or "",
                "kodeDokumen": "331",
                "kodeJenisKemasan": brg.get("get")("kode_kemasan") or "",
                "kodeSatuanBarang": brg.get("get")("kode_satuan") or "",
                "merk": brg.get("get")("merek") or "",
                "ndpbm": round_decimal(brg.get("get")("ndpbm"), 4),
                "netto": round_decimal(brg.get("get")("netto"), 4),
                "nilaiBarang": round_decimal(brg.get("get")("nilai_barang"), 2),
                "nilaiDevisa": round_decimal(brg.get("get")("nilai_devisa"), 2),
                "posTarif": brg.get("get")("hs") or "",
                "seriBarang": brg.get("get")("seri_barang") or 0,
                "spesifikasiLain": brg.get("get")("spesifikasi_lain") or "",
                "tipe": brg.get("get")("tipe") or "",
                "ukuran": brg.get("get")("ukuran") or "",
                "uraian": brg.get("get")("uraian") or "",
                "kodeKantorAsal": brg.get("get")("kode_kantor_asal") or "",
                "kodeDokAsal": brg.get("get")("kode_dokumen_asal") or "",
                "nomorDaftarDokAsal": brg.get("get")("nomor_daftar_asal") or "",
                "seriBarangDokAsal": str(brg.get("get")("seri_barang_asal") or 0),
                "tanggalDaftarDokAsal": fmt_date(brg.get("get")("tanggal_daftar_asal")),
                "nomorAjuDokAsal": brg.get("get")("nomor_aju_asal") or "",
                "barangTarif": [{"kodeJenisTarif": t.get("get")("kode_tarif") or "1", "jumlahSatuan": round_decimal(t.get("get")("jumlah_satuan"), 4), "kodeFasilitasTarif": t.get("get")("kode_fasilitas") or "", "kodeSatuanBarang": t.get("get")("kode_satuan") or "", "kodeJenisPungutan": t.get("get")("kode_pungutan") or "", "nilaiBayar": round_decimal(t.get("get")("nilai_bayar"), 2), "seriBarang": brg.get("get")("seri_barang") or 0, "tarif": round_decimal(t.get("get")("tarif"), 2), "tarifFasilitas": round_decimal(t.get("get")("tarif_fasilitas"), 2)} for t in brg_doc.get("barang_tarif") or []],
                "barangDokumen": [{"seriDokumen": d.get("get")("seri_dokumen") or 0, "seriIjin": d.get("get")("seri_izin") or 0} for d in brg_doc.get("barang_dokumen") or []],
                "barangPemilik": [{"seriEntitas": 1}]
            }
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
                "asuransi": round_decimal(doc.get("asuransi"), 2), "bruto": round_decimal(doc.get("bruto"), 4), "cif": round_decimal(doc.get("cif"), 2),
                "fob": round_decimal(doc.get("fob"), 2), "freight": round_decimal(doc.get("freight"), 2), "jabatanTtd": doc.get("jabatan_pernyataan") or "",
                "jumlahKontainer": len( (doc.get("kontainer") or [])), "kodeAsalBarangFtz": doc.get("kode_barang_asal_ftz") or "1",
                "kodeAsuransi": doc.get("kode_asuransi") or "DN", "kodeCaraBayar": doc.get("kode_cara_bayar") or "", "kodeCaraDagang": doc.get("kode_cara_dagang") or "",
                "kodeDokumen": "511", "kodeIncoterm": doc.get("kode_incoterm") or "", "kodeKantor": doc.get("kode_kantor") or "",
                "kodeJenisProsedur": doc.get("kode_jenis_prosedur") or "1", "kodeTujuanPemasukan": doc.get("kode_tujuan_pemasukan") or "1",
                "kodePelMuat": doc.get("kode_pelabuhan_muat") or "", "kodePelTransit": doc.get("kode_pelabuhan_transit") or "", "kodePelTujuan": doc.get("kode_pelabuhan_tujuan") or "",
                "kodeTps": doc.get("kode_tps") or "", "kodeValuta": doc.get("kode_valuta") or "IDR", "kotaTtd": doc.get("kota_pernyataan") or "",
                "namaTtd": doc.get("nama_pernyataan") or "", "ndpbm": round_decimal(doc.get("ndpbm"), 4), "netto": round_decimal(doc.get("netto"), 4),
                "nomorAju": doc.get("nomoraju") or doc.name or "", "nomorBc11": doc.get("nomor_bc11") or "", "posBc11": doc.get("nomor_pos") or "",
                "seri": 0, "subposBc11": doc.get("nomor_sub_pos") or "", "tanggalBc11": fmt_date(doc.get("tanggal_bc11")), "tanggalTiba": fmt_date(doc.get("tanggal_tiba")),
                "tanggalTtd": fmt_date(doc.get("tanggal_pernyataan")), "volume": round_decimal(doc.get("volume"), 4),
                "biayaTambahan": round_decimal(doc.get("biaya_tambahan"), 2), "biayaPengurang": round_decimal(doc.get("biaya_pengurang"), 2),
                "entitas": get_child_data(doc, "entitas", {
                    "alamatEntitas": "alamat_entitas", "kodeEntitas": "kode_entitas", "kodeJenisApi": "kode_jenis_api",
                    "kodeJenisIdentitas": "kode_jenis_identitas", "kodeNegara": "kode_negara", "kodeStatus": "kode_status",
                    "namaEntitas": "nama_entitas", "nomorIdentitas": "nomor_identitas", "seriEntitas": "seri"
                }),
                "kemasan": get_child_data(doc, "kemasan", {
                    "jumlahKemasan": "jumlah_kemasan", "kodeJenisKemasan": "kode_jenis_kemasan", "merkKemasan": "merk_kemasan", "seriKemasan": "seri"
                }),
                "kontainer": get_child_data(doc, "kontainer", {
                    "kodeJenisKontainer": "kode_jenis_kontainer", "kodeTipeKontainer": "kode_tipe_kontainer", "kodeUkuranKontainer": "kode_ukuran_kontainer", "nomorKontainer": "nomor_kontainer", "seriKontainer": "seri"
                }),
                "dokumen": [{"kodeDokumen": d.get("kode_dokumen") or "", "nomorDokumen": d.get("nomor_dokumen") or "", "seriDokumen": d.get("seri") or 0, "tanggalDokumen": fmt_date(d.get("tanggal_dokumen"))} for d in (doc.get("dokumen") or [])],
                "pengangkut": [{"namaPengangkut": p.get("nama_pengangkut") or "", "nomorPengangkut": p.get("nomor_pengangkut") or "", "seriPengangkut": p.get("seri_pengangkut") or 0, "kodeCaraAngkut": p.get("kode_cara_angkut") or "", "kodeBendera": p.get("kode_bendera") or ""} for p in (doc.get("pengangkut") or [])],
                "barang": []
            }
        }
        for brg in frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc"):
            brg_doc = frappe.get_doc("BARANG V1", brg.get("name"))
            brg_item = {
                "idBarang": "", "asuransi": round_decimal(brg.get("asuransi"), 2), "bruto": cint(brg.get("bruto")), "cif": round_decimal(brg.get("cif"), 2),
                "fob": round_decimal(brg.get("fob"), 2), "freight": round_decimal(brg.get("freight"), 2), "hargaPenyerahan": round_decimal(brg.get("harga_penyerahan"), 4),
                "hargaSatuan": round_decimal(brg.get("harga_satuan"), 4), "isiPerKemasan": cint(brg.get("isi_per_kemasan")) or 1, "jumlahKemasan": round_decimal(brg.get("jumlah_kemasan"), 2),
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4), "kodeJenisKemasan": brg.get("kode_kemasan") or "", "kodeNegaraAsal": brg.get("kode_negara_asal") or "",
                "kodeSatuanBarang": brg.get("kode_satuan") or "", "merk": brg.get("merek") or "", "netto": round_decimal(brg.get("netto"), 4), "posTarif": brg.get("hs") or "",
                "seriBarang": brg.get("seri_barang") or 0, "spesifikasiLain": brg.get("spesifikasi_lain") or "", "tipe": brg.get("tipe") or "", "ukuran": brg.get("ukuran") or "",
                "uraian": brg.get("uraian") or "", "volume": round_decimal(brg.get("volume"), 4), "ndpbm": round_decimal(brg.get("ndpbm"), 4), "cifRupiah": round_decimal(brg.get("cif_rupiah"), 2),
                "kodeAsalBahanBaku": brg.get("kode_dokumen_asal") or "",
                "barangTarif": [{"kodeJenisTarif": t.get("kode_tarif") or "1", "jumlahSatuan": round_decimal(t.get("jumlah_satuan"), 4), "kodeFasilitasTarif": t.get("kode_fasilitas") or "", "kodeSatuanBarang": t.get("kode_satuan") or "", "kodeJenisPungutan": t.get("kode_pungutan") or "PPN", "nilaiBayar": round_decimal(t.get("nilai_bayar"), 2), "nilaiFasilitas": round_decimal(t.get("nilai_fasilitas"), 2), "nilaiSudahDilunasi": cint(t.get("nilai_sudah_dilunasi")), "seriBarang": brg.get("seri_barang") or 0, "tarif": round_decimal(t.get("tarif"), 2), "tarifFasilitas": round_decimal(t.get("tarif_fasilitas"), 2)} for t in brg_doc.get("barang_tarif") or []]
            }
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
                "asuransi": round_decimal(doc.get("asuransi"), 2), "bruto": round_decimal(doc.get("bruto"), 4), "cif": round_decimal(doc.get("cif"), 2),
                "fob": round_decimal(doc.get("fob"), 2), "freight": round_decimal(doc.get("freight"), 2), "jabatanTtd": doc.get("jabatan_pernyataan") or "",
                "jumlahKontainer": len( (doc.get("kontainer") or [])), "kodeAsalBarangFtz": doc.get("kode_barang_asal_ftz") or "1",
                "kodeAsuransi": doc.get("kode_asuransi") or "DN", "kodeCaraBayar": doc.get("kode_cara_bayar") or "", "kodeCaraDagang": doc.get("kode_cara_dagang") or "",
                "kodeDokumen": "512", "kodeIncoterm": doc.get("kode_incoterm") or "", "kodeKantor": doc.get("kode_kantor") or "",
                "kodeJenisProsedur": doc.get("kode_jenis_prosedur") or "1", "kodeKategoriKeluarFtz": doc.get("kode_kategori_keluar_ftz") or "",
                "kodePelMuat": doc.get("kode_pelabuhan_muat") or "", "kodePelTransit": doc.get("kode_pelabuhan_transit") or "", "kodePelTujuan": doc.get("kode_pelabuhan_tujuan") or "",
                "kodeTps": doc.get("kode_tps") or "", "kodeTujuanPengiriman": doc.get("kode_tujuan_pengiriman") or "", "kodeValuta": doc.get("kode_valuta") or "IDR",
                "kotaTtd": doc.get("kota_pernyataan") or "", "namaTtd": doc.get("nama_pernyataan") or "", "ndpbm": round_decimal(doc.get("ndpbm"), 4),
                "netto": round_decimal(doc.get("netto"), 4), "nomorAju": doc.get("nomoraju") or doc.name or "",
                "seri": 0, "tanggalTtd": fmt_date(doc.get("tanggal_pernyataan")), "volume": round_decimal(doc.get("volume"), 4),
                "biayaTambahan": round_decimal(doc.get("biaya_tambahan"), 2), "biayaPengurang": round_decimal(doc.get("biaya_pengurang"), 2),
                "entitas": get_child_data(doc, "entitas", {
                    "alamatEntitas": "alamat_entitas", "kodeEntitas": "kode_entitas", "kodeJenisApi": "kode_jenis_api",
                    "kodeJenisIdentitas": "kode_jenis_identitas", "kodeNegara": "kode_negara", "kodeStatus": "kode_status",
                    "namaEntitas": "nama_entitas", "nomorIdentitas": "nomor_identitas", "seriEntitas": "seri"
                }),
                "kemasan": get_child_data(doc, "kemasan", {
                    "jumlahKemasan": "jumlah_kemasan", "kodeJenisKemasan": "kode_jenis_kemasan", "merkKemasan": "merk_kemasan", "seriKemasan": "seri"
                }),
                "kontainer": get_child_data(doc, "kontainer", {
                    "kodeJenisKontainer": "kode_jenis_kontainer", "kodeTipeKontainer": "kode_tipe_kontainer", "kodeUkuranKontainer": "kode_ukuran_kontainer", "nomorKontainer": "nomor_kontainer", "seriKontainer": "seri"
                }),
                "dokumen": [{"kodeDokumen": d.get("kode_dokumen") or "", "nomorDokumen": d.get("nomor_dokumen") or "", "seriDokumen": d.get("seri") or 0, "tanggalDokumen": fmt_date(d.get("tanggal_dokumen"))} for d in (doc.get("dokumen") or [])],
                "pengangkut": [{"namaPengangkut": p.get("nama_pengangkut") or "", "nomorPengangkut": p.get("nomor_pengangkut") or "", "seriPengangkut": p.get("seri_pengangkut") or 0, "kodeCaraAngkut": p.get("kode_cara_angkut") or "", "kodeBendera": p.get("kode_bendera") or ""} for p in (doc.get("pengangkut") or [])],
                "barang": []
            }
        }
        for brg in frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc"):
            brg_doc = frappe.get_doc("BARANG V1", brg.get("name"))
            brg_item = {
                "idBarang": "", "asuransi": round_decimal(brg.get("asuransi"), 2), "bruto": cint(brg.get("bruto")), "cif": round_decimal(brg.get("cif"), 2),
                "fob": round_decimal(brg.get("fob"), 2), "freight": round_decimal(brg.get("freight"), 2), "hargaPenyerahan": round_decimal(brg.get("harga_penyerahan"), 4),
                "hargaSatuan": round_decimal(brg.get("harga_satuan"), 4), "isiPerKemasan": cint(brg.get("isi_per_kemasan")) or 1, "jumlahKemasan": round_decimal(brg.get("jumlah_kemasan"), 2),
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4), "kodeJenisKemasan": brg.get("kode_kemasan") or "", "kodeNegaraAsal": brg.get("kode_negara_asal") or "",
                "kodeSatuanBarang": brg.get("kode_satuan") or "", "merk": brg.get("merek") or "", "netto": round_decimal(brg.get("netto"), 4), "posTarif": brg.get("hs") or "",
                "seriBarang": brg.get("seri_barang") or 0, "spesifikasiLain": brg.get("spesifikasi_lain") or "", "tipe": brg.get("tipe") or "", "ukuran": brg.get("ukuran") or "",
                "uraian": brg.get("uraian") or "", "volume": round_decimal(brg.get("volume"), 4), "ndpbm": round_decimal(brg.get("ndpbm"), 4), "cifRupiah": round_decimal(brg.get("cif_rupiah"), 2),
                "kodeAsalBahanBaku": brg.get("kode_dokumen_asal") or "",
                "barangTarif": [{"kodeJenisTarif": t.get("kode_tarif") or "1", "jumlahSatuan": round_decimal(t.get("jumlah_satuan"), 4), "kodeFasilitasTarif": t.get("kode_fasilitas") or "", "kodeSatuanBarang": t.get("kode_satuan") or "", "kodeJenisPungutan": t.get("kode_pungutan") or "PPN", "nilaiBayar": round_decimal(t.get("nilai_bayar"), 2), "nilaiFasilitas": round_decimal(t.get("nilai_fasilitas"), 2), "nilaiSudahDilunasi": cint(t.get("nilai_sudah_dilunasi")), "seriBarang": brg.get("seri_barang") or 0, "tarif": round_decimal(t.get("tarif"), 2), "tarifFasilitas": round_decimal(t.get("tarif_fasilitas"), 2)} for t in brg_doc.get("barang_tarif") or []]
            }
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
                "asuransi": round_decimal(doc.get("asuransi"), 2), "bruto": round_decimal(doc.get("bruto"), 4), "cif": round_decimal(doc.get("cif"), 2),
                "fob": round_decimal(doc.get("fob"), 2), "freight": round_decimal(doc.get("freight"), 2), "jabatanTtd": doc.get("jabatan_pernyataan") or "",
                "jumlahKontainer": len( (doc.get("kontainer") or [])), "kodeAsalBarangFtz": doc.get("kode_barang_asal_ftz") or "1",
                "kodeAsuransi": doc.get("kode_asuransi") or "DN", "kodeCaraBayar": doc.get("kode_cara_bayar") or "", "kodeCaraDagang": doc.get("kode_cara_dagang") or "",
                "kodeDokumen": "513", "kodeIncoterm": doc.get("kode_incoterm") or "", "kodeKantor": doc.get("kode_kantor") or "",
                "kodeKategoriBarangFtz": doc.get("kode_kategori_barang_ftz") or "", "kodeKategoriKeluarFtz": doc.get("kode_kategori_keluar_ftz") or "",
                "kodePelMuat": doc.get("kode_pelabuhan_muat") or "", "kodePelTransit": doc.get("kode_pelabuhan_transit") or "",
                "kodePelTujuan": doc.get("kode_pelabuhan_tujuan") or "", "kodeTps": doc.get("kode_tps") or "", "kodeTujuanPengiriman": doc.get("kode_tujuan_pengiriman") or "",
                "kodeTujuanPengeluaran": doc.get("kode_tujuan_pengeluaran") or "", "kodeTutupPu": doc.get("kode_tutup_pu") or "",
                "kodeValuta": doc.get("kode_valuta") or "", "kotaTtd": doc.get("kota_pernyataan") or "", "namaTransaksiLainnyaFtz": doc.get("nama_transaksi_lainnya_ftz") or "",
                "namaTtd": doc.get("nama_pernyataan") or "", "ndpbm": round_decimal(doc.get("ndpbm"), 4), "netto": round_decimal(doc.get("netto"), 4),
                "nomorAju": doc.get("nomoraju") or doc.name or "", "nomorBc11": doc.get("nomor_bc11") or "", "posBc11": doc.get("nomor_pos") or "",
                "seri": 0, "subposBc11": doc.get("nomor_sub_pos") or "", "tanggalBc11": fmt_date(doc.get("tanggal_bc11")), "tanggalTiba": fmt_date(doc.get("tanggal_tiba")),
                "tanggalTtd": fmt_date(doc.get("tanggal_pernyataan")), "volume": round_decimal(doc.get("volume"), 4),
                "biayaTambahan": round_decimal(doc.get("biaya_tambahan"), 2), "biayaPengurang": round_decimal(doc.get("biaya_pengurang"), 2),
            }
        }
        decl = payload["Declaration"]
        
        # Header Child Tables
        decl["entitas"] = get_child_data(doc, "entitas", {
            "alamatEntitas": "alamat_entitas", "kodeEntitas": "kode_entitas", "kodeJenisApi": "kode_jenis_api",
            "kodeJenisIdentitas": "kode_jenis_identitas", "kodeNegara": "kode_negara", "kodeStatus": "kode_status",
            "namaEntitas": "nama_entitas", "nomorIdentitas": "nomor_identitas", "seriEntitas": "seri"
        })
        decl["kemasan"] = get_child_data(doc, "kemasan", {
            "jumlahKemasan": "jumlah_kemasan", "kodeJenisKemasan": "kode_jenis_kemasan", "merkKemasan": "merk_kemasan", "seriKemasan": "seri"
        })
        decl["kontainer"] = get_child_data(doc, "kontainer", {
            "kodeJenisKontainer": "kode_jenis_kontainer", "kodeTipeKontainer": "kode_tipe_kontainer", "kodeUkuranKontainer": "kode_ukuran_kontainer", "nomorKontainer": "nomor_kontainer", "seriKontainer": "seri"
        })
        decl["dokumen"] = [{"kodeDokumen": d.get("kode_dokumen") or "", "nomorDokumen": d.get("nomor_dokumen") or "", "seriDokumen": d.get("seri") or 0, "tanggalDokumen": fmt_date(d.get("tanggal_dokumen"))} for d in (doc.get("dokumen") or [])]
        decl["pengangkut"] = [{"namaPengangkut": p.get("nama_pengangkut") or "", "nomorPengangkut": p.get("nomor_pengangkut") or "", "seriPengangkut": p.get("seri_pengangkut") or 0, "kodeCaraAngkut": p.get("kode_cara_angkut") or "", "kodeBendera": p.get("kode_bendera") or ""} for p in (doc.get("pengangkut") or [])]

        # Barang V1
        decl["barang"] = []
        for brg in frappe.get_all("BARANG V1", filters={"nomoraju": doc.name}, fields=["*"], order_by="seri_barang asc"):
            brg_doc = frappe.get_doc("BARANG V1", brg.get("name"))
            brg_item = {
                "idBarang": "", "asuransi": round_decimal(brg.get("asuransi"), 2), "bruto": cint(brg.get("bruto")), "cif": round_decimal(brg.get("cif"), 2),
                "fob": round_decimal(brg.get("fob"), 2), "freight": round_decimal(brg.get("freight"), 2), "hargaPenyerahan": round_decimal(brg.get("harga_penyerahan"), 4),
                "hargaSatuan": round_decimal(brg.get("harga_satuan"), 4), "isiPerKemasan": cint(brg.get("isi_per_kemasan")) or 1, "jumlahKemasan": round_decimal(brg.get("jumlah_kemasan"), 2),
                "jumlahSatuan": round_decimal(brg.get("jumlah_satuan"), 4), "kodeJenisKemasan": brg.get("kode_kemasan") or "", "kodeNegaraAsal": brg.get("kode_negara_asal") or "",
                "kodeSatuanBarang": brg.get("kode_satuan") or "", "merk": brg.get("merek") or "", "netto": round_decimal(brg.get("netto"), 4), "posTarif": brg.get("hs") or "",
                "seriBarang": brg.get("seri_barang") or 0, "spesifikasiLain": brg.get("spesifikasi_lain") or "", "tipe": brg.get("tipe") or "", "ukuran": brg.get("ukuran") or "",
                "uraian": brg.get("uraian") or "", "volume": round_decimal(brg.get("volume"), 4), "ndpbm": round_decimal(brg.get("ndpbm"), 4), "cifRupiah": round_decimal(brg.get("cif_rupiah"), 2),
                "barangTarif": [{"kodeJenisTarif": t.get("kode_tarif") or "1", "jumlahSatuan": round_decimal(t.get("jumlah_satuan"), 4), "kodeFasilitasTarif": t.get("kode_fasilitas") or "", "kodeSatuanBarang": t.get("kode_satuan") or "", "kodeJenisPungutan": t.get("kode_pungutan") or "PPN", "nilaiBayar": round_decimal(t.get("nilai_bayar"), 2), "nilaiFasilitas": round_decimal(t.get("nilai_fasilitas"), 2), "nilaiSudahDilunasi": cint(t.get("nilai_sudah_dilunasi")), "seriBarang": brg.get("seri_barang") or 0, "tarif": round_decimal(t.get("tarif"), 2), "tarifFasilitas": round_decimal(t.get("tarif_fasilitas"), 2)} for t in brg_doc.get("barang_tarif") or []]
            }
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


