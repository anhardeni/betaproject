import frappe
import requests
import json
from os import stat

SUCCESS = 200
NOT_FOUND = 400

@frappe.whitelist(allow_guest=True)
def get_all_headerq():
    headerq = frappe.qb.from_('HEADER').select('name' , 'owner', 'nomor_aju' , 'kode_dokumen' ).run(as_dict=True)
    return headerq

@frappe.whitelist(allow_guest=True)
def authenticate_and_get_token(username, password):
    auth_url = "https://example.com/api/authenticate"
    auth_data = {
        "username": username,
        "password": password
    }
    try:
        response = requests.post(auth_url, json=auth_data)
        response.raise_for_status() 
        token = response.json().get("access_token")
        if token:
            return token
        else:
            raise ValueError("No access token found in response")
    except requests.exceptions.RequestException as e:
        print("Authentication error:", e)
        return None

def get_parent_data():
    parent_data = {}
    parents = frappe.get_all("Parent", filters={"name": "Parent1"}, fields=["name"])
    for parent in parents:
        parent_name = parent.name
        children = frappe.get_all("Child", filters={"parent": parent_name}, fields=["name"])
        parent_data[parent_name] = {"children": {}}
        for child in children:
            child_name = child.name
            grandchildren = frappe.get_all("Grandchild", filters={"parent": child_name}, fields=["name"])
            parent_data[parent_name]["children"][child_name] = {"grandchildren": []}
            for grandchild in grandchildren:
                parent_data[parent_name]["children"][child_name]["grandchildren"].append(grandchild.name)
    return parent_data

def send_data_to_other_app(data, token):
    url = "https://example.com/api/data"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        print("Data sent successfully:", response.json())
    except requests.exceptions.RequestException as e:
        print("Error sending data:", e)

@frappe.whitelist(allow_guest=True)
def get_nested_data_all():
    # Implementation copied from api.py lines 100-310
    parent_data = frappe.get_doc("HEADER V2", "000020BT000120241128505790")
    entitas_data = frappe.get_list("ENTITAS",  filters={"parent": parent_data.name}, fields=[ 'seri', 'kode_entitas', 'parent', 'alamat_entitas','kode_jenis_identitas','nama_entitas','nib_entitas','nomor_identitas','nomor_ijin_entitas','tanggal_ijin_entitas'],)
    barang_data = frappe.get_list("BARANG V1", filters={"nomoraju": parent_data.name}, fields=['name','nomoraju', 'seri_barang','asuransi','cif','diskon','fob','freight','harga_ekspor','harga_penyerahan','harga_satuan','isi_per_kemasan','jumlah_kemasan','jumlah_satuan','kode_barang','kode_dokumen_asal','kode_kategori_barang','kode_negara_asal','kode_perhitungan','kode_satuan','merek','netto','nilai_barang','nilai_tambah','hs','spesifikasi_lain','tipe','ukuran','uraian','ndpbm','cif_rupiah','harga_perolehan','kode_asal_barang'],)
    barang_tarif_data = frappe.get_list("BARANG TARIF", fields=['nomoraju', 'seri_barang', 'parent','name','kode_tarif','jumlah_satuan','kode_fasilitas','kode_satuan','kode_pungutan','nilai_bayar','nilai_fasilitas','nilai_sudah_dilunasi','tarif','tarif_fasilitas'],)
    barang_dokumen_data = frappe.get_list("BARANG DOKUMEN",  fields=['seri_izin', 'seri_barang', 'parent','name'],)
    kemasan_data = frappe.get_list("KEMASAN", filters={"parent": parent_data.name}, fields=[ 'jumlah_kemasan','merek_kemasan', 'kode_kemasan','seri','name'],)
    kontainer_data = frappe.get_list("KONTAINER", filters={"parent": parent_data.name}, fields=['name','kode_jenis_kontainer','kode_tipe_kontainer','kode_ukuran_kontainer','nomor_kontainer','seri'],)
    dokumen_data = frappe.get_list("DOKUMEN", filters={"parent": parent_data.name}, fields=['name', 'kode_dokumen','nomor_dokumen','seri','tanggal_dokumen'],)
    pengangkut_data = frappe.get_list("PENGANGKUT", filters={"parent": parent_data.name}, fields=['name','call_sign','kode_bendera','nama_pengangkut','nomor_pengangkut','kode_cara_angkut','seri_pengangkut'],)

    nested_data_all = {
            "asalData": parent_data.asaldata,
            "nomorAju": parent_data.name,
            "kodeDokumen": parent_data.kode_dokumen,
            "asuransi":float(parent_data.asuransi),
            "bruto":float(parent_data.bruto),
            "cif":float(parent_data.cif),
            "fob":float(parent_data.fob),
            "freight":float(parent_data.freight),
            "hargaPenyerahan":float(parent_data.harga_penyerahan),
            "nik": parent_data.id_pengguna,
            "jabatanTtd":parent_data.jabatan_pernyataan,
            "jumlahKontainer":0,
            "kodeAsuransi":parent_data.kode_asuransi,
            "kodeIncoterm":parent_data.kode_incoterm,
            "kodeKantor": parent_data.kode_kantor,
            "kodeKantorBongkar":parent_data.kode_kantor_bongkar,
            "kodePelBongkar":parent_data.kode_pelabuhan_bongkar,
            "kodePelMuat":parent_data.kode_pelabuhan_muat,
            "kodePelTransit":parent_data.kode_pelabuhan_transit,
            "kodeTps":parent_data.kode_tps,
            "kodeTujuanTpb":parent_data.kode_tujuan_tpb,
            "kodeTutupPu":parent_data.kode_tutup_pu,
            "kodeValuta":parent_data.kode_valuta,
            "kotaTtd":parent_data.kota_pernyataan,
            "namaTtd":parent_data.nama_pernyataan,
            "ndpbm":float(parent_data.ndpbm),
            "netto":float(parent_data.netto),
            "nilaiBarang":float(parent_data.nilai_barang),	
            "nomorBc11":parent_data.nomor_bc11, 
            "posBc11":parent_data.nomor_pos,
            "seri":int(parent_data.seri_dokumen),
            "subposBc11":parent_data.nomor_sub_pos,
            "tanggalBc11":parent_data.tanggal_bc11,
            "tanggalTiba":parent_data.tanggal_tiba,
            "tanggalTtd":parent_data.tanggal_pernyataan,
            "biayaTambahan":float(parent_data.biaya_tambahan),
            "biayaPengurang":float(parent_data.biaya_pengurang),	
            "kodeKenaPajak":parent_data.kode_jasa_kena_pajak,
            "entitas": [
                {
                    "seriEntitas": int(entitas.seri),
                    "kodeEntitas": entitas.kode_entitas,
                    "alamatEntitas": entitas.alamat_entitas,
                    "kodeJenisIdentitas": entitas.kode_jenis_identitas,
                    "namaEntitas": entitas.nama_entitas,
                    "nibEntitas": entitas.nib_entitas,
                    "nomorIdentitas": entitas.nomor_identitas,
                    "nomorIjinEntitas": entitas.nomor_ijin_entitas,
                    "tanggalIjinEntitas": entitas.tanggal_ijin_entitas
                }
                for entitas in entitas_data
            ],
            "barang": [
                {
                    "Nomor_aju_brg": child.nomoraju,
                    "kode_brg": child.name,
                    "Seri_barang_brg": child.seri_barang,
                    "asuransi": float(child.asuransi),
                    "cif": float(child.cif),
                    "diskon": float(child.diskon),
                    "fob": float(child.fob),
                    "freight": float(child.freight),
                    "hargaEkspor": float(child.harga_ekspor),
                    "hargaPenyerahan": float(child.harga_penyerahan),
                    "hargaSatuan": float(child.harga_satuan),
                    "isiPerKemasan": float(child.isi_per_kemasan),
                    "jumlahKemasan": float(child.jumlah_kemasan),
                    "jumlahSatuan": float(child.jumlah_satuan),
                    "kodeBarang": child.kode_barang,
                    "kodeDokumen": child.kode_dokumen_asal,
                    "kodeKategoriBarang": child.kode_kategori_barang,
                    "kodeJenisKemasan": child.kode_jenis_kemasan,
                    "kodeNegaraAsal": child.kode_negara_asal,
                    "kodePerhitungan": child.kode_perhitungan,
                    "kodeSatuanBarang": child.kode_satuan,
                    "merk": child.merek,
                    "netto": float(child.netto),
                    "nilaiBarang": float(child.nilai_barang),
                    "nilaiTambah": float(child.nilai_tambah),
                    "posTarif": child.hs,
                    "seriBarang": child.seri_barang,
                    "spesifikasiLain": child.spesifikasi_lain,
                    "tipe": child.tipe,
                    "ukuran": child.ukuran,
                    "uraian": child.uraian,
                    "ndpbm": float(child.ndpbm),
                    "cifRupiah": float(child.cif_rupiah),
                    "hargaPerolehan": float(child.harga_perolehan),
                    "kodeAsalBahanBaku": child.kode_asal_barang,
                    "barangTarif": [
                       {
                           "kodeJenisTarif": item.kode_tarif,
                           "jumlahSatuan": float(item.jumlah_satuan),
                           "kodeFasilitasTarif": item.kode_fasilitas,
                           "kodeSatuanBarang": item.kode_satuan,
                           "kodeJenisPungutan": item.kode_pungutan,
                           "nilaiBayar": float(item.nilai_bayar),
                           "nilaiFasilitas": float(item.nilai_fasilitas),
                           "nilaiSudahDilunasi": float(item.nilai_sudah_dilunasi),
                           "seriBarang": int(item.seri_barang),
                           "tarif": float(item.tarif),
                           "tarifFasilitas": float(item.tarif_fasilitas)
                       }
                       for item in barang_tarif_data if item.parent == child.name
                    ],
                    "barangDokumen": [
                       {
                           "seriDokumen": item.seri_dokumen
                       }
                       for item in barang_dokumen_data if item.parent == child.name
                    ]
                }
                for child in barang_data
            ],
            "kemasan": [
                {
                    "jumlahKemasan": kemasan.jumlah_kemasan,
                    "kodeJenisKemasan": kemasan.kode_kemasan,
                    "merkKemasan": kemasan.merek_kemasan,
                    "seriKemasan": int(kemasan.seri)
                }
                for kemasan in kemasan_data
            ],
            "kontainer": [
                {
                    "kodeJenisKontainer": kontainer.kode_jenis_kontainer,
                    "kodeTipeKontainer": kontainer.kode_tipe_kontainer,
                    "kodeUkuranKontainer": kontainer.kode_ukuran_kontainer,
                    "nomorKontainer": kontainer.nomor_kontainer,
                    "seriKontainer": int(kontainer.seri)
                }
                for kontainer in kontainer_data
            ],
             "dokumen": [
                {
                    "kodeDokumen": dokumen.kode_dokumen,
                    "nomorDokumen": dokumen.nomor_dokumen,
                    "seriDokumen": int(dokumen.seri),
                    "tanggalDokumen": dokumen.tanggal_dokumen
                }
                for dokumen in dokumen_data
            ],
             "pengangkut": [
                {
                    "callSign": pengangkut.call_sign,
                    "kodeBendera": pengangkut.kode_bendera,
                    "namaPengangkut": pengangkut.nama_pengangkut,
                    "nomorPengangkut": pengangkut.nomor_pengangkut,
                    "kodeCaraAngkut": pengangkut.kode_cara_angkut,
                    "seriPengangkut": int(pengangkut.seri_pengangkut)
                }
                for pengangkut in pengangkut_data
            ],
    }
    return nested_data_all

@frappe.whitelist(allow_guest=True)
def get_nested_data_bc20():
    parent_data = frappe.get_doc("HEADER V2", "000020BT000120240522000060")
    entitas_data = frappe.get_list("ENTITAS",  filters={"parent": parent_data.name}, fields=[ 'seri', 'kode_entitas', 'parent', 'alamat_entitas','kode_jenis_identitas','nama_entitas','nib_entitas','nomor_identitas','nomor_ijin_entitas','tanggal_ijin_entitas'],)
    barang_data = frappe.get_list("BARANG V1", filters={"nomoraju": parent_data.name}, fields=['name','nomoraju', 'seri_barang','asuransi','cif','diskon','fob','freight','harga_ekspor','harga_penyerahan','harga_satuan','isi_per_kemasan','jumlah_kemasan','jumlah_satuan','kode_barang','kode_dokumen_asal','kode_kategori_barang','kode_negara_asal','kode_perhitungan','kode_satuan','merek','netto','nilai_barang','nilai_tambah','hs','spesifikasi_lain','tipe','ukuran','uraian','ndpbm','cif_rupiah','harga_perolehan','kode_asal_barang'],)
    barang_tarif_data = frappe.get_list("BARANG TARIF", fields=['nomoraju', 'seri_barang', 'parent','name','kode_tarif','jumlah_satuan','kode_fasilitas','kode_satuan','kode_pungutan','nilai_bayar','nilai_fasilitas','nilai_sudah_dilunasi','tarif','tarif_fasilitas'],)
    barang_dokumen_data = frappe.get_list("BARANG DOKUMEN",  fields=['seri_izin', 'seri_barang', 'parent','name'],)
    barang_spekkhusus_data = frappe.get_list("BARANG SPEK KHUSUS",  fields=['seri_barang', 'parent','name'],)
    barang_vd_data = frappe.get_list("BARANG VD",  fields=['seri_barang', 'parent','name'],)
    barang_pemilik_data = frappe.get_list("BARANG ENTITAS", fields=['seri_barang', 'parent','name'],)
    kemasan_data = frappe.get_list("KEMASAN", filters={"parent": parent_data.name}, fields=[ 'jumlah_kemasan','merek_kemasan', 'kode_kemasan','seri','name'],)
    kontainer_data = frappe.get_list("KONTAINER", filters={"parent": parent_data.name}, fields=['name','kode_jenis_kontainer','kode_tipe_kontainer','kode_ukuran_kontainer','nomor_kontainer','seri'],)
    dokumen_data = frappe.get_list("DOKUMEN", filters={"parent": parent_data.name}, fields=['name', 'kode_dokumen','nomor_dokumen','seri','tanggal_dokumen'],)
    pengangkut_data = frappe.get_list("PENGANGKUT", filters={"parent": parent_data.name}, fields=['name','call_sign','kode_bendera','nama_pengangkut','nomor_pengangkut','kode_cara_angkut','seri_pengangkut'],)

    nested_data_bc20 = {
            "asalData": parent_data.asaldata,
            "nomorAju": parent_data.name,
            "kodeDokumen": parent_data.kode_dokumen,
            "asuransi":float(parent_data.asuransi),
            "bruto":float(parent_data.bruto),
            "cif":float(parent_data.cif),
            "fob":float(parent_data.fob),
            "freight":float(parent_data.freight),
            "hargaPenyerahan":float(parent_data.harga_penyerahan),
            "nik": parent_data.id_pengguna,
            "jabatanTtd":parent_data.jabatan_pernyataan,
            "kodeAsuransi":parent_data.kode_asuransi,
            "kodeIncoterm":parent_data.kode_incoterm,
            "kodeKantor": parent_data.kode_kantor,
            "kodeKantorBongkar":parent_data.kode_kantor_bongkar,
            "kodePelBongkar":parent_data.kode_pelabuhan_bongkar,
            "kodePelMuat":parent_data.kode_pelabuhan_muat,
            "kodePelTransit":parent_data.kode_pelabuhan_transit,
            "kodeTps":parent_data.kode_tps,
            "kodeTutupPu":parent_data.kode_tutup_pu,
            "kodeValuta":parent_data.kode_valuta,
            "kotaTtd":parent_data.kota_pernyataan,
            "namaTtd":parent_data.nama_pernyataan,
            "ndpbm":float(parent_data.ndpbm),
            "netto":float(parent_data.netto),
            "nilaiBarang":float(parent_data.nilai_barang),	
            "nomorBc11":parent_data.nomor_bc11, 
            "posBc11":parent_data.nomor_pos,
            "seri":int(parent_data.seri_dokumen),
            "subposBc11":parent_data.nomor_sub_pos,
            "tanggalBc11":parent_data.tanggal_bc11,
            "tanggalTiba":parent_data.tanggal_tiba,
            "tanggalTtd":parent_data.tanggal_pernyataan,
            "biayaTambahan":float(parent_data.biaya_tambahan),
            "biayaPengurang":float(parent_data.biaya_pengurang),
            "disclaimer":parent_data.tanggal_pernyataan,
            "flagVd":parent_data.tanggal_pernyataan,
            "idPengguna":parent_data.tanggal_pernyataan,
            "jumlahTandaPengaman":int(parent_data.biaya_pengurang),
            "kodeCaraBayar":parent_data.tanggal_pernyataan,
            "kodeJenisImpor":parent_data.tanggal_pernyataan,
            "kodeJenisNilai":parent_data.tanggal_pernyataan,
            "kodeJenisProsedur":parent_data.tanggal_pernyataan,
            "kodePelTujuan":parent_data.tanggal_pernyataan,
            "nilaiIncoterm":float(parent_data.biaya_pengurang),
            "nilaiMaklon":float(parent_data.biaya_pengurang),
            "tanggalAju":parent_data.tanggal_pernyataan,
            "totalDanaSawit":float(parent_data.biaya_pengurang),
            "vd":float(parent_data.vd),
            "volume":float(parent_data.biaya_pengurang),	
            "entitas": [
                {
                    "seriEntitas": int(entitas.seri),
                    "kodeEntitas": entitas.kode_entitas,
                    "alamatEntitas": entitas.alamat_entitas,
                    "kodeJenisIdentitas": entitas.kode_jenis_identitas,
                    "namaEntitas": entitas.nama_entitas,
                    "nibEntitas": entitas.nib_entitas,
                    "nomorIdentitas": entitas.nomor_identitas,
                    "nomorIjinEntitas": entitas.nomor_ijin_entitas,
                    "tanggalIjinEntitas": entitas.tanggal_ijin_entitas
                }
                for entitas in entitas_data
            ],
            "barang": [
                {
                    "Nomor_aju_brg": child.nomoraju,
                    "kode_brg": child.name,
                    "Seri_barang_brg": child.seri_barang,
                    "asuransi": float(child.asuransi),
                    "cif": float(child.cif),
                    "diskon": float(child.diskon),
                    "fob": float(child.fob),
                    "freight": float(child.freight),
                    "hargaEkspor": float(child.harga_ekspor),
                    "hargaPenyerahan": float(child.harga_penyerahan),
                    "hargaSatuan": float(child.harga_satuan),
                    "isiPerKemasan": float(child.isi_per_kemasan),
                    "jumlahKemasan": float(child.jumlah_kemasan),
                    "jumlahSatuan": float(child.jumlah_satuan),
                    "kodeBarang": child.kode_barang,
                    "kodeDokumen": child.kode_dokumen_asal,
                    "kodeKategoriBarang": child.kode_kategori_barang,
                    "kodeJenisKemasan": child.kode_jenis_kemasan,
                    "kodeNegaraAsal": child.kode_negara_asal,
                    "kodePerhitungan": child.kode_perhitungan,
                    "kodeSatuanBarang": child.kode_satuan,
                    "merk": child.merek,
                    "netto": float(child.netto),
                    "nilaiBarang": float(child.nilai_barang),
                    "nilaiTambah": float(child.nilai_tambah),
                    "posTarif": child.hs,
                    "seriBarang": child.seri_barang,
                    "spesifikasiLain": child.spesifikasi_lain,
                    "tipe": child.tipe,
                    "ukuran": child.ukuran,
                    "uraian": child.uraian,
                    "ndpbm": float(child.ndpbm),
                    "cifRupiah": float(child.cif_rupiah),
                    "hargaPerolehan": float(child.harga_perolehan),
                    "brutto": float(child.harga_perolehan),
                    "hargaPatokan": float(child.harga_perolehan),
                    "hjeCukai": float(child.harga_perolehan),
                    "jumlahBahanBaku": float(child.harga_perolehan),
                    "jumlahDilekatkan": float(child.harga_perolehan),
                    "jumlahPitaCukai": float(child.harga_perolehan),
                    "jumlahRealisasi": float(child.harga_perolehan),
                    "kapasitasSilinder": float(child.harga_perolehan),
                    # "kodeKondisiBarang" - This line was incomplete in original file
                    "nilaiDanaSawit": float(child.harga_perolehan),
                    "nilaiDevisa": float(child.harga_perolehan),
                    # "pernyataanLartas" - This line was incomplete in original file
                    "persentaseImpor": float(child.harga_perolehan),
                    "saldoAkhir": float(child.harga_perolehan),
                    "saldoAwal": float(child.harga_perolehan),
                    # "seriBarangDokAsal" - This line was incomplete in original file
                    # "seriIjin" - This line was incomplete in original file
                    # "tahunPembuatan" - This line was incomplete in original file
                    "tarifCukai": float(child.harga_perolehan),
                    "volume": float(child.harga_perolehan),
                    "barangTarif": [
                       {
                           "kodeJenisTarif": item.kode_tarif,
                           "jumlahSatuan": float(item.jumlah_satuan),
                           "kodeFasilitasTarif": item.kode_fasilitas,
                           "kodeSatuanBarang": item.kode_satuan,
                           "kodeJenisPungutan": item.kode_pungutan,
                           "nilaiBayar": float(item.nilai_bayar),
                           "nilaiFasilitas": float(item.nilai_fasilitas),
                           "seriBarang": int(item.seri_barang),
                           "tarif": float(item.tarif),
                           "tarifFasilitas": float(item.tarif_fasilitas)
                       }
                       for item in barang_tarif_data if item.parent == child.name
                    ],
                    "barangDokumen": [
                       {
                           "seriDokumen": item.seri_dokumen
                       }
                       for item in barang_dokumen_data if item.parent == child.name
                    ],
                    "barangSpekKhusus": [
                       {
                           "seriDokumen": item.seri_barang # Original code had seri_barang mapped to seriDokumen??
                       }
                       for item in barang_spekkhusus_data if item.parent == child.name
                    ],
                    "barangPemilik": [
                       {
                           "seriDokumen": item.seri_barang
                       }
                       for item in barang_pemilik_data if item.parent == child.name
                    ],
                    "barangVd": [
                       {
                           "seriDokumen": item.seri_barang
                       }
                       for item in barang_vd_data if item.parent == child.name
                    ]
                }
                for child in barang_data
            ],
            "kemasan": [
                {
                    "jumlahKemasan": kemasan.jumlah_kemasan,
                    "kodeJenisKemasan": kemasan.kode_kemasan,
                    "merkKemasan": kemasan.merek_kemasan,
                    "seriKemasan": int(kemasan.seri)
                }
                for kemasan in kemasan_data
            ],
            "kontainer": [
                {
                    "kodeJenisKontainer": kontainer.kode_jenis_kontainer,
                    "kodeTipeKontainer": kontainer.kode_tipe_kontainer,
                    "kodeUkuranKontainer": kontainer.kode_ukuran_kontainer,
                    "nomorKontainer": kontainer.nomor_kontainer,
                    "seriKontainer": int(kontainer.seri)
                }
                for kontainer in kontainer_data
            ],
             "dokumen": [
                {
                    "kodeDokumen": dokumen.kode_dokumen,
                    "nomorDokumen": dokumen.nomor_dokumen,
                    "seriDokumen": int(dokumen.seri),
                    "tanggalDokumen": dokumen.tanggal_dokumen
                }
                for dokumen in dokumen_data
            ],
             "pengangkut": [
                {
                    "callSign": pengangkut.call_sign,
                    "kodeBendera": pengangkut.kode_bendera,
                    "namaPengangkut": pengangkut.nama_pengangkut,
                    "nomorPengangkut": pengangkut.nomor_pengangkut,
                    "kodeCaraAngkut": pengangkut.kode_cara_angkut,
                    "seriPengangkut": int(pengangkut.seri_pengangkut)
                }
                for pengangkut in pengangkut_data
            ],
    }
    return nested_data_bc20

# Aliases
get_nested_data = get_nested_data_all 
