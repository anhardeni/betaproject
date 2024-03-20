# generated by datamodel-codegen:
#   filename:  bc23.json
#   timestamp: 2024-01-25T01:50:21+00:00

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field, confloat, constr


class KodeAsuransi(Enum):
    LN = 'LN'
    DN = 'DN'


class KodeTutupPu(Enum):
    field_11 = '11'
    field_12 = '12'
    field_14 = '14'


class KodeKenaPajak(Enum):
    field_1 = '1'
    field_2 = '2'


class KodePerhitungan(Enum):
    field_0 = '0'
    field_1 = '1'


class KodeAsalBahanBaku(Enum):
    field_0 = '0'
    field_1 = '1'


class KodeJenisTarif(Enum):
    field_1 = '1'
    field_2 = '2'


class BarangTarifItem(BaseModel):
    kodeJenisTarif: KodeJenisTarif = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - Jenis Tarif. Referensi Jenis Tarif: [1] Advalorum atau [2] Spesifik',
    )
    jumlahSatuan: confloat(multiple_of=0.01) = Field(
        ..., description='jumlah satuan barang tarif BM'
    )
    kodeFasilitasTarif: str = Field(
        ...,
        description='Kode fasilitas tarif BM. Sesuai kolom formulir BC 2.3 - B.37 Kode Fasilitas. Lihat Referensi Fasilitas Tarif',
    )
    kodeSatuanBarang: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.38 Jenis Satuan Barang. Lihat Referensi Satuan Barang',
    )
    kodeJenisPungutan: str = Field(
        'BM', const=True, description='Set kode jenis pungutan Bea Masuk (BM)'
    )
    nilaiBayar: confloat(multiple_of=0.01) = Field(
        ..., description='nilai bayar barang tarif BM'
    )
    nilaiFasilitas: confloat(multiple_of=0.01) = Field(
        ...,
        description='Nilai fasilitas tarif BM. Sesuai kolom formulir BC 2.3 - B37. Tarif dan Fasilitas',
    )
    nilaiSudahDilunasi: confloat(multiple_of=0.01) = Field(
        ..., description='Nilai sudah dilunasi'
    )
    seriBarang: int = Field(..., description='seri barang')
    tarif: confloat(multiple_of=0.01) = Field(
        ..., description='Tarif BM. Sesuai kolom formulir BC 2.3 - B.37 Tarif'
    )
    tarifFasilitas: confloat(multiple_of=0.01) = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.37 Tarif dan Fasilitas. Dapat diisi apabila Kode Fasilitas Tarif selain dibayar [1]',
    )


class BarangTarifItem1(BaseModel):
    kodeJenisTarif: KodeJenisTarif = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - Jenis Tarif. Referensi Jenis Tarif: [1] Advalorum atau [2] Spesifik',
    )
    jumlahSatuan: confloat(multiple_of=0.01) = Field(
        ..., description='jumlah satuan barang tarif PPH'
    )
    kodeFasilitasTarif: str = Field(
        ...,
        description='Kode fasilitas tarif PPH. Sesuai kolom formulir BC 2.3 - B37. Kode Fasilitas. Lihat Referensi Fasilitas Tarif',
    )
    kodeSatuanBarang: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.38 Jenis Satuan Barang. Lihat Referensi Satuan Barang',
    )
    kodeJenisPungutan: str = Field(
        'PPH', const=True, description='Set kode jenis pungutan Pajak Penghasilan (PPh)'
    )
    nilaiBayar: confloat(multiple_of=0.01) = Field(
        ..., description='nilai bayar barang tarif PPH'
    )
    nilaiFasilitas: confloat(multiple_of=0.01) = Field(
        ...,
        description='Nilai fasilitas tarif PPH. Sesuai kolom formulir BC 2.3 - B37. Tarif dan Fasilitas',
    )
    nilaiSudahDilunasi: confloat(multiple_of=0.01) = Field(
        ..., description='Nilai sudah dilunasi'
    )
    seriBarang: int = Field(..., description='seri barang')
    tarif: confloat(multiple_of=0.01) = Field(
        ..., description='Tarif PPH. Sesuai kolom formulir BC 2.3 - B37. Tarif'
    )
    tarifFasilitas: confloat(multiple_of=0.01) = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B37. Tarif dan Fasilitas. Dapat diisi apabila Kode Fasilitas Tarif selain dibayar [1]',
    )


class BarangTarifItem2(BaseModel):
    kodeJenisTarif: KodeJenisTarif = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - Jenis Tarif. Referensi Jenis Tarif: [1] Advalorum atau [2] Spesifik',
    )
    jumlahSatuan: confloat(multiple_of=0.01) = Field(
        ..., description='jumlah satuan barang tarif PPN'
    )
    kodeFasilitasTarif: str = Field(
        ...,
        description='Kode fasilitas tarif PPN. Sesuai kolom formulir BC 2.3 - B37. Kode Fasilitas. Lihat Referensi Fasilitas Tarif',
    )
    kodeSatuanBarang: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B38. jenis Satuan Barang. Lihat Referensi Satuan Barang',
    )
    kodeJenisPungutan: str = Field(
        'PPN',
        const=True,
        description='Set kode jenis pungutan Pajak Pertambahan Nilai (PPN)',
    )
    nilaiBayar: confloat(multiple_of=0.01) = Field(
        ..., description='nilai bayar barang tarif PPN'
    )
    nilaiFasilitas: confloat(multiple_of=0.01) = Field(
        ...,
        description='Nilai fasilitas tarif PPN. Sesuai kolom formulir BC 2.3 - B37. Tarif dan Fasilitas',
    )
    nilaiSudahDilunasi: confloat(multiple_of=0.01) = Field(
        ..., description='Nilai sudah dilunasi'
    )
    seriBarang: int = Field(..., description='seri barang')
    tarif: confloat(multiple_of=0.01) = Field(
        ..., description='Tarif PPN. Sesuai kolom formulir BC 2.3 - B37. Tarif'
    )
    tarifFasilitas: confloat(multiple_of=0.01) = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B37. Tarif dan Fasilitas. Dapat diisi apabila Kode Fasilitas Tarif selain dibayar [1]',
    )


class BarangTarifItem3(BaseModel):
    kodeJenisTarif: Optional[KodeJenisTarif] = Field(
        None,
        description='Sesuai kolom formulir BC 2.3- B.37 Jenis Tarif/Pembebanan. Referensi Jenis Tarif: [1] Advalorum atau [2] Spesifik',
    )
    jumlahSatuan: Optional[confloat(multiple_of=0.01)] = Field(
        None, description='jumlah satuan barang tarif'
    )
    kodeFasilitasTarif: Optional[str] = Field(
        None,
        description='Sesuai kolom formulir BC 2.3 - B.37 Kode Fasilitas. Lihat Referensi Fasilitas Tarif',
    )
    kodeJenisPungutan: Optional[str] = Field(
        None,
        description='Sesuai kolom formulir BC 2.3 - B.37 Tarif dan Fasilitas. Lihat Referensi Jenis Pungutan',
    )
    nilaiBayar: Optional[confloat(multiple_of=0.01)] = Field(
        None, description='nilai bayar barang tarif'
    )
    seriBarang: Optional[int] = Field(None, description='seri barang')
    tarif: Optional[confloat(multiple_of=0.01)] = Field(
        None, description='Sesuai kolom formulir BC 2.3 - B.37 Tarif'
    )
    tarifFasilitas: Optional[confloat(multiple_of=0.01)] = Field(
        None, description='Sesuai kolom formulir BC 2.3 - B.37 Tarif dan Fasilitas'
    )
    nilaiFasilitas: Optional[confloat(multiple_of=0.01)] = Field(
        None,
        description='Sesuai kolom formulir BC 2.3 - D.37 Tarif dan Fasilitas. Dapat diisi apabila Kode Fasilitas Tarif selain dibayar [1]',
    )


class BarangDokuman(BaseModel):
    seriDokumen: Optional[str] = Field(None, description='seri dokumen')


class BarangItem(BaseModel):
    idBarang: Optional[str] = Field(None, description='Identitas barang')
    asuransi: float = Field(..., description='nilai asuransi')
    cif: float = Field(..., description='harga cif')
    diskon: float = Field(..., description='diskon')
    fob: float = Field(..., description='free on board')
    freight: float = Field(..., description='freight')
    hargaEkspor: float = Field(..., description='harga ekspor')
    hargaPenyerahan: float = Field(..., description='harga penyerahan barang')
    hargaSatuan: float = Field(..., description='harga satuan barang')
    isiPerKemasan: int = Field(..., description='isi per kemasan')
    jumlahKemasan: confloat(multiple_of=0.01) = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.30 Jumlah Kemasan'
    )
    jumlahSatuan: confloat(multiple_of=0.0001) = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.38 Jumlah Satuan'
    )
    kodeBarang: str = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.34 Kode barang'
    )
    kodeDokumen: str = Field(..., description='Lihat Referensi Dokumen')
    kodeKategoriBarang: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.35 Kategori Barang. Lihat Referensi Kategori Barang',
    )
    kodeJenisKemasan: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.34 Jenis Kemasan. Lihat Referensi Jenis Kemasan',
    )
    kodeNegaraAsal: constr(regex=r'^[A-Z]{2}$') = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.36 Negara Asal. Lihat Referensi Negara',
    )
    kodePerhitungan: KodePerhitungan = Field(
        ...,
        description='Lihat Referensi Cara Perhitungan: [0] Harga Pemasukan atau [1] Harga Pengeluaran',
    )
    kodeSatuanBarang: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.38 Jenis Satuan. Lihat Referensi Satuan Barang',
    )
    merk: str = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.34 Merk Barang'
    )
    netto: confloat(multiple_of=0.0001) = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.38 Berat Bersih (Kg)'
    )
    nilaiBarang: confloat(multiple_of=0.01) = Field(..., description='nilai barang')
    nilaiTambah: float = Field(..., description='nilai tambah')
    posTarif: str = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.34 Pos Tarif/HS'
    )
    seriBarang: int = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.33 No. Seri data barang'
    )
    spesifikasiLain: str = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.34 Spesifikasi Lain'
    )
    tipe: str = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.34 Tipe Barang'
    )
    ukuran: str = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.34 Ukuran Barang'
    )
    uraian: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.34 Uraian barang secara lengkap',
    )
    ndpbm: float = Field(..., description='nilai dasar penghitungan bea masuk')
    cifRupiah: float = Field(..., description='harga cif rupiah')
    hargaPerolehan: float = Field(..., description='harga perolehan barang')
    kodeAsalBahanBaku: KodeAsalBahanBaku = Field(
        ..., description='kode asal bahan baku: [0] Impor atau [1] Lokal'
    )
    barangTarif: List[
        Union[BarangTarifItem, BarangTarifItem1, BarangTarifItem2, BarangTarifItem3]
    ] = Field(..., description='data barang tarif per barang')
    barangDokumen: List[BarangDokuman] = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.34 Surat Keputusan/Dokumen Lainnya',
    )


class KodeJenisIdentitas(Enum):
    field_0 = '0'
    field_1 = '1'
    field_2 = '2'
    field_3 = '3'
    field_4 = '4'
    field_5 = '5'


class Entita(BaseModel):
    alamatEntitas: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.3 Alamat Importir/Pengusaha TPB',
    )
    kodeEntitas: str = Field(
        '3',
        const=True,
        description='Set kode entitas Pengusaha (3). Mengacu pada Referensi Entitas',
    )
    kodeJenisIdentitas: KodeJenisIdentitas = Field(
        ...,
        description='Referensi Jenis Identitas: [0] NPWP 12 Digit, [1] NPWP 10 Digit, [2] Paspor, [3] KTP, [4] Lainnya, [5] NPWP 15 Digit',
    )
    namaEntitas: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.3 Nama Importir/Pengusaha TPB',
    )
    nibEntitas: str = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.5 API. Angka Pengenal Impor'
    )
    nomorIdentitas: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.2 Identitas Importir/Pengusaha TPB',
    )
    nomorIjinEntitas: str = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.4 No Izin TPB'
    )
    tanggalIjinEntitas: date = Field(..., description='Tanggal izin TPB')
    seriEntitas: int = Field(..., description='seri entitas')


class Entita1(BaseModel):
    alamatEntitas: str = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.1 Alamat Pemasok'
    )
    kodeEntitas: str = Field(
        '5',
        const=True,
        description='Set kode entitas pemasok (7). Mengacu pada Referensi Entitas',
    )
    kodeNegara: constr(regex=r'^[A-Za-z]{2}$') = Field(
        ..., description='Lihat Referensi Negara'
    )
    namaEntitas: str = Field(
        ..., description='Sesuai kolom formulir BC 2.0 - B.1 Nama Pemasok'
    )
    seriEntitas: int = Field(..., description='seri entitas')


class KodeStatus(Enum):
    field_0 = '0'
    field_1 = '1'
    field_2 = '2'
    field_3 = '3'
    field_4 = '4'
    field_5 = '5'
    field_6 = '6'
    field_7 = '7'
    field_8 = '8'
    field_9 = '9'
    field_10 = '10'


class Entita2(BaseModel):
    alamatEntitas: str = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - D.6 Alamat Pemilik Barang'
    )
    kodeEntitas: str = Field(
        '7',
        const=True,
        description='Set kode entitas pemilik barang (7). Mengacu pada Referensi Entitas',
    )
    kodeJenisApi: str
    kodeJenisIdentitas: KodeJenisIdentitas = Field(
        ...,
        description='Referensi Jenis Identitas: [0] NPWP 12 Digit, [1] NPWP 10 Digit, [2] Paspor, [3] KTP, [4] Lainnya, [5] NPWP 15 Digit',
    )
    kodeStatus: KodeStatus = Field(
        ...,
        description='Referensi Kode Status Pengusaha: [1] KOPERASI, [2] PMDN (MIGAS), [3] PMDN (NON MIGAS), [4] PMA (MIGAS), [5] PMA (NON MIGAS), [6] BUMN, [7] BUMD, [8] PERORANGAN, [9] USAHA KECIL, MIKRO DAN MENENGAH, [10] LAINNYA',
    )
    namaEntitas: str = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.7 Nama Pemilik Barang'
    )
    nomorIdentitas: str = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.6 Identitas Pemilik Barang'
    )
    nomorIjinEntitas: str = Field(..., description='Nomor ijin entitas')
    tanggalIjinEntitas: date = Field(..., description='Tanggal ijin entitas')
    seriEntitas: int = Field(..., description='seri entitas')


class KemasanItem(BaseModel):
    jumlahKemasan: int = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.30 Jumlah Kemasan'
    )
    kodeJenisKemasan: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.30 Jenis Kemasan. Lihat Referensi Jenis Kemasan',
    )
    seriKemasan: int = Field(
        ..., description='seri data kemasan berdasarkan data yang dimasukkan'
    )
    merkKemasan: str = Field(..., description='Merek kemasan')


class KodeTipeKontainer(Enum):
    field_1 = '1'
    field_2 = '2'
    field_3 = '3'
    field_4 = '4'
    field_5 = '5'
    field_6 = '6'
    field_7 = '7'
    field_8 = '8'
    field_99 = '99'


class KodeUkuranKontainer(Enum):
    field_20 = '20'
    field_40 = '40'
    field_45 = '45'
    field_60 = '60'


class KodeJenisKontainer(Enum):
    field_4 = '4'
    field_7 = '7'
    field_8 = '8'


class KontainerItem(BaseModel):
    kodeTipeKontainer: Optional[KodeTipeKontainer] = Field(
        None,
        description='Sesuai kolom formulir BC 2.3 - B.29 Tipe Peti Kemas. Referensi Tipe Kontainer: [1] General/Dry Cargo, [2] Tunne Type, [3] Open Top Steel, [4] Flat Rack, [5] Reefer/Refregete, [6] Barge Container, [7] Bulk Container, [8] Isotank, [99] Lain-lain ',
    )
    kodeUkuranKontainer: Optional[KodeUkuranKontainer] = Field(
        None,
        description='Sesuai kolom formulir BC 2.3 - D.29 Ukuran Peti Kemas. Referensi Ukuran Kontainer: [20] 20 feet, [40] 40 feet, [45] 45 feet, [60] 60 feet',
    )
    nomorKontainer: Optional[str] = Field(
        None, description='Sesuai kolom formulir BC 2.3 - D.29 Nomor Peti Kemas'
    )
    seriKontainer: Optional[int] = Field(
        None, description='seri data kontainer berdasarkan data yang dimasukkan'
    )
    kodeJenisKontainer: Optional[KodeJenisKontainer] = Field(
        None, description='Referensi Jenis Kontainer: [4] Empty, [7] LCL, [8] FCL'
    )


class Dokuman(BaseModel):
    idDokumen: Optional[str] = Field(None, description='ID Dokumen')
    kodeDokumen: str = Field(
        '380', const=True, description='Set kode dokumen invoice (380)'
    )
    nomorDokumen: str = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.16 Nomor Invoice'
    )
    seriDokumen: int = Field(..., description='seri dokumen pelengkap pabean')
    tanggalDokumen: date = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.16 Tanggal Invoice dengan format YYYY-MM-DD',
    )


class KodeDokumen(Enum):
    field_705 = '705'
    field_740 = '740'


class Dokuman1(BaseModel):
    idDokumen: Optional[str] = Field(None, description='ID Dokumen')
    kodeDokumen: KodeDokumen = Field(
        ..., description='Referensi kode dokumen BL/AWB : [705] B/L, [740] AWB'
    )
    nomorDokumen: str = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.20 BL/AWB'
    )
    seriDokumen: int = Field(..., description='seri dokumen pelengkap pabean')
    tanggalDokumen: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.20 Tanggal BL/AWB dengan format YYYY-MM-DD',
    )


class Dokuman2(BaseModel):
    idDokumen: Optional[str] = Field(None, description='ID Dokumen')
    kodeDokumen: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.18 Surat Keputusan/Nomor Dokumen Lainnya. Lihat referensi dokumen',
    )
    nomorDokumen: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.18 Surat Keputusan/Nomor Dokumen Lainnya',
    )
    seriDokumen: int = Field(..., description='seri dokumen pelengkap pabean')
    tanggalDokumen: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.18 Tanggal Surat Keputusan / Dokumen Lainnya dengan format YYYY-MM-DD',
    )


class KodeCaraAngkut(Enum):
    field_1 = '1'
    field_2 = '2'
    field_3 = '3'
    field_4 = '4'
    field_5 = '5'
    field_6 = '6'
    field_7 = '7'
    field_8 = '8'
    field_9 = '9'


class PengangkutItem(BaseModel):
    kodeBendera: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.12 Bendera. Lihat Referensi Bendera',
    )
    namaPengangkut: str = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.12 Nama Sarana Pengangkut'
    )
    nomorPengangkut: str = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.12 No. Voy/Flight'
    )
    kodeCaraAngkut: KodeCaraAngkut = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.11 Cara Pengangkutan. Referensi Cara Angkut: [1] Laut, [2] Kereta Api, [3] Darat, [4] Udara, [5] Pos, [6] Multimoda, [7] Instalasi/Pipa, [8] Perairan, [9] Lainnya',
    )
    seriPengangkut: int = Field(..., description='seri data pengangkut')


class SchemaKirimDokumenBc23(BaseModel):
    asalData: str = Field(..., description='set value [S]')
    asuransi: confloat(multiple_of=0.01) = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.27 Asuransi LN/DN'
    )
    bruto: confloat(multiple_of=0.0001) = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.31 Berat Kotor (Kg)'
    )
    cif: confloat(multiple_of=0.01) = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.28 Nilai CIF'
    )
    fob: confloat(multiple_of=0.01) = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.25 FOB'
    )
    freight: confloat(multiple_of=0.01) = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.26 Freight'
    )
    hargaPenyerahan: confloat(multiple_of=0.0001) = Field(
        ..., description='Nilai Harga Penyerahan'
    )
    jabatanTtd: str = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - C. Jabatan Pengusaha TPB'
    )
    jumlahKontainer: int = Field(
        ..., description='jumlah peti kemas yang digunakan untuk mengangkut barang'
    )
    kodeAsuransi: KodeAsuransi = Field(
        ...,
        description='kode asuransi yang dibayar di [LN] luar negeri atau [DN] dalam negeri',
    )
    kodeDokumen: str = Field('23', const=True, description='set value [23]')
    kodeIncoterm: str = Field(..., description='Lihat Referensi Incoterm')
    kodeKantor: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - D. Kantor Pabean Pengawas. Lihat Referensi Kantor',
    )
    kodeKantorBongkar: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - D. Kantor Pabean Bongkar. Lihat Referensi Kantor',
    )
    kodePelBongkar: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.15 Pelabuhan Bongkar. Lihat Referensi Pelabuhan',
    )
    kodePelMuat: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.13 Pelabuhan Muat. Lihat Referensi Pelabuhan',
    )
    kodePelTransit: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.14 Pelabuhan Transit. Lihat Referensi Pelabuhan',
    )
    kodeTps: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.22 Tempat Penimbunan. Kode tps sesuai dengan yang dibuat oleh Kantor Pabean masing-masing',
    )
    kodeTujuanTpb: str = Field(..., description='Lihat Referensi Jenis TPB')
    kodeTutupPu: KodeTutupPu = Field(
        ..., description='Referensi TutupPu: [11] BC 1.1, [12] BC 1.2, [14] BC 1.4'
    )
    kodeValuta: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.23 Valuta. Lihat Referensi Valuta',
    )
    kotaTtd: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - C Kota tempat pengguna membuat dokumen BC 2.3',
    )
    namaTtd: str = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - C Nama pengguna yang membuat dokumen BC 2.3',
    )
    ndpbm: confloat(multiple_of=0.0001) = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.24 NDPBM'
    )
    netto: confloat(multiple_of=0.0001) = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.32 Berat Bersih (Kg)'
    )
    nik: str = Field(..., description='Sesuai kolom formulir BC 2.3 - B.5 API')
    nilaiBarang: confloat(multiple_of=0.01) = Field(
        ...,
        description='nilai barang impor dalam mata uang sesuai kode valuta yang dimasukkan',
    )
    nomorAju: constr(regex=r'^[A-Za-z0-9]{26}$') = Field(
        ...,
        description='nomor pengajuan dokumen pabean 26 digit dengan format 4 digit kode kantor, 2 digit kode dokumen pabean, 6 digit unik perusahaan, 8 digit tanggal pengajuan dengan format YYYYMMDD, 6 digit sequence/nomor urut pengajuan dokumen pabean',
    )
    nomorBc11: str = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.21 BC 1.1'
    )
    posBc11: str = Field(..., description='Sesuai kolom formulir BC 2.3 - B.21 BC 1.1')
    seri: int = Field(..., description='seri dokumen TPB')
    subposBc11: str = Field(
        ..., description='Sesuai kolom formulir BC 2.3 - B.21 BC 1.1'
    )
    tanggalBc11: date = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - B.21 Tanggal BC 1.1 dengan format YYYY-MM-DD',
    )
    tanggalTiba: date = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - Perkiraan Tanggal Tiba dengan format YYYY-MM-DD',
    )
    tanggalTtd: date = Field(
        ...,
        description='Sesuai kolom formulir BC 2.3 - Tanggal penandatanganan dokumen pabean dengan format YYYY-MM-DD',
    )
    biayaTambahan: confloat(multiple_of=0.0001) = Field(
        ..., description='biaya tambahan yang dikenakan'
    )
    biayaPengurang: confloat(multiple_of=0.0001) = Field(
        ..., description='biaya pengurang yang dikenakan'
    )
    kodeKenaPajak: Optional[KodeKenaPajak] = Field(
        None,
        description='Referensi Kode Kena Pajak: [1] PEMBELIAN BKP, [2] PENERIMA JASA BKP',
    )
    barang: List[BarangItem]
    entitas: List[Union[Entita, Entita1, Entita2]] = Field(
        ..., description='data entitas dalam pengajuan dokumen pabean'
    )
    kemasan: List[KemasanItem] = Field(
        ..., description='data kemasan dalam pengajuan dokumen pabean'
    )
    kontainer: Optional[List[KontainerItem]] = Field(
        None, description='data kontainer dalam pengajuan dokumen pabean'
    )
    dokumen: List[Union[Dokuman, Dokuman1, Dokuman2]] = Field(
        ..., description='data dokumen pelengkap dalam pengajuan dokumen pabean'
    )
    pengangkut: List[PengangkutItem] = Field(
        ..., description='data pengangkut dalam pengajuan dokumen pabean'
    )
