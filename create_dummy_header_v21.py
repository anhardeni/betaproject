#!/usr/bin/env python3
"""
Script to create dummy data for HEADER V21 (BC20 - Pemberitahuan Impor Barang)
This creates a complete BC20 document with all necessary fields and child tables
"""

import frappe
from frappe.utils import now_datetime, today, add_days
import random

def create_dummy_header_v21():
    """Create a complete dummy HEADER V21 document"""
    
    print("🚀 Creating dummy HEADER V21 document...")
    
    # Create the header document
    doc = frappe.get_doc({
        "doctype": "HEADER V21",
        
        # Basic Information
        "asaldata": "S",  # S = Swadana (Self Declaration)
        "disclaimer": "1",  # 1 = Agree
        "kode_dokumen": "20",  # BC20 - PIB (Pemberitahuan Impor Barang)
        "kode_dokumen4digit": "0020",
        
        # Kantor & Location
        "kode_kantor": "050100",  # Example: Kantor Bea Cukai
        "kode_kantor_bongkar": "050100",
        
        # Pernyataan (Declaration)
        "kota_pernyataan": "Jakarta",
        "tanggal_pernyataan": today(),
        "nama_pernyataan": "John Doe",
        "jabatan_pernyataan": "Direktur",
        
        # Jenis PIB & Import
        "kode_jenis_pib": "1",  # 1 = Biasa, 2 = Berkala
        "kode_jenis_impor": "1",  # Regular Import
        
        # BC11 Information (Bill of Lading)
        "nomor_bc11": "BC11/2024/001234",
        "tanggal_bc11": add_days(today(), -7),
        "nomor_pos": "1",
        "nomor_sub_pos": "1",
        
        # Pelabuhan & Transport
        "kode_pelabuhan_bongkar": "IDTPP",  # Tanjung Priok
        "kode_pelabuhan_muat": "SGSIN",  # Singapore
        "kode_tps": "TPSA",  # TPS Code
        
        # Dates
        "tanggal_tiba": add_days(today(), -5),
        "tanggal_muat": add_days(today(), -10),
        
        # Financial Information
        "kode_valuta": "USD",
        "kode_incoterm": "CIF",
        "ndpbm": 15750.00,  # NDPBM rate (example)
        
        # Costs (in USD)
        "nilai_barang": 10000.00,
        "freight": 500.00,
        "asuransi": 100.00,
        "biaya_tambahan": 50.00,
        "biaya_pengurang": 0.00,
        
        # Calculated values
        "fob": 10000.00,
        "cif": 10650.00,  # FOB + Freight + Insurance + Extra
        "harga_penyerahan": 10650.00,
        
        # Weight & Volume
        "bruto": 1250.50,  # KG
        "netto": 1200.00,  # KG
        "volume": 2.5,  # M3
        
        # Flags
        "flag_curah": "2",  # 2 = Non Curah
        "flag_migas": "2",  # 2 = Non Migas
        "kode_asuransi": "LN",  # Luar Negeri
        
        # Cara Bayar & Dagang
        "kode_cara_bayar": "1",  # TT (Telegraphic Transfer)
        "kode_cara_dagang": "1",  # Regular Trade
        
        # Child Tables (will be added after save)
    })
    
    # Insert the document
    doc.insert()
    print(f"✅ Created HEADER V21: {doc.name}")
    
    # Add ENTITAS (Entities)
    add_entitas(doc)
    
    # Add KEMASAN (Packaging)
    add_kemasan(doc)
    
    # Add DOKUMEN (Supporting Documents)
    add_dokumen(doc)
    
    # Add PENGANGKUT (Transport)
    add_pengangkut(doc)
    
    # Save the document
    doc.save()
    print(f"💾 Saved all child tables")
    
    # Submit the document (optional)
    # doc.submit()
    # print(f"📤 Submitted document")
    
    return doc

def add_entitas(doc):
    """Add entity records (Importir, Pemilik, etc.)"""
    print("  Adding ENTITAS...")
    
    # Importir
    doc.append("entitas", {
        "seri": 1,
        "kode_entitas": "1",  # 1 = Importir
        "nama_entitas": "PT Importir Sejahtera",
        "alamat_entitas": "Jl. Sudirman No. 123, Jakarta",
        "nomor_identitas": "01.234.567.8-901.000",
        "kode_jenis_identitas": "4",  # 4 = NPWP
    })
    
    # Pemilik Barang
    doc.append("entitas", {
        "seri": 2,
        "kode_entitas": "2",  # 2 = Pemilik
        "nama_entitas": "PT Pemilik Barang Indonesia",
        "alamat_entitas": "Jl. Thamrin No. 456, Jakarta",
        "nomor_identitas": "01.987.654.3-210.000",
        "kode_jenis_identitas": "4",
    })
    
    print("  ✅ Added 2 ENTITAS")

def add_kemasan(doc):
    """Add packaging records"""
    print("  Adding KEMASAN...")
    
    doc.append("kemasan", {
        "seri": 1,
        "kode_kemasan": "PK",  # Pallet Kayu
        "jumlah_kemasan": 10,
        "merek_kemasan": "ABC CARGO"
    })
    
    doc.append("kemasan", {
        "seri": 2,
        "kode_kemasan": "CT",  # Carton
        "jumlah_kemasan": 50,
        "merek_kemasan": "XYZ LOGISTICS"
    })
    
    print("  ✅ Added 2 KEMASAN")

def add_dokumen(doc):
    """Add supporting documents"""
    print("  Adding DOKUMEN...")
    
    # Invoice
    doc.append("dokumen", {
        "seri": 1,
        "kode_dokumen": "380",  # Commercial Invoice
        "nomor_dokumen": "INV/2024/001234",
        "tanggal_dokumen": add_days(today(), -15)
    })
    
    # Bill of Lading
    doc.append("dokumen", {
        "seri": 2,
        "kode_dokumen": "705",  # Bill of Lading
        "nomor_dokumen": "BL/SG/2024/5678",
        "tanggal_dokumen": add_days(today(), -12)
    })
    
    # Packing List
    doc.append("dokumen", {
        "seri": 3,
        "kode_dokumen": "271",  # Packing List
        "nomor_dokumen": "PL/2024/001234",
        "tanggal_dokumen": add_days(today(), -15)
    })
    
    print("  ✅ Added 3 DOKUMEN")

def add_pengangkut(doc):
    """Add transport information"""
    print("  Adding PENGANGKUT...")
    
    doc.append("pengangkut", {
        "seri_pengangkut": 1,
        "kode_cara_angkut": "1",  # 1 = Laut (Sea)
        "nama_pengangkut": "MV. OCEAN EXPRESS",
        "nomor_pengangkut": "IMO1234567",  # Voyage number
        "kode_bendera": "SG",  # Singapore flag
    })
    
    print("  ✅ Added 1 PENGANGKUT")

def create_dummy_barang_v1(header_name):
    """Create dummy BARANG V1 linked to the header"""
    print(f"\n📦 Creating dummy BARANG V1 for {header_name}...")
    
    barang = frappe.get_doc({
        "doctype": "BARANG V1",
        "nomoraju": header_name,
        
        # Basic Info
        "seri_barang": 1,
        "hs": "8471.30.10",  # HS Code for Laptop
        "uraian": "LAPTOP COMPUTER, INTEL CORE I7, 16GB RAM, 512GB SSD",
        
        # Quantity & Weight
        "jumlah_satuan": 100,  # 100 units
        "kode_satuan": "PCE",  # Piece
        "netto": 250.00,  # KG
       "bruto": 300.00,  # KG
        
        # Values (USD)
        "harga_satuan": 800.00,
        "nilai_barang": 80000.00,  # 100 * 800
        "fob": 80000.00,
        "freight": 400.00,
        "asuransi": 80.00,
        "cif": 80480.00,
        
        # CIF in Rupiah (using NDPBM)
        "cif_rupiah": 80480.00 * 15750.00,  # CIF * NDPBM
        
        # Origin
        "kode_negara_asal": "SG",  # Singapore
        "kode_asal_barang": "1",  # Import
        
        # Category
        "kode_kategori_barang": "I",  # Import
    })
    
    barang.insert()
    print(f"✅ Created BARANG V1: {barang.name}")
    
    # Add BARANG TARIF
    add_barang_tarif(barang)
    
    # Add BARANG DOKUMEN
    add_barang_dokumen(barang)
    
    barang.save()
    print(f"💾 Saved BARANG V1 with child tables")
    
    return barang

def add_barang_tarif(barang):
    """Add tariff records to BARANG V1"""
    print("  Adding BARANG TARIF...")
    
    # Bea Masuk (Import Duty)
    barang.append("barang_tarif", {
        "nomoraju": barang.nomoraju,
        "seri_barang": barang.seri_barang,
        "kode_pungutan": "BM",
        "kode_tarif": "1",  # Tarif Umum
        "tarif": 5.00,  # 5%
        "kode_satuan": "PCE",
        "jumlah_satuan": 100,
        "nilai_bayar": 4024.00,  # 5% of CIF
    })
    
    # PPN (Value Added Tax)
    barang.append("barang_tarif", {
        "nomoraju": barang.nomoraju,
        "seri_barang": barang.seri_barang,
        "kode_pungutan": "PPN",
        "kode_tarif": "1",
        "tarif": 11.00,  # 11%
        "kode_satuan": "PCE",
        "jumlah_satuan": 100,
        "nilai_bayar": 9325.28,  # 11% of (CIF + BM)
    })
    
    # PPh (Income Tax)
    barang.append("barang_tarif", {
        "nomoraju": barang.nomoraju,
        "seri_barang": barang.seri_barang,
        "kode_pungutan": "PPH",
        "kode_tarif": "1",
        "tarif": 2.50,  # 2.5%
        "kode_satuan": "PCE",
        "jumlah_satuan": 100,
        "nilai_bayar": 2012.00,  # 2.5% of CIF
    })
    
    print("  ✅ Added 3 BARANG TARIF (BM, PPN, PPh)")

def add_barang_dokumen(barang):
    """Add document links to BARANG V1"""
    print("  Adding BARANG DOKUMEN...")
    
    # Link to Invoice (seri 1 from HEADER)
    barang.append("barang_dokumen", {
        "nomoraju": barang.nomoraju,
        "seri_barang": barang.seri_barang,
        "seri_dokumen": 1,  # Invoice
    })
    
    # Link to Packing List (seri 3 from HEADER)
    barang.append("barang_dokumen", {
        "nomoraju": barang.nomoraju,
        "seri_barang": barang.seri_barang,
        "seri_dokumen": 3,  # Packing List
    })
    
    print("  ✅ Added 2 BARANG DOKUMEN")

if __name__ == "__main__":
    # Run the script
    try:
        # Create HEADER V21
        header = create_dummy_header_v21()
        
        # Create BARANG V1
        barang = create_dummy_barang_v1(header.name)
        
        print(f"\n🎉 SUCCESS! Created complete BC20 document:")
        print(f"   📄 HEADER V21: {header.name}")
        print(f"   📦 BARANG V1: {barang.name}")
        print(f"\n✅ You can now open this document in ERPNext!")
        print(f"   URL: /app/header-v21/{header.name}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
