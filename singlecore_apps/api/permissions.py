import frappe

# Wajib pake whitelist agar amam dipanggil oleh tombol front-end
@frappe.whitelist()
def set_singlecore_role(target_role):
    # KEAMANAN: Cek jika yang memanggil bukan System Manager
    if "System Manager" not in frappe.get_roles(frappe.session.user):
        frappe.throw("Akses Ditolak! Hanya System Manager yang bisa mengeksekusi ini.")

    # -------------------------------------------------------------
    # 1. PARENT DOCTYPES (Transaksi Utama -> Akses: CRUD_SUBMIT)
    # -------------------------------------------------------------
    parent_doctypes = [
        "HEADER V21",
        "Inhouse V3",
        "Permohonan Perijinan Online V1",
        "Permohonan Perijinan Online V2",
        "Permohonan Perijinan Online V21"
    ]

    # -------------------------------------------------------------
    # 2. CHILD DOCTYPES (Anak langsung dari Header -> Akses: CRU)
    # -------------------------------------------------------------
    child_doctypes = [
        "Barang V1",
        "Barang",
        "Entitas",
        "Dokumen",
        "Kemasan",
        "Kontainer",
        "Jaminan",
        "Pengangkut",
        "Bank Devisa",
        "Pungutan",
        "Kesiapan Barang",
        "Komponen Biaya"
    ]

    # -------------------------------------------------------------
    # 3. GRANDCHILD DOCTYPES (Anak dari Barang / Anak dari Child -> Akses: CRU)
    # -------------------------------------------------------------
    grandchild_doctypes = [
        "Barang Tarif",
        "Barang Dokumen",
        "Barang Entitas",
        "Barang VD",
        "Barang Spek Khusus",
        "Barang Yang Akan Dimasukkan",
        "Barang Yang Dihasilkan",
        "Barang Yang Dikirim",
        "Bahan Baku",
        "Bahan Baku Tarif",
        "Bahan Baku Dokumen",
        "Barang Bahan Sisa Potongan",
        "Barang Bahan Yang Ditambahkan"
    ]

    # -------------------------------------------------------------
    # 4. REFERENCE / MASTER DOCTYPES (Data Setup -> Akses: READ ONLY)
    # (Pegawai biasa hanya boleh baca list valuta, pelabuhan, dsb)
    # -------------------------------------------------------------
    reference_doctypes = [
        "Referensi Asal Barang",
        "Referensi Asal Barang FTZ",
        "Referensi Bank",
        "Referensi Cara Angkut",
        "Referensi Cara Bayar",
        "Referensi Cara Dagang",
        "Referensi Catatan Petugas",
        "Referensi Catatan Petugas1",
        "Referensi Daerah Asal",
        "Referensi Dokumen",
        "Referensi Entitas",
        "Referensi Fasilitas",
        "Referensi Fasilitas Tarif",
        "Referensi Fasilitas Tarif Baru",
        "Referensi Gudang",
        "Referensi HS 2022 v1",
        "Referensi Ijin",
        "Referensi Incoterm",
        "Referensi Jenis API",
        "Referensi Jenis Ekspor",
        "Referensi Jenis Identitas",
        "Referensi Jenis Impor",
        "Referensi Jenis Jaminan",
        "Referensi Jenis Kemasan",
        "Referensi Jenis Kontainer",
        "Referensi Jenis Pengangkutan",
        "Referensi Jenis Pib",
        "Referensi Jenis Pungutan",
        "Referensi Jenis Tarif",
        "Referensi Jenis TPB",
        "Referensi Jenis Transaksi Perdagangan",
        "Referensi Jenis VD",
        "Referensi Kantor",
        "Referensi Kapal",
        "Referensi Kategori Barang",
        "Referensi Kategori Ekspor",
        "Referensi Kategori Keluar FTZ",
        "Referensi Kategori Konsolidator",
        "Referensi Komoditi Cukai",
        "Referensi Kondisi Barang",
        "Referensi Layanan",
        "Referensi Layanan Fix",
        "Referensi Lokasi Bayar",
        "Referensi Negara",
        "Referensi Pelabuhan Dalam Negeri",
        "Referensi Pelabuhan Luar Negeri",
        "Referensi Putusan Petugas",
        "Referensi Respon",
        "Referensi Satuan Barang",
        "Referensi Spesifikasi Khusus",
        "Referensi Spesifikasi Khusus Detail",
        "Referensi Status",
        "Referensi Status Pengusaha",
        "Referensi Tipe Kontainer",
        "Referensi Tujuan Pemasukan",
        "Referensi Tujuan Pengeluaran",
        "Referensi Tujuan Pengiriman",
        "Referensi Tutup Pu",
        "Referensi Ukuran Kontainer",
        "Referensi Valuta"  
        # Anda dapat menambahkan referensi lainnya...
    ]

    # =================== LOKUS FUNGSI INJEKSI ===================
    # Gunakan fungsi inner karena list-list di atas spesifik ke Singlecore
    def inject_permissions(doctype_list, perm_type):
        for dt in doctype_list:
            if not frappe.db.exists("DocType", dt):
                continue
                
            doc = frappe.get_doc("DocType", dt)
            
            # Hapus dulu jika role sudah pernah ada (agar menimpa / update)
            doc.permissions = [p for p in doc.permissions if p.role != target_role]
            
            # Konfigurasi Akses Berdasarkan Kategori
            perm_rule = {
                "role": target_role,
                "permlevel": 0,
                "read": 1,
                "export": 1
            }
            
            if perm_type == "CRUD":
                perm_rule.update({"write": 1, "create": 1, "delete": 1})
            elif perm_type == "CRU":
                perm_rule.update({"write": 1, "create": 1, "delete": 0})
            elif perm_type == "READ_ONLY":
                perm_rule.update({"write": 0, "create": 0, "delete": 0})
                
            # PENTING: Frappe akan error (Cannot set Assign Submit if not Submittable)
            # jika sebuah DocType tidak di-set *is_submittable = 1* tapi kita paksa beri permission submit
            if getattr(doc, "is_submittable", 0):
                if perm_type == "CRUD":
                    perm_rule.update({"submit": 1, "cancel": 1})
                else:
                    perm_rule.update({"submit": 0, "cancel": 0})
                
            doc.append("permissions", perm_rule)
            doc.save(ignore_permissions=True)

    # Eksekusi fungsi injeksi untuk masing-masing kategori
    inject_permissions(parent_doctypes, "CRUD")
    inject_permissions(child_doctypes, "CRU")
    inject_permissions(grandchild_doctypes, "CRU")
    inject_permissions(reference_doctypes, "READ_ONLY")

    # Kembalikan response sukses
    return {"status": "success", "message": f"Sukses memasang rules untuk Role {target_role}"}
