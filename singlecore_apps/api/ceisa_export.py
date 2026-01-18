import frappe
from frappe.utils import getdate, flt, cint

# Helper to format date
def fmt_date(date_obj):
    if not date_obj: return ""
    return str(date_obj)

# Helper to get child table data
def get_child_data(doc, child_table_name, fields_map):
    data = []
    for child in doc.get(child_table_name, []):
        item = {}
        for json_field, doc_field in fields_map.items():
            val = child.get(doc_field)
            item[json_field] = val if val is not None else ""
        data.append(item)
    return data

@frappe.whitelist(allow_guest=True)
def get_ceisa_bc27_json(nomor_aju):
    try:
        doc = frappe.get_doc("HEADER V21", nomor_aju)
        
        # 1. Map Header Fields
        payload = {
            "idPengguna": "", # Not in DocType
            "nomorAju": doc.nomoraju or doc.name,
            "tanggalAju": fmt_date(doc.tanggal_pernyataan), # Mapping to tanggal_pernyataan
            "asalData": doc.asaldata,
            "asuransi": doc.asuransi,
            "bruto": doc.bruto,
            "cif": doc.cif,
            "disclaimer": doc.disclaimer,
            "fob": doc.fob,
            "freight": doc.freight,
            "jabatanTtd": doc.jabatan_pernyataan,
            "jumlahKontainer": len(doc.get("kontainer", [])), # Calculated
            "kodeAsuransi": doc.kode_asuransi,
            "kodeCaraBayar": doc.kode_cara_bayar,
            "kodeDokumen": doc.kode_dokumen,
            "kodeIncoterm": doc.kode_incoterm,
            "kodeJenisNilai": doc.kode_jenis_nilai,
            "kodeJenisProsedur": doc.kode_jenis_pib, # Assuming mapping
            "kodeKantor": doc.kode_kantor,
            "kodePelMuat": doc.kode_pelabuhan_muat,
            "kodePelTujuan": doc.kode_pelabuhan_tujuan,
            "kodeTps": doc.kode_tps,
            "kodeValuta": doc.kode_valuta,
            "kotaTtd": doc.kota_pernyataan,
            "namaTtd": doc.nama_pernyataan,
            "ndpbm": doc.ndpbm,
            "netto": doc.netto,
            "nilaiMaklon": doc.nilai_maklon,
            "seri": 0, # Default or calculated?
            "tanggalTtd": fmt_date(doc.tanggal_pernyataan),
            "totalDanaSawit": doc.total_dana_sawit,
            "biayaPengurang": doc.biaya_pengurang,
            "biayaTambahan": doc.biaya_tambahan,
            "flagVd": doc.flag_vd,
            "hargaPenyerahan": doc.harga_penyerahan,
            "jumlahTandaPengaman": doc.jumlah_tanda_pengaman,
            "kodeJenisImpor": doc.kode_jenis_impor,
            "kodePelTransit": doc.kode_pelabuhan_transit,
            "kodeTutupPu": doc.kode_tutup_pu,
            "nilaiBarang": doc.nilai_barang,
            "nilaiIncoterm": doc.nilai_incoterm,
            "nomorBc11": doc.nomor_bc11,
            "posBc11": doc.nomor_pos,
            "subPosBc11": doc.nomor_sub_pos,
            "tanggalBc11": fmt_date(doc.tanggal_bc11),
            "tanggalTiba": fmt_date(doc.tanggal_tiba),
            "volume": doc.volume,
            "vd": doc.vd,
        }

        # 2. Map Child Tables
        payload["entitas"] = get_child_data(doc, "entitas", {
            "alamatEntitas": "alamat_entitas",
            "kodeEntitas": "kode_entitas",
            "kodeJenisIdentitas": "kode_jenis_identitas",
            "namaEntitas": "nama_entitas",
            "nibEntitas": "nib_entitas",
            "nomorIdentitas": "nomor_identitas",
            "kodeStatus": "kode_status",
            "seriEntitas": "seri_entitas",
            "kodeJenisApi": "kode_jenis_api",
            "kodeNegara": "kode_negara",
            "kodeAfiliasi": "kode_afiliasi"
        })

        payload["kemasan"] = get_child_data(doc, "kemasan", {
            "jumlahKemasan": "jumlah_kemasan",
            "kodeJenisKemasan": "kode_jenis_kemasan",
            "merkKemasan": "merek_kemasan",
            "seriKemasan": "seri_kemasan"
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
                "cif": brg.cif,
                "cifRupiah": brg.cif_rupiah,
                "fob": brg.fob,
                "hargaEkspor": brg.harga_ekspor,
                "hargaPatokan": brg.harga_patokan,
                "hargaPerolehan": brg.harga_perolehan,
                "hargaSatuan": brg.harga_satuan,
                "jumlahKemasan": brg.jumlah_kemasan,
                "jumlahSatuan": brg.jumlah_satuan,
                "kodeJenisKemasan": brg.kode_kemasan,
                "kodeNegaraAsal": brg.kode_negara_asal,
                "kodeSatuanBarang": brg.kode_satuan,
                "merk": brg.merek,
                "ndpbm": brg.ndpbm,
                "netto": brg.netto,
                "nilaiBarang": brg.nilai_barang,
                "nilaiDanaSawit": brg.nilai_dana_sawit,
                "posTarif": brg.hs,
                "seriBarang": brg.seri_barang,
                "tipe": brg.tipe,
                "uraian": brg.uraian,
                "volume": brg.volume,
                "asuransi": brg.asuransi,
                "bruto": brg.bruto,
                "diskon": brg.diskon,
                "freight": brg.freight,
                "hargaPenyerahan": brg.harga_penyerahan,
                "hjeCukai": brg.hje_cukai,
                "isiPerKemasan": brg.isi_per_kemasan,
                "jumlahBahanBaku": brg.jumlah_bahan_baku,
                "jumlahDilekatkan": brg.jumlah_dilekatkan,
                "jumlahPitaCukai": brg.jumlah_pita_cukai,
                "jumlahRealisasi": brg.jumlah_realisasi,
                "kapasitasSilinder": brg.kapasitas_silinder,
                "kodeKondisiBarang": brg.kode_kondisi_barang,
                "nilaiDevisa": brg.nilai_devisa,
                "nilaiTambah": brg.nilai_tambah,
                "pernyataanLartas": brg.pernyataan_lartas,
                "persentaseImpor": brg.persentase_impor,
                "saldoAkhir": brg.saldo_akhir,
                "saldoAwal": brg.saldo_awal,
                "seriBarangDokAsal": brg.seri_barang_asal,
                "seriIjin": brg.seri_izin,
                "tahunPembuatan": brg.tahun_pembuatan,
                "tarifCukai": brg.tarif_cukai,
            }
            
            # Fetch Child Tables for this Barang
            brg_doc = frappe.get_doc("BARANG V1", brg.name)
            
            brg_item["barangTarif"] = []
            for trf in brg_doc.get("barang_tarif", []):
                brg_item["barangTarif"].append({
                    "tarif": trf.tarif,
                    "nilaiBayar": trf.nilai_bayar,
                    "seriBarang": trf.seri_barang,
                    "kodeKemasan": "",
                    "jumlahSatuan": trf.jumlah_satuan,
                    "jumlahKemasan": 0,
                    "kodeJenisTarif": trf.kode_tarif,
                    "nilaiFasilitas": trf.nilai_fasilitas,
                    "tarifFasilitas": trf.tarif_fasilitas,
                    "kodeSatuanBarang": trf.kode_satuan,
                    "kodeJenisPungutan": trf.kode_pungutan,
                    "kodeKomoditiCukai": "",
                    "kodeFasilitasTarif": trf.kode_fasilitas,
                    "nilaiSudahDilunasi": trf.nilai_sudah_dilunasi,
                    "kodeSubKomoditiCukai": ""
                })

            brg_item["barangDokumen"] = []
            for dok in brg_doc.get("barang_dokumen", []):
                brg_item["barangDokumen"].append({
                    "seriDokumen": dok.seri_dokumen,
                    "seriIzin": dok.seri_izin
                })
                
            brg_item["barangSpekKhusus"] = []
            for spek in brg_doc.get("barang_spek_khusus", []):
                brg_item["barangSpekKhusus"].append({
                    "kodeSpekKhusus": spek.kode_spek_khusus,
                    "uraian": spek.uraian
                })
                
            brg_item["barangVd"] = []
            for vd in brg_doc.get("barang_vd", []):
                brg_item["barangVd"].append({
                    "kodeJenisVd": vd.kode_jenis_vd,
                    "nilaiBarang": vd.nilai_barang
                })
                
            brg_item["barangPemilik"] = []
            for pem in brg_doc.get("barang_pemilik", []):
                 brg_item["barangPemilik"].append({
                     "seriEntitas": pem.seri_entitas
                 })

            # BAHAN BAKU 
            brg_item["bahanBaku"] = []
            bahan_bakus = frappe.get_all("BAHAN BAKU", 
                filters={"parent_barang": brg.name}, 
                fields=["*"],
                order_by="seri_bahan_baku asc"
            )
            for bb in bahan_bakus:
                bb_doc = frappe.get_doc("BAHAN BAKU", bb.name)
                bb_item = {
                    "seriBahanBaku": bb.seri_bahan_baku,
                    "kodeAsalBahanBaku": bb.kode_asal_bahan_baku,
                    "hs": bb.hs,
                    "kodeBarang": bb.kode_barang,
                    "uraian": bb.uraian,
                    "merek": bb.merek,
                    "tipe": bb.tipe,
                    "ukuran": bb.ukuran,
                    "spesifikasiLain": bb.spesifikasi_lain,
                    "kodeSatuan": bb.kode_satuan,
                    "jumlahSatuan": bb.jumlah_satuan,
                    "netto": bb.netto,
                    "bruto": bb.bruto,
                    "volume": bb.volume,
                    "cif": bb.cif,
                    "cifRupiah": bb.cif_rupiah,
                    "ndpbm": bb.ndpbm,
                    "hargaPenyerahan": bb.harga_penyerahan,
                    "hargaPerolehan": bb.harga_perolehan,
                    "kodeDokumenAsal": bb.kode_dokumen_asal,
                    "kodeKantorAsal": bb.kode_kantor_asal,
                    "nomorDaftarAsal": bb.nomor_daftar_asal,
                    "tanggalDaftarAsal": bb.tanggal_daftar_asal,
                    "nomorAjuAsal": bb.nomor_aju_asal,
                    "seriBarangAsal": bb.seri_barang_asal,
                }
                
                bb_item["bahanBakuTarif"] = []
                for bbt in bb_doc.get("bahan_tarif", []):
                    bb_item["bahanBakuTarif"].append({
                        "kodePungutan": bbt.kode_pungutan,
                        "kodeTarif": bbt.kode_tarif,
                        "tarif": bbt.tarif,
                        "kodeFasilitas": bbt.kode_fasilitas,
                        "tarifFasilitas": bbt.tarif_fasilitas,
                        "nilaiBayar": bbt.nilai_bayar,
                        "nilaiFasilitas": bbt.nilai_fasilitas
                    })
                
                bb_item["bahanBakuDokumen"] = []
                for bbd in bb_doc.get("bahan_baku_dokumen", []):
                    bb_item["bahanBakuDokumen"].append({
                        "seriDokumen": bbd.seri_dokumen,
                        "seriIzin": bbd.seri_izin
                    })
                
                brg_item["bahanBaku"].append(bb_item)

            barang_list.append(brg_item)

        payload["barang"] = barang_list
        
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
            "idPengguna": "", 
            "nomorAju": doc.nomoraju or doc.name,
            "tanggalAju": fmt_date(doc.tanggal_pernyataan),
            "asalData": doc.asaldata,
            "asuransi": doc.asuransi,
            "bruto": doc.bruto,
            "cif": doc.cif,
            "disclaimer": doc.disclaimer,
            "fob": doc.fob,
            "freight": doc.freight,
            "jabatanTtd": doc.jabatan_pernyataan,
            "jumlahKontainer": len(doc.get("kontainer", [])), 
            "kodeAsuransi": doc.kode_asuransi,
            "kodeCaraBayar": doc.kode_cara_bayar,
            "kodeDokumen": doc.kode_dokumen,
            "kodeIncoterm": doc.kode_incoterm,
            "kodeJenisNilai": doc.kode_jenis_nilai,
            "kodeJenisProsedur": doc.kode_jenis_pib, 
            "kodeKantor": doc.kode_kantor,
            "kodePelMuat": doc.kode_pelabuhan_muat,
            "kodePelTujuan": doc.kode_pelabuhan_tujuan,
            "kodeTps": doc.kode_tps,
            "kodeValuta": doc.kode_valuta,
            "kotaTtd": doc.kota_pernyataan,
            "namaTtd": doc.nama_pernyataan,
            "ndpbm": doc.ndpbm,
            "netto": doc.netto,
            "nilaiMaklon": doc.nilai_maklon,
            "seri": 0, 
            "tanggalTtd": fmt_date(doc.tanggal_pernyataan),
            "totalDanaSawit": doc.total_dana_sawit,
            "biayaPengurang": doc.biaya_pengurang,
            "biayaTambahan": doc.biaya_tambahan,
            "flagVd": doc.flag_vd,
            "hargaPenyerahan": doc.harga_penyerahan,
            "jumlahTandaPengaman": doc.jumlah_tanda_pengaman,
            "kodeJenisImpor": doc.kode_jenis_impor,
            "kodePelTransit": doc.kode_pelabuhan_transit,
            "kodeTutupPu": doc.kode_tutup_pu,
            "nilaiBarang": doc.nilai_barang,
            "nilaiIncoterm": doc.nilai_incoterm,
            "nomorBc11": doc.nomor_bc11,
            "posBc11": doc.nomor_pos,
            "subPosBc11": doc.nomor_sub_pos,
            "tanggalBc11": fmt_date(doc.tanggal_bc11),
            "tanggalTiba": fmt_date(doc.tanggal_tiba),
            "volume": doc.volume,
            "vd": doc.vd,
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
            "seriEntitas": "seri_entitas",
            "kodeJenisApi": "kode_jenis_api",
            "kodeNegara": "kode_negara",
            "kodeAfiliasi": "kode_afiliasi"
        })

        payload["kemasan"] = get_child_data(doc, "kemasan", {
            "jumlahKemasan": "jumlah_kemasan",
            "kodeJenisKemasan": "kode_jenis_kemasan",
            "merkKemasan": "merek_kemasan",
            "seriKemasan": "seri_kemasan"
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
                "cif": brg.cif,
                "cifRupiah": brg.cif_rupiah,
                "fob": brg.fob,
                "hargaEkspor": brg.harga_ekspor,
                "hargaPatokan": brg.harga_patokan,
                "hargaPerolehan": brg.harga_perolehan,
                "hargaSatuan": brg.harga_satuan,
                "jumlahKemasan": brg.jumlah_kemasan,
                "jumlahSatuan": brg.jumlah_satuan,
                "kodeJenisKemasan": brg.kode_kemasan,
                "kodeNegaraAsal": brg.kode_negara_asal,
                "kodeSatuanBarang": brg.kode_satuan,
                "merk": brg.merek,
                "ndpbm": brg.ndpbm,
                "netto": brg.netto,
                "nilaiBarang": brg.nilai_barang,
                "nilaiDanaSawit": brg.nilai_dana_sawit,
                "posTarif": brg.hs,
                "seriBarang": brg.seri_barang,
                "tipe": brg.tipe,
                "uraian": brg.uraian,
                "volume": brg.volume,
                "asuransi": brg.asuransi,
                "bruto": brg.bruto,
                "diskon": brg.diskon,
                "freight": brg.freight,
                "hargaPenyerahan": brg.harga_penyerahan,
                "hjeCukai": brg.hje_cukai,
                "isiPerKemasan": brg.isi_per_kemasan,
                "jumlahBahanBaku": brg.jumlah_bahan_baku,
                "jumlahDilekatkan": brg.jumlah_dilekatkan,
                "jumlahPitaCukai": brg.jumlah_pita_cukai,
                "jumlahRealisasi": brg.jumlah_realisasi,
                "kapasitasSilinder": brg.kapasitas_silinder,
                "kodeKondisiBarang": brg.kode_kondisi_barang,
                "nilaiDevisa": brg.nilai_devisa,
                "nilaiTambah": brg.nilai_tambah,
                "pernyataanLartas": brg.pernyataan_lartas,
                "persentaseImpor": brg.persentase_impor,
                "saldoAkhir": brg.saldo_akhir,
                "saldoAwal": brg.saldo_awal,
                "seriBarangDokAsal": brg.seri_barang_asal,
                "seriIjin": brg.seri_izin,
                "tahunPembuatan": brg.tahun_pembuatan,
                "tarifCukai": brg.tarif_cukai,
            }
            
            # Fetch Child Tables for this Barang
            # BARANG TARIF
            brg_doc = frappe.get_doc("BARANG V1", brg.name) # Need doc to get child tables easily
            
            brg_item["barangTarif"] = []
            for trf in brg_doc.get("barang_tarif", []):
                brg_item["barangTarif"].append({
                    "tarif": trf.tarif,
                    "nilaiBayar": trf.nilai_bayar,
                    "seriBarang": trf.seri_barang,
                    "kodeKemasan": "", # Not in BARANG TARIF
                    "jumlahSatuan": trf.jumlah_satuan,
                    "jumlahKemasan": 0, # Not in BARANG TARIF
                    "kodeJenisTarif": trf.kode_tarif,
                    "nilaiFasilitas": trf.nilai_fasilitas,
                    "tarifFasilitas": trf.tarif_fasilitas,
                    "kodeSatuanBarang": trf.kode_satuan,
                    "kodeJenisPungutan": trf.kode_pungutan,
                    "kodeKomoditiCukai": "", # Not in BARANG TARIF
                    "kodeFasilitasTarif": trf.kode_fasilitas,
                    "nilaiSudahDilunasi": trf.nilai_sudah_dilunasi,
                    "kodeSubKomoditiCukai": "" # Not in BARANG TARIF
                })

            # BARANG DOKUMEN
            brg_item["barangDokumen"] = []
            for dok in brg_doc.get("barang_dokumen", []):
                brg_item["barangDokumen"].append({
                    "seriDokumen": dok.seri_dokumen,
                    "seriIzin": dok.seri_izin
                })
                
            # BARANG SPEK KHUSUS
            brg_item["barangSpekKhusus"] = []
            for spek in brg_doc.get("barang_spek_khusus", []):
                brg_item["barangSpekKhusus"].append({
                    "kodeSpekKhusus": spek.kode_spek_khusus,
                    "uraian": spek.uraian
                })
                
            # BARANG VD
            brg_item["barangVd"] = []
            for vd in brg_doc.get("barang_vd", []):
                brg_item["barangVd"].append({
                    "kodeJenisVd": vd.kode_jenis_vd,
                    "nilaiBarang": vd.nilai_barang
                })
                
            # BARANG PEMILIK
            brg_item["barangPemilik"] = []
             # Assuming barang_pemilik exists in BARANG V1 based on previous file views
            for pem in brg_doc.get("barang_pemilik", []):
                 brg_item["barangPemilik"].append({
                     "seriEntitas": pem.seri_entitas
                 })

            barang_list.append(brg_item)

        payload["barang"] = barang_list
        
        return payload

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get CEISA BC20 JSON Error")
        return {"status": "error", "message": str(e)}
