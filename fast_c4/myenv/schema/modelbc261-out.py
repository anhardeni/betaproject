# generated by datamodel-codegen:
#   filename:  bc261-out.json
#   timestamp: 2024-01-30T06:59:38+00:00

from __future__ import annotations

from typing import List

from pydantic import BaseModel


class BahanBakuTarifItem(BaseModel):
    jumlahKemasan: int
    jumlahSatuan: int
    kodeAsalBahanBaku: str
    kodeFasilitasTarif: str
    kodeJenisPungutan: str
    kodeJenisTarif: str
    kodeSatuanBarang: str
    nilaiBayar: int
    nilaiFasilitas: float
    nilaiSudahDilunasi: int
    seriBahanBaku: int
    tarif: float
    tarifFasilitas: int


class BahanBakuItem(BaseModel):
    bahanBakuTarif: List[BahanBakuTarifItem]
    cif: float
    cifRupiah: float
    flagTis: None
    hargaPenyerahan: float
    hargaPerolehan: float
    isiPerKemasan: int
    jumlahSatuan: int
    kodeAsalBahanBaku: str
    kodeBarang: str
    kodeDokAsal: str
    kodeDokumen: str
    kodeKantor: str
    kodeSatuanBarang: str
    merkBarang: str
    ndpbm: int
    netto: int
    nilaiJasa: int
    nomorDaftarDokAsal: str
    nomorDokumen: str
    posTarif: str
    seriBahanBaku: int
    seriBarang: int
    seriBarangDokAsal: int
    seriIjin: int
    spesifikasiLainBarang: str
    tanggalDaftarDokAsal: str
    tipeBarang: str
    ukuranBarang: str
    uraianBarang: str


class BarangItem(BaseModel):
    bahanBaku: List[BahanBakuItem]
    cif: float
    cifRupiah: int
    hargaEkspor: int
    hargaPenyerahan: int
    hargaPerolehan: int
    isiPerKemasan: int
    jumlahKemasan: int
    jumlahSatuan: int
    kodeAsalBahanBaku: str
    kodeAsalBarang: str
    kodeBarang: str
    kodeDokumen: str
    kodeJenisKemasan: str
    kodeNegaraAsal: str
    kodeSatuanBarang: str
    merk: str
    ndpbm: int
    netto: int
    nilaiBarang: int
    nilaiJasa: int
    posTarif: str
    seriBarang: int
    spesifikasiLain: str
    tipe: str
    uangMuka: int
    ukuran: str
    uraian: str


class Dokuman(BaseModel):
    idDokumen: str
    kodeDokumen: str
    kodeFasilitas: str
    nomorDokumen: str
    seriDokumen: int
    tanggalDokumen: str


class Entita(BaseModel):
    alamatEntitas: str
    kodeEntitas: str
    kodeJenisApi: str
    kodeJenisIdentitas: str
    kodeStatus: str
    namaEntitas: str
    nibEntitas: str
    nomorIdentitas: str
    nomorIjinEntitas: str
    seriEntitas: int
    tanggalIjinEntitas: str


class JaminanItem(BaseModel):
    idJaminan: str
    kodeJenisJaminan: str
    nilaiJaminan: int
    nomorBpj: str
    nomorJaminan: str
    penjamin: str
    tanggalBpj: str
    tanggalJaminan: str
    tanggalJatuhTempo: str


class KemasanItem(BaseModel):
    jumlahKemasan: int
    kodeJenisKemasan: str
    merkKemasan: str
    seriKemasan: int


class PengangkutItem(BaseModel):
    idPengangkut: str
    kodeCaraAngkut: str
    seriPengangkut: int


class Model(BaseModel):
    asalData: str
    asuransi: int
    bahanBaku: List
    bahanBakuTarif: List
    barang: List[BarangItem]
    biayaPengurang: int
    biayaTambahan: int
    bruto: int
    cif: float
    disclaimer: str
    dokumen: List[Dokuman]
    entitas: List[Entita]
    freight: int
    hargaPenyerahan: int
    jabatanTtd: str
    jaminan: List[JaminanItem]
    jumlahKontainer: int
    kemasan: List[KemasanItem]
    kodeDokumen: str
    kodeKantor: str
    kodeTujuanPengiriman: str
    kodeValuta: str
    kontainer: List
    kotaTtd: str
    namaTtd: str
    ndpbm: int
    netto: int
    nik: str
    nilaiBarang: int
    nomorAju: str
    pengangkut: List[PengangkutItem]
    pungutan: List
    seri: int
    tanggalAju: str
    tanggalTtd: str
    tempatStuffing: None
    tglAkhirBerlaku: None
    tglAwalBerlaku: None
    totalDanaSawit: int
    uangMuka: int
    vd: int
