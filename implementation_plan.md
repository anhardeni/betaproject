# Implementation Plan - Optimasi Laporan Monitoring Saldo Subkontrak

Rencana ini bertujuan untuk menyempurnakan dan mengoptimalkan laporan pabean eksisting **Monitoring Saldo Subkontrak** (`monitoring_saldo_subkontrak`) agar lebih akurat, responsif terhadap filter, dan memiliki visualisasi antarmuka (*rich styling*) yang premium sesuai kebutuhan operasional.

### ⚠️ Poin Koreksi Bisnis & Logika Kritis:
1. **Perbaikan Filter Vendor (Broken Filter):** Laporan eksisting memiliki filter `Vendor/Partner` di UI, namun nilai filter tersebut sama sekali tidak diproses di dalam query Python (`monitoring_saldo_subkontrak.py`). Kita akan memperbaikinya dengan mencocokkan field `nama_entitas` (dengan kode entitas `4` / Penerima) pada data pabean.
2. **Kalkulasi Rekonsiliasi Parsial (Logic Bug):** Query eksisting menggunakan `LIMIT 1` saat menarik data pengembalian subkontrak. Jika satu dokumen jalan keluar (BC 2.6.1) dicicil pemulangan/rekonsiliasinya dalam beberapa tahap (dokumen BC 2.6.2 parsial), maka kalkulasi saldo gantung (*outstanding*) menjadi salah. Kita akan mengubahnya menjadi fungsi agregasi `SUM`.
3. **Penyempurnaan Tampilan Visual (Aesthetics):** Kita akan menambahkan fungsi `formatter` JavaScript di sisi klien untuk mengubah teks status dan durasi jatuh tempo menjadi badge berwarna dinamis (Hijau, Kuning, Merah) agar pengguna dapat langsung mengidentifikasi stok yang kritis/terlambat.

---

## Usulan Perubahan Kode

### 1. File Backend Python: `monitoring_saldo_subkontrak.py`
* **Filter Vendor**: Kita tambahkan pengecekan filter vendor di query SQL utama:
  ```python
  if filters.get("vendor"):
      supplier_name = frappe.db.get_value("Supplier", filters.get("vendor"), "supplier_name") or filters.get("vendor")
      conditions += f" AND EXISTS (SELECT 1 FROM `tabENTITAS` WHERE parent = h.name AND kode_entitas = '4' AND nama_entitas = {frappe.db.escape(supplier_name)}) "
  ```
* **Kombinasi Pengembalian Parsial**: Kita ubah pengambilan data dari child table rekonsiliasi agar menjumlahkan (`SUM`) seluruh pengembalian yang valid daripada membatasinya ke `LIMIT 1`:
  ```python
  recon_data = frappe.db.sql(f"""
      SELECT 
          SUM(ri.qty_masuk) as total_masuk, 
          SUM(ri.qty_scrap) as total_scrap
      FROM `tabSubcontract Reconciliation Item` ri
      JOIN `tabSubcontract Reconciliation` r ON r.name = ri.parent
      WHERE r.header_keluar = '{row.header_id}' 
      AND ri.item_code = '{row.item_code}'
      AND r.docstatus = 1
  """, as_dict=1)
  ```

---

### 2. File Frontend JavaScript: `monitoring_saldo_subkontrak.js`
Kita akan menambahkan fungsi `formatter` visual pada grid laporan:
* **Kolom Status**:
  * `🔴 Overdue` jika ada saldo gantung & tanggal jatuh tempo sudah terlewati (aging < 0).
  * `🟡 Kritis` jika ada saldo gantung & waktu tersisa ≤ 7 hari.
  * `🔵 Outstanding` jika masih berjalan normal > 7 hari.
  * `🟢 Settled` jika barang sudah kembali penuh.
* **Kolom Aging**: Otomatis berwarna merah jika expired, oranye jika kritis, abu-abu jika sudah selesai (`Settled`), dan hijau jika aman.

---

## Rencana Pengujian
1. Membuka laporan **Monitoring Saldo Subkontrak** di desk ERPNext.
2. Memastikan filter **Vendor/Partner** dapat menyaring data subkontraktor secara akurat.
3. Memastikan kalkulasi saldo *BAL* tetap akurat meskipun satu pengiriman dicicil pengembaliannya 2-3 kali.
4. Memverifikasi badge warna visual (Merah/Oranye/Hijau) tampil dengan indah dan intuitif.
