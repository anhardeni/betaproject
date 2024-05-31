from os import stat
import frappe
from frappe.query_builder import DocType


SUCCESS = 200
NOT_FOUND = 400


@frappe.whitelist(allow_guest=True)
def get_all_headerg():
    headerg = frappe.db.sql("""SELECT kode_kantor_bongkar AS kodeKantorBongkar, kode_dokumen  FROM `tabHEADER V2` ;""", as_dict=True)

    return headerg

@frappe.whitelist(allow_guest=True)
def get_all_headera1():
    headera1 = frappe.db.sql("""SELECT kode_kantor_bongkar AS kodeKantorBongkar, JSON_ARRAYAGG(kode_dokumen) FROM `tabHEADER V2` ;""", as_dict=True)

    return headera1


@frappe.whitelist(allow_guest=True)
def get_all_headerq():
    #headerq = frappe.qb.Table("tabHEADER")
    headerq = frappe.qb.from_('HEADER').select('name' , 'owner', 'nomor_aju' , 'kode_dokumen' ).run(as_dict=True)
    #headerq = frappe.qb.from_('HEADER').select('name').as_('nomorAju').run(as_dict=True)
    return headerq
    #str(query)
    # SELECT "id","fname","lname","phone" FROM "tabCustomer"

    #query.get_sql()
    # SELECT "id","fname","lname","phone" FROM "tabCustomer"

    #str(query) == query.get_sql()



    #headerq = frappe.qb.DocType('HEADER')
        #filtered_data = (
            #frappe.qb.from_(headerq)
                #.select(headerq.kode_kantor_bongkar, headerq.nomoraju, headerq.name, headerq.referensi_kantor)
                #.where((customer.fname == 'Max') | customer.id.like('RA%'))
                #.where(customer.lname == 'Mustermann')
        #).run(as_dict=True)

    #return headerq

@frappe.whitelist(allow_guest=True)
def get_all_bc20():
    bc20 = frappe.db.sql("""SELECT 
    name AS nomorAju,
    kode_kantor_bongkar AS kodeKantorBongkar, 
    kode_dokumen  
    FROM `tabHEADER V2` ;""", as_dict=True)

    return bc20


@frappe.whitelist(allow_guest=True)
def get_all_bc30():
    bc30 = frappe.db.sql("""SELECT 
    asaldata	AS	asalData	,
    asuransi	AS	asuransi	,
    barang_tidak_berwujud	AS	barang_tidak_berwujud	,
    biaya_pengurang	AS	biaya_pengurang	,
    biaya_tambahan	AS	biaya_tambahan	,
    bruto	AS	bruto	,
    cif	AS	cif	,
    kode_kantor_bongkar AS kodeKantorBongkar, 
    kode_dokumen  
    FROM `tabHEADER V2`
    WHERE `tabHEADER V2`.kode_dokumen = "30"
        AND  `tabHEADER V2`.name = "000030BT000120231002000013"     ;""", as_dict=True)

    return bc30

@frappe.whitelist(allow_guest=True)
def get_all_headerq30():
    #headerq30 = frappe.qb.Table("tabHEADER")
    #headerq30 = frappe.qb.from_('HEADER').select('name' , 'owner', 'nomor_aju' , 'kode_dokumen' ).where('kode_dokumen' == '261').walk(as_dict=True)
    headerq30 = frappe.qb.from_('HEADER V2').select('name' , 'owner', 'nomoraju' , 'kode_dokumen' ).run(as_dict=True)
    #headerq30 = frappe.qb.from_('HEADER V2').select('name').as_('nomorAju').run(as_dict=True)
    return headerq30

@frappe.whitelist(allow_guest=True)
def get_all_headerl1():
    frappe.get_list("HEADER V2")
    #headerq = frappe.qb.from_('HEADER').select('name' , 'owner', 'nomor_aju' , 'kode_dokumen' ).run(as_dict=True)
    #headerq30 = frappe.qb.from_('HEADER V2').select('name').as_('nomorAju').run(as_dict=True)

@frappe.whitelist(allow_guest=True)
def get_all_bc301():
    bc301 = frappe.db.sql("""SELECT JSON_OBJECT(
        asaldata,asalData	
        , Asuransi,	Asuransi
        , kode_kantor ,	kode_Kantor 
    )
    FROM `tabHEADER V2`
         ;""", as_dict=True)

    return bc301

@frappe.whitelist(allow_guest=True)
def get_all_bctest01():
    bctest01 = frappe.db.sql("""select json_object(
        'id',p.id
        ,'desc',p.desc
        ,'child_objects',JSON_EXTRACT(IFNULL((select
        CONCAT('[',GROUP_CONCAT(
        json_object('id',c.id,'parent_id',c.parent_id,'desc',c.desc)
        ),']')   
        from `child_table` c where  c.parent_id = p.id),'[]'),'$')
        ) from `parent_table` p where p.id = 2;""", as_dict=True)

    return bctest01



frappe.whitelist(allow_guest=True)
def authenticate_and_get_token(username, password):
    auth_url = "https://example.com/api/authenticate"
    auth_data = {
        "username": username,
        "password": password
    }
    try:
        response = requests.post(auth_url, json=auth_data)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
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

    # Query to fetch parent data and its related children and grandchildren
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
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        print("Data sent successfully:", response.json())
    except requests.exceptions.RequestException as e:
        print("Error sending data:", e)

# Example usage:
    username = "your_username"
    password = "your_password"

    token = authenticate_and_get_token(username, password)
    if token:
        parent_data = get_parent_data()
        send_data_to_other_app(parent_data, token)



@frappe.whitelist(allow_guest=True)
def get_nested_data_all():    # Example: Retrieve data from Frappe doctypes
    #parent_data = frappe.get_doc("HEADER V2", "nomoraju")
    parent_data = frappe.get_doc("HEADER V2", "000023BT000120240110000050")
    entitas_data = frappe.get_list("ENTITAS",  filters={"parent": parent_data.name}, fields=[ 'seri', 'kode_entitas', 'parent', 'alamat_entitas','kode_jenis_identitas','nama_entitas','nib_entitas','nomor_identitas','nomor_ijin_entitas','tanggal_ijin_entitas'],)
    #entitas_data = parent_data.as_dict().get('ENTITAS', [])
    #entitas_data = [entitas.as_dict() for entitas in parent_data.get("nomoraju")]
    # barang_data = frappe.get_doc("BARANG V1", "000023BT000120240110000050" )
    # barang_data.as_dict()
    
    barang_data = frappe.get_list("BARANG V1", filters={"nomoraju": parent_data.name}, fields=['name','nomoraju', 'seri_barang','asuransi','cif','diskon','fob','freight','harga_ekspor','harga_penyerahan','harga_satuan','isi_per_kemasan','jumlah_kemasan','jumlah_satuan','kode_barang','kode_dokumen_asal','kode_kategori_barang','kode_negara_asal','kode_perhitungan','kode_satuan','merek','netto','nilai_barang','nilai_tambah','hs','spesifikasi_lain','tipe','ukuran','uraian','ndpbm','cif_rupiah','harga_perolehan','kode_asal_barang'],)
    barang_tarif_data = frappe.get_list("BARANG TARIF", fields=['nomoraju', 'seri_barang', 'parent','name','kode_tarif','jumlah_satuan','kode_fasilitas','kode_satuan','kode_pungutan','nilai_bayar','nilai_fasilitas','nilai_sudah_dilunasi','tarif','tarif_fasilitas'],)
    barang_dokumen_data = frappe.get_list("BARANG DOKUMEN",  fields=['seri_izin', 'seri_barang', 'parent','name'],)

    #barang_data1 = frappe.db.get_value("BARANG V1", 'TASK00002', 'subject')
    #barang_data1 = frappe.get_doc({doctype”: "BARANG V1", })
    #barang_tarif_data = frappe.get_list("BARANG TARIF", filters={"parent": barang_data1.name}, fields=['nomoraju', 'seri_barang', 'parent','name'],)
    #barang_dokumen_data = frappe.get_list("BARANG DOKUMEN", filters={"parent": barang_data1.name}, fields=['seri_izin', 'seri_barang', 'parent','name'],)
    #barangTarifItem = frappe.get_list("KEMASAN", filters={"parent": "000023BT000120240110000050"}, fields=['nomoraju', 'name'],)
    
    kemasan_data = frappe.get_list("KEMASAN", filters={"parent": parent_data.name}, fields=[ 'jumlah_kemasan','merek_kemasan', 'kode_kemasan','seri','name'],)
    kontainer_data = frappe.get_list("KONTAINER", filters={"parent": parent_data.name}, fields=['name','kode_jenis_kontainer','kode_tipe_kontainer','kode_ukuran_kontainer','nomor_kontainer','seri'],)
    dokumen_data = frappe.get_list("DOKUMEN", filters={"parent": parent_data.name}, fields=['name', 'kode_dokumen','nomor_dokumen','seri','tanggal_dokumen'],)
    pengangkut_data = frappe.get_list("PENGANGKUT", filters={"parent": parent_data.name}, fields=['name','call_sign','kode_bendera','nama_pengangkut','nomor_pengangkut','kode_cara_angkut','seri_pengangkut'],)

    # Format the data into the nested JSON structure with aliases
    nested_data_all = {
       # "data": {
            "asalData": parent_data.asaldata,  # Alias for parent field 1
            "nomorAju": parent_data.name,  # Alias for parent field 1
            "kodeDokumen": parent_data.kode_dokumen,  # Alias for parent field 2
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
                    "Nomor_aju_brg": child.nomoraju,  # Alias for child field 1
                    "kode_brg": child.name,  # Alias for child field 1
                    "Seri_barang_brg": child.seri_barang,  # Alias for child field 2
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
                           #"kode_brg": item.parent,  # Alias for grandchild field 1
                           #"grandchild_field1": item.nomoraju,  # Alias for grandchild field 1
                           #"grandchild_field2": item.seri_barang,  # Alias for grandchild field 2
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
                        #    "kode_brg": item.parent,  # Alias for grandchild field 1
                        #    "seriIzin": item.seri_izin,  # Alias for grandchild field 1
                        #    "seriBarang": item.seri_barang,  # Alias for grandchild field 2
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
                   
                    #"grandchildren": [
                    #    {
                    #        "grandchild_field1": grandchild.grandchild_field1,  # Alias for grandchild field 1
                    #        "grandchild_field2": grandchild.grandchild_field2  # Alias for grandchild field 2
                    #    }
                    #    for grandchild in grandchildren_data if grandchild.parent == child.name
                    #]
                }
                for dokumen in dokumen_data
            ],
             "pengangkut": [
                {
                    "callSign": pengangkut.call_sign, # Alias for child field 1
                    "kodeBendera": pengangkut.kode_bendera,
                    "namaPengangkut": pengangkut.nama_pengangkut,
                    "nomorPengangkut": pengangkut.nomor_pengangkut,
                    "kodeCaraAngkut": pengangkut.kode_cara_angkut,
                    "seriPengangkut": int(pengangkut.seri_pengangkut)
               
                    #"grandchildren": [
                    #    {
                    #        "grandchild_field1": grandchild.grandchild_field1,  # Alias for grandchild field 1
                    #        "grandchild_field2": grandchild.grandchild_field2  # Alias for grandchild field 2
                    #    }
                    #    for grandchild in grandchildren_data if grandchild.parent == child.name
                    #]
                }
                for pengangkut in pengangkut_data
            ],
       # }
    }

    return nested_data_all

@frappe.whitelist(allow_guest=True)
def get_nested_data_bc23():    # Example: Retrieve data from Frappe doctypes
    parent_data = frappe.get_doc("HEADER V2", "000023BT000120240110000050")
    entitas_data = frappe.get_list("ENTITAS",  filters={"parent": parent_data.name}, fields=[ 'seri', 'kode_entitas', 'parent', 'alamat_entitas','kode_jenis_identitas','nama_entitas','nib_entitas','nomor_identitas','nomor_ijin_entitas','tanggal_ijin_entitas'],)
       
    barang_data = frappe.get_list("BARANG V1", filters={"nomoraju": parent_data.name}, fields=['name','nomoraju', 'seri_barang','asuransi','cif','diskon','fob','freight','harga_ekspor','harga_penyerahan','harga_satuan','isi_per_kemasan','jumlah_kemasan','jumlah_satuan','kode_barang','kode_dokumen_asal','kode_kategori_barang','kode_negara_asal','kode_perhitungan','kode_satuan','merek','netto','nilai_barang','nilai_tambah','hs','spesifikasi_lain','tipe','ukuran','uraian','ndpbm','cif_rupiah','harga_perolehan','kode_asal_barang'],)
    barang_tarif_data = frappe.get_list("BARANG TARIF", fields=['nomoraju', 'seri_barang', 'parent','name','kode_tarif','jumlah_satuan','kode_fasilitas','kode_satuan','kode_pungutan','nilai_bayar','nilai_fasilitas','nilai_sudah_dilunasi','tarif','tarif_fasilitas'],)
    barang_dokumen_data = frappe.get_list("BARANG DOKUMEN",  fields=['seri_izin', 'seri_barang', 'parent','name'],)
     
    kemasan_data = frappe.get_list("KEMASAN", filters={"parent": parent_data.name}, fields=[ 'jumlah_kemasan','merek_kemasan', 'kode_kemasan','seri','name'],)
    kontainer_data = frappe.get_list("KONTAINER", filters={"parent": parent_data.name}, fields=['name','kode_jenis_kontainer','kode_tipe_kontainer','kode_ukuran_kontainer','nomor_kontainer','seri'],)
    dokumen_data = frappe.get_list("DOKUMEN", filters={"parent": parent_data.name}, fields=['name', 'kode_dokumen','nomor_dokumen','seri','tanggal_dokumen'],)
    pengangkut_data = frappe.get_list("PENGANGKUT", filters={"parent": parent_data.name}, fields=['name','call_sign','kode_bendera','nama_pengangkut','nomor_pengangkut','kode_cara_angkut','seri_pengangkut'],)

    # Format the data into the nested JSON structure with aliases
    nested_data_bc23 = {
       # "data": {
            "asalData": parent_data.asaldata,  # Alias for parent field 1
            "nomorAju": parent_data.name,  # Alias for parent field 1
            "kodeDokumen": parent_data.kode_dokumen,  # Alias for parent field 2
            "asuransi":float(parent_data.asuransi),
            "bruto":float(parent_data.bruto),
            "cif":float(parent_data.cif),
            "fob":float(parent_data.fob),
            "freight":float(parent_data.freight),
            "hargaPenyerahan":float(parent_data.harga_penyerahan),
            "nik": parent_data.id_pengguna,
            "jabatanTtd":parent_data.jabatan_pernyataan,
            "jumlahKontainer":int(parent_data.jumlah_kontainer),
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
                    "Nomor_aju_brg": child.nomoraju,  # Alias for child field 1
                    "kode_brg": child.name,  # Alias for child field 1
                    "Seri_barang_brg": child.seri_barang,  # Alias for child field 2
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
                   
                    #"grandchildren": [
                    #    {
                    #        "grandchild_field1": grandchild.grandchild_field1,  # Alias for grandchild field 1
                    #        "grandchild_field2": grandchild.grandchild_field2  # Alias for grandchild field 2
                    #    }
                    #    for grandchild in grandchildren_data if grandchild.parent == child.name
                    #]
                }
                for dokumen in dokumen_data
            ],
             "pengangkut": [
                {
                    "callSign": pengangkut.call_sign, # Alias for child field 1
                    "kodeBendera": pengangkut.kode_bendera,
                    "namaPengangkut": pengangkut.nama_pengangkut,
                    "nomorPengangkut": pengangkut.nomor_pengangkut,
                    "kodeCaraAngkut": pengangkut.kode_cara_angkut,
                    "seriPengangkut": int(pengangkut.seri_pengangkut)
               
                    #"grandchildren": [
                    #    {
                    #        "grandchild_field1": grandchild.grandchild_field1,  # Alias for grandchild field 1
                    #        "grandchild_field2": grandchild.grandchild_field2  # Alias for grandchild field 2
                    #    }
                    #    for grandchild in grandchildren_data if grandchild.parent == child.name
                    #]
                }
                for pengangkut in pengangkut_data
            ],
       # }
    }

    return nested_data_bc23


@frappe.whitelist(allow_guest=True)
def get_nested_data_bc20():    # Example: Retrieve data from Frappe doctypes
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

    # Format the data into the nested JSON structure with aliases
    nested_data_bc20 = {
       # "data": {
            "asalData": parent_data.asaldata,  # Alias for parent field 1
            "nomorAju": parent_data.name,  # Alias for parent field 1
            "kodeDokumen": parent_data.kode_dokumen,  # Alias for parent field 2
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
                    "Nomor_aju_brg": child.nomoraju,  # Alias for child field 1
                    "kode_brg": child.name,  # Alias for child field 1
                    "Seri_barang_brg": child.seri_barang,  # Alias for child field 2
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
                    "kodeKondisiBarang"
                    "nilaiDanaSawit": float(child.harga_perolehan),
                    "nilaiDevisa": float(child.harga_perolehan),
                    "pernyataanLartas"
                    "persentaseImpor": float(child.harga_perolehan),
                    "saldoAkhir": float(child.harga_perolehan),
                    "saldoAwal": float(child.harga_perolehan),
                    "seriBarangDokAsal"
                    "seriIjin"
                    "tahunPembuatan"
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
                           "seriDokumen": item.seri_barang
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
                   
                    #"grandchildren": [
                    #    {
                    #        "grandchild_field1": grandchild.grandchild_field1,  # Alias for grandchild field 1
                    #        "grandchild_field2": grandchild.grandchild_field2  # Alias for grandchild field 2
                    #    }
                    #    for grandchild in grandchildren_data if grandchild.parent == child.name
                    #]
                }
                for dokumen in dokumen_data
            ],
             "pengangkut": [
                {
                    "callSign": pengangkut.call_sign, # Alias for child field 1
                    "kodeBendera": pengangkut.kode_bendera,
                    "namaPengangkut": pengangkut.nama_pengangkut,
                    "nomorPengangkut": pengangkut.nomor_pengangkut,
                    "kodeCaraAngkut": pengangkut.kode_cara_angkut,
                    "seriPengangkut": int(pengangkut.seri_pengangkut)
               
                    #"grandchildren": [
                    #    {
                    #        "grandchild_field1": grandchild.grandchild_field1,  # Alias for grandchild field 1
                    #        "grandchild_field2": grandchild.grandchild_field2  # Alias for grandchild field 2
                    #    }
                    #    for grandchild in grandchildren_data if grandchild.parent == child.name
                    #]
                }
                for pengangkut in pengangkut_data
            ],
       # }
    }

    return nested_data_bc20





 