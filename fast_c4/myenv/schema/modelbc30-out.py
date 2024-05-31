# generated by datamodel-codegen:
#   filename:  peb.json
#   timestamp: 2024-01-25T07:56:04+00:00

from __future__ import annotations

from typing import List

from pydantic import BaseModel


class BankDevisaItem(BaseModel):
    kodeBank: str
    namaBank: str
    seriBank: int


class BarangPemilikItem(BaseModel):
    seriEntitas: int


class BarangItem(BaseModel):
    barangDokumen: List
    barangPemilik: List[BarangPemilikItem]
    barangTarif: List
    cif: int
    cifRupiah: int
    fob: float
    hargaEkspor: int
    hargaPatokan: int
    hargaPerolehan: int
    hargaSatuan: float
    jumlahKemasan: int
    jumlahSatuan: int
    kodeAsalBahanBaku: str
    kodeBarang: str
    kodeDaerahAsal: str
    kodeDokumen: str
    kodeJenisKemasan: str
    kodeNegaraAsal: str
    kodeSatuanBarang: str
    merk: str
    ndpbm: int
    netto: int
    nilaiBarang: int
    nilaiDanaSawit: int
    posTarif: str
    seriBarang: int
    spesifikasiLain: str
    tipe: str
    ukuran: str
    uraian: str
    volume: int


class Dokuman(BaseModel):
    kodeDokumen: str
    nomorDokumen: str
    seriDokumen: int
    tanggalDokumen: str


class Entita(BaseModel):
    alamatEntitas: str
    kodeEntitas: str
    kodeJenisApi: str
    kodeJenisIdentitas: str
    kodeNegara: str
    kodeStatus: str
    namaEntitas: str
    nibEntitas: str
    nomorIdentitas: str
    seriEntitas: int


class KemasanItem(BaseModel):
    jumlahKemasan: int
    kodeJenisKemasan: str
    merkKemasan: str
    seriKemasan: int


class KontainerItem(BaseModel):
    kodeJenisKontainer: str
    kodeTipeKontainer: str
    kodeUkuranKontainer: str
    nomorKontainer: str
    seriKontainer: int


class PengangkutItem(BaseModel):
    kodeBendera: str
    kodeCaraAngkut: str
    namaPengangkut: str
    nomorPengangkut: str
    seriPengangkut: int


class Model(BaseModel):
    asalData: str
    asuransi: float
    bankDevisa: List[BankDevisaItem]
    barang: List[BarangItem]
    bruto: int
    cif: float
    disclaimer: str
    dokumen: List[Dokuman]
    entitas: List[Entita]
    flagCurah: str
    flagMigas: str
    fob: float
    freight: float
    idPengguna: str
    jabatanTtd: str
    jumlahKontainer: int
    kemasan: List[KemasanItem]
    kesiapanBarang: List
    kodeAsuransi: str
    kodeCaraBayar: str
    kodeCaraDagang: str
    kodeDokumen: str
    kodeIncoterm: str
    kodeJenisEkspor: str
    kodeJenisNilai: str
    kodeJenisProsedur: str
    kodeKantor: str
    kodeKantorEkspor: str
    kodeKantorMuat: str
    kodeKantorPeriksa: str
    kodeKategoriEkspor: str
    kodeLokasi: str
    kodeNegaraTujuan: str
    kodePelBongkar: str
    kodePelEkspor: str
    kodePelMuat: str
    kodePelTujuan: str
    kodePembayar: str
    kodeTps: str
    kodeValuta: str
    kontainer: List[KontainerItem]
    kotaTtd: str
    namaTtd: str
    ndpbm: int
    netto: int
    nilaiMaklon: int
    nomorAju: str
    nomorBc11: str
    pengangkut: List[PengangkutItem]
    posBc11: str
    seri: int
    subPosBc11: str
    tanggalAju: str
    tanggalBc11: str
    tanggalEkspor: str
    tanggalPeriksa: str
    tanggalTtd: str
    totalDanaSawit: int