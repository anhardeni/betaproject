# generated by datamodel-codegen:
#   filename:  bc262-out.json
#   timestamp: 2024-01-30T06:59:51+00:00

from __future__ import annotations

from typing import List

from pydantic import BaseModel


class BahanBakuItem(BaseModel):
    bahanBakuTarif: List
    cif: int
    cifRupiah: int
    hargaPenyerahan: int
    hargaPerolehan: int
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
    nomorAjuDokAsal: str
    nomorDaftarDokAsal: str
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


class PungutanItem(BaseModel):
    idPungutan: str
    kodeFasilitasTarif: str
    kodeJenisPungutan: str
    nilaiPungutan: int


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
    kemasan: List[KemasanItem]
    kodeDokumen: str
    kodeKantor: str
    kodeTujuanPemasukan: str
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
    pungutan: List[PungutanItem]
    seri: int
    tanggalAju: str
    tanggalTtd: str
    uangMuka: int
    vd: int
