# generated by datamodel-codegen:
#   filename:  bc40-out.json
#   timestamp: 2024-01-26T10:38:35+00:00

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class Entita(BaseModel):
    alamatEntitas: str
    kodeEntitas: str
    kodeJenisIdentitas: str
    namaEntitas: str
    nibEntitas: str
    nomorIdentitas: str
    nomorIjinEntitas: Optional[str] = None
    seriEntitas: int
    tanggalIjinEntitas: Optional[str] = None
    kodeJenisApi: Optional[str] = None
    kodeStatus: Optional[str] = None


class Dokuman(BaseModel):
    kodeDokumen: str
    nomorDokumen: str
    seriDokumen: int
    tanggalDokumen: str


class PengangkutItem(BaseModel):
    namaPengangkut: str
    nomorPengangkut: str
    seriPengangkut: int


class KemasanItem(BaseModel):
    jumlahKemasan: int
    kodeJenisKemasan: str
    merkKemasan: str
    seriKemasan: int


class PungutanItem(BaseModel):
    kodeFasilitasTarif: str
    kodeJenisPungutan: str
    nilaiPungutan: float


class BarangTarifItem(BaseModel):
    kodeJenisTarif: str
    jumlahSatuan: float
    kodeFasilitasTarif: str
    kodeSatuanBarang: str
    nilaiBayar: float
    nilaiFasilitas: float
    nilaiSudahDilunasi: float
    seriBarang: int
    tarif: float
    tarifFasilitas: float
    kodeJenisPungutan: str


class BarangItem(BaseModel):
    asuransi: float
    bruto: float
    cif: float
    diskon: float
    hargaEkspor: float
    hargaPenyerahan: float
    hargaSatuan: float
    isiPerKemasan: int
    jumlahKemasan: float
    jumlahRealisasi: float
    jumlahSatuan: float
    kodeBarang: str
    kodeDokumen: str
    kodeJenisKemasan: str
    kodeSatuanBarang: str
    merk: str
    netto: float
    nilaiBarang: float
    posTarif: str
    seriBarang: int
    spesifikasiLain: str
    tipe: str
    ukuran: str
    uraian: str
    volume: float
    cifRupiah: float
    hargaPerolehan: float
    kodeAsalBahanBaku: str
    ndpbm: float
    uangMuka: float
    nilaiJasa: int
    barangTarif: List[BarangTarifItem]


class Model(BaseModel):
    asalData: str
    asuransi: float
    bruto: float
    cif: float
    kodeJenisTpb: str
    freight: float
    hargaPenyerahan: float
    idPengguna: str
    jabatanTtd: str
    jumlahKontainer: int
    kodeDokumen: str
    kodeKantor: str
    kodeTujuanPengiriman: str
    kotaTtd: str
    namaTtd: str
    netto: float
    nik: str
    nomorAju: str
    seri: int
    tanggalAju: str
    tanggalTtd: str
    volume: float
    biayaTambahan: float
    biayaPengurang: float
    vd: float
    uangMuka: float
    nilaiJasa: float
    entitas: List[Entita]
    dokumen: List[Dokuman]
    pengangkut: List[PengangkutItem]
    kontainer: List
    kemasan: List[KemasanItem]
    pungutan: List[PungutanItem]
    barang: List[BarangItem]
