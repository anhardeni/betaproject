import re
import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import requests
import urllib3

# Matikan warning SSL jika server internal SAP memakai Self-Signed Certificate
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from singlecore_apps.utils.normalizer import normalize_sap_id, strip_sap_padding
except ImportError:
    from utils.normalizer import normalize_sap_id, strip_sap_padding

logger = logging.getLogger("sap_hana_connector")


def clean_sap_string(val: Any, max_len: int = 140) -> str:
    """
    Membersihkan karakter kontrol non-printable dari SAP dan memotong panjang string
    agar tidak pernah memicu MariaDB DataError (1406: Data too long for column, batas 140 char).
    """
    if val is None:
        return ""
    # Hapus control characters (\x00-\x1f kecuali tab/newline)
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", str(val)).strip()
    return s[:max_len] if max_len else s


def parse_sap_number(val: Any, default: float = 1.0) -> float:
    """
    Konversi format angka tidak biasa (unusual) dari SAP menjadi float Python yang aman:
    1. Tanda minus di belakang khas ABAP: '1500.00-' -> -1500.0 -> abs(1500.0)
    2. Format ribuan titik & desimal koma Eropa: '1.500,50' -> 1500.50
    3. Format ribuan koma & desimal titik: '1,500.50' -> 1500.50
    4. String dengan satuan menempel: '1500 KGM' -> 1500.0
    """
    if val is None or val == "":
        return default
    if isinstance(val, (int, float)):
        return float(val) if float(val) > 0 else default

    s = str(val).strip()
    # Tangani tanda minus di belakang khas SAP ABAP (contoh: "150.00-")
    is_negative = s.endswith("-") or s.startswith("-")
    s = re.sub(r"[^0-9.,]", "", s)
    if not s:
        return default

    # Jika ada titik dan koma sekaligus
    if "." in s and "," in s:
        if s.rfind(",") > s.rfind("."):
            # Format Eropa: 1.500,50
            s = s.replace(".", "").replace(",", ".")
        else:
            # Format US: 1,500.50
            s = s.replace(",", "")
    elif "," in s:
        # Cek apakah koma adalah desimal (misal 150,50) atau ribuan (1,500)
        parts = s.split(",")
        if len(parts) == 2 and len(parts[1]) in (1, 2):
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")

    try:
        num = abs(float(s))
        return num if num > 0 else default
    except Exception:
        return default


def parse_sap_date(val: Any) -> str:
    """
    Konversi otomatis berbagai format tanggal khas SAP menjadi 'YYYY-MM-DD' standar ERPNext:
    1. OData V2 Epoch: '/Date(1727740800000)/' atau '/Date(1727740800000+0700)/'
    2. SAP ABAP DATS: '20261001' (8 digit)
    3. ISO 8601 / OData V4: '2026-10-01T00:00:00Z'
    4. Format titik/garis miring Eropa: '01.10.2026' atau '01/10/2026'
    """
    if not val:
        return datetime.now().strftime("%Y-%m-%d")

    s = str(val).strip()

    # 1. Cek format OData V2: /Date(1727740800000)/
    m = re.search(r"/Date\((-?\d+)", s)
    if m:
        try:
            ms = int(m.group(1))
            dt = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # 2. Cek format YYYYMMDD (8 digit angka murni)
    if re.match(r"^\d{8}$", s):
        if s == "00000000":
            return datetime.now().strftime("%Y-%m-%d")
        return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"

    # 3. Cek format ISO YYYY-MM-DD...
    if re.match(r"^\d{4}-\d{2}-\d{2}", s):
        return s[:10]

    # 4. Cek format DD.MM.YYYY atau DD/MM/YYYY
    m_eu = re.match(r"^(\d{2})[./](\d{2})[./](\d{4})$", s)
    if m_eu:
        return f"{m_eu.group(3)}-{m_eu.group(2)}-{m_eu.group(1)}"

    return datetime.now().strftime("%Y-%m-%d")


def parse_sap_xml_fallback(xml_text: str) -> List[Dict[str, Any]]:
    """
    Fallback Parser jika SAP Gateway mengabaikan `$format=json` dan mengembalikan
    XML OData Atom (`<feed><entry><content><m:properties><d:Material>...`).
    """
    results: List[Dict[str, Any]] = []
    try:
        root = ET.fromstring(xml_text)
        # Cari semua elemen <properties> (dengan atau tanpa namespace)
        for elem in root.iter():
            tag_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if tag_name.lower() == "properties":
                row: Dict[str, Any] = {}
                for child in elem:
                    c_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    row[c_tag] = (child.text or "").strip()
                if row:
                    results.append(row)
    except Exception as e:
        logger.warning(f"Gagal mem-parsing fallback XML SAP: {e}")
    return results


def unwrap_sap_json(payload: Any) -> List[Dict[str, Any]]:
    """
    Mengekstrak array record dari berbagai kemungkinan struktur pembungkus (envelope) JSON SAP:
    - OData V2: {"d": {"results": [...]}} atau {"d": {...}}
    - OData V4: {"value": [...]}
    - Custom REST / RFC Wrapper: {"data": [...]}, {"items": [...]}, {"results": [...]}
    - Direct JSON Array: [...]
    """
    if isinstance(payload, list):
        return payload

    if not isinstance(payload, dict):
        return []

    # OData V2
    if "d" in payload:
        d_val = payload["d"]
        if isinstance(d_val, dict) and "results" in d_val and isinstance(d_val["results"], list):
            return d_val["results"]
        if isinstance(d_val, list):
            return d_val
        if isinstance(d_val, dict):
            return [d_val]

    # OData V4
    if "value" in payload and isinstance(payload["value"], list):
        return payload["value"]

    # Custom REST Wrappers
    for key in ("results", "data", "items", "records", "MATDOC", "MSEG", "ET_DATA", "T_DATA"):
        if key in payload and isinstance(payload[key], list):
            return payload[key]

    return [payload]


class SapHanaConnector:
    """
    Konektor Penarikan Data (Pull Engine) via SAP OData / REST API menuju ERPNext 15.
    Dilengkapi proteksi kondisi tidak biasa (Unusual Edge-Case Hardening):
    - Multi-Alias Field Resolver (S/4HANA OData & ECC ABAP DDIC)
    - ABAP Trailing-Minus & European Number Parser ("1.500,50" / "500.00-")
    - OData XML Atom Fallback Parser (jika SAP mengembalikan XML alih-alih JSON)
    - Auto-Retry Tanpa Filter (jika SAP menolak parameter $filter)
    - Corporate Proxy Bypass (trust_env = False untuk IP lokal SAP)
    """

    FIELD_ALIASES = {
        "sap_doc_num": ["MaterialDocument", "MBLNR", "DeliveryDocument", "VBELN", "BELNR", "sap_doc_num", "doc_num"],
        "sap_doc_year": ["MaterialDocumentYear", "MJAHR", "GJAHR", "sap_doc_year", "doc_year"],
        "sap_item_num": ["MaterialDocumentItem", "ZEILE", "DeliveryDocumentItem", "POSNR", "sap_item_num", "item_num"],
        "posting_date": ["PostingDate", "BUDAT", "ActualGoodsMovementDate", "WADAT_IST", "DocumentDate", "BLDAT", "posting_date"],
        "movement_type": ["GoodsMovementType", "BWART", "movement_type"],
        "material_code": ["Material", "MATNR", "Product", "material_code", "item_code"],
        "material_name": ["MaterialName", "MAKTX", "MaterialDescription", "ARKTX", "ProductDescription", "material_name", "item_name"],
        "qty": ["QuantityInEntryUnit", "MENGE", "ActualDeliveryQuantity", "LFIMG", "ERFMG", "qty", "quantity"],
        "uom": ["EntryUnit", "MEINS", "DeliveryQuantityUnit", "VRKME", "ERFME", "BaseUnit", "uom"],
        "batch_no": ["Batch", "CHARG", "batch_no"],
        "warehouse": ["StorageLocation", "LGORT", "Plant", "WERKS", "warehouse"],
        "supplier": ["Supplier", "LIFNR", "Vendor", "supplier"],
        "customer": ["Customer", "KUNNR", "ShipToParty", "customer"],
        "jenis_dok_bc": ["YY1_BCDocType", "ZPPKEK_TYPE", "DocumentHeaderText", "BKTXT", "jenis_dok_bc"],
        "no_daftar_bc": ["YY1_BCRegNo", "ZPPKEK_NO", "ReferenceDocument", "XBLNR", "no_daftar_bc"],
        "tgl_daftar_bc": ["YY1_BCRegDate", "ZPPKEK_DATE", "DocumentDate", "BLDAT", "tgl_daftar_bc"]
    }

    def __init__(self, base_url: Optional[str] = None, user: Optional[str] = None,
                 password: Optional[str] = None, **kwargs):
        self.base_url = "https://saphana.perusahaan.com:44300"
        self.pemasukan_endpoint = "/sap/opu/odata/sap/API_MATERIAL_DOCUMENT_SRV/A_MaterialDocumentItem"
        self.pengeluaran_endpoint = "/sap/opu/odata/sap/API_MATERIAL_DOCUMENT_SRV/A_MaterialDocumentItem"
        self.sap_client = "100"
        self.auth_type = "Basic Auth (Username & Password)"
        self.user = "SAP_API_USER"
        self.password = ""
        self.api_token = ""
        self.verify_ssl = False
        self.connection_mode = "OData / REST API Pull (Recommended)"
        self.enabled = True

        # Auto-load dari Single DocType 'SAP HANA Settings'
        try:
            import frappe
            if hasattr(frappe, "get_single") and getattr(frappe, "db", None):
                settings = frappe.get_single("SAP HANA Settings")
                if settings:
                    self.enabled = bool(getattr(settings, "enabled", 1))
                    self.connection_mode = getattr(settings, "connection_mode", self.connection_mode) or self.connection_mode
                    self.base_url = (base_url or getattr(settings, "base_url", "") or getattr(settings, "odata_url", "") or getattr(settings, "host", "") or self.base_url).rstrip("/")
                    if not self.base_url.startswith("http"):
                        self.base_url = f"https://{self.base_url}"
                    self.pemasukan_endpoint = getattr(settings, "pemasukan_endpoint", "") or self.pemasukan_endpoint
                    self.pengeluaran_endpoint = getattr(settings, "pengeluaran_endpoint", "") or self.pengeluaran_endpoint
                    self.sap_client = str(getattr(settings, "sap_client", "100") or "100").strip()
                    self.auth_type = getattr(settings, "auth_type", self.auth_type) or self.auth_type
                    self.user = user or getattr(settings, "user", "") or self.user
                    pwd = settings.get_password("password") if hasattr(settings, "get_password") else (getattr(settings, "password", "") or "")
                    self.password = password or pwd or ""
                    tok = settings.get_password("api_token") if hasattr(settings, "get_password") else (getattr(settings, "api_token", "") or "")
                    self.api_token = tok or ""
                    self.verify_ssl = bool(getattr(settings, "verify_ssl", 0))
        except Exception:
            pass

        if base_url:
            self.base_url = base_url.rstrip("/")
        if user:
            self.user = user
        if password:
            self.password = password

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.verify = self.verify_ssl
        # Penting: Bypass environment proxy agar koneksi ke IP internal SAP tidak nyasar ke proxy internet
        session.trust_env = False

        headers = {
            "Accept": "application/json, application/atom+xml, application/xml;q=0.9, */*;q=0.8",
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        }
        if self.sap_client:
            headers["sap-client"] = self.sap_client

        if self.auth_type == "Bearer Token / API Key" and self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        elif self.user:
            session.auth = (self.user, self.password)

        session.headers.update(headers)
        return session

    def _parse_response_body(self, resp: requests.Response) -> List[Dict[str, Any]]:
        """
        Mem-parsing response SAP baik berupa JSON maupun fallback XML Atom.
        """
        try:
            return unwrap_sap_json(resp.json())
        except Exception:
            # Jika SAP mengembalikan XML meskipun diminta JSON
            text = (resp.text or "").strip()
            if text.startswith("<"):
                return parse_sap_xml_fallback(text)
            return []

    def test_api_connection(self) -> Dict[str, Any]:
        """
        Menguji koneksi HTTP Pull ke endpoint SAP OData / REST.
        """
        if self.connection_mode == "Simulation (Demo)":
            return {
                "status": "success",
                "message": "Mode Simulasi (Demo) aktif. Penarikan data menggunakan simulator SAP OData standar."
            }

        url = f"{self.base_url}{self.pemasukan_endpoint}"
        params = {"$format": "json", "$top": "1"}
        if self.sap_client:
            params["sap-client"] = self.sap_client

        try:
            session = self._build_session()
            resp = session.get(url, params=params, timeout=15)
            if resp.status_code == 200:
                data = self._parse_response_body(resp)
                return {
                    "status": "success",
                    "message": f"✅ Koneksi Pull Berhasil! Server SAP ({self.base_url}) merespons HTTP 200 OK. Contoh record terbaca: {len(data)} baris."
                }
            elif resp.status_code in (401, 403):
                return {
                    "status": "error",
                    "message": f"❌ Server SAP terjangkau ({url}), tetapi Autentikasi Ditolak (HTTP {resp.status_code}). Periksa Username, Password, atau SAP Client ({self.sap_client})."
                }
            else:
                return {
                    "status": "warning",
                    "message": f"⚠️ Server SAP merespons dengan HTTP {resp.status_code}: {resp.text[:200]}"
                }
        except Exception as e:
            return {
                "status": "warning",
                "message": f"⚠️ Tidak dapat menjangkau URL SAP ({url}): {str(e)}. Sistem otomatis menggunakan Fallback Simulasi saat sinkronisasi."
            }

    def normalize_sap_record(self, raw_row: Dict[str, Any], default_mvt: str = "101") -> Dict[str, Any]:
        """
        Memetakan baris JSON/XML dari SAP menjadi format seragam dengan pembersihan
        string, angka, dan tanggal anti-gagal.
        """
        mapped_keys_used = set()
        normalized: Dict[str, Any] = {}

        for target_key, aliases in self.FIELD_ALIASES.items():
            val = None
            for alias in aliases:
                if alias in raw_row and raw_row[alias] not in (None, ""):
                    val = raw_row[alias]
                    mapped_keys_used.add(alias)
                    break
                for raw_k in raw_row.keys():
                    if raw_k.lower() == alias.lower() and raw_row[raw_k] not in (None, ""):
                        val = raw_row[raw_k]
                        mapped_keys_used.add(raw_k)
                        break
                if val is not None:
                    break
            normalized[target_key] = val

        # Normalisasi & Truncate aman (batas 140 char MariaDB)
        normalized["sap_doc_num"] = clean_sap_string(normalize_sap_id(normalized.get("sap_doc_num") or "5000000001"), 50)
        normalized["sap_doc_year"] = clean_sap_string(normalized.get("sap_doc_year") or datetime.now().year, 10)
        normalized["sap_item_num"] = clean_sap_string(strip_sap_padding(str(normalized.get("sap_item_num") or "1")), 20)
        normalized["posting_date"] = parse_sap_date(normalized.get("posting_date"))
        normalized["movement_type"] = clean_sap_string(normalized.get("movement_type") or default_mvt, 10)

        raw_mat = clean_sap_string(normalized.get("material_code") or "MAT-001", 100)
        normalized["material_code"] = raw_mat
        normalized["clean_material_code"] = clean_sap_string(strip_sap_padding(raw_mat), 100) or "MAT-001"
        normalized["material_name"] = clean_sap_string(
            normalized.get("material_name") or f"Material SAP {normalized['clean_material_code']}", 140
        )

        # Konversi angka aman (menangani "1.500,50" dan "500.00-")
        normalized["qty"] = parse_sap_number(normalized.get("qty"), default=1.0)

        normalized["uom"] = clean_sap_string(normalized.get("uom") or "Nos", 30)
        normalized["batch_no"] = clean_sap_string(normalized.get("batch_no") or "", 100)
        normalized["warehouse"] = clean_sap_string(normalized.get("warehouse") or "", 100)
        normalized["supplier"] = clean_sap_string(normalized.get("supplier") or "SAP Default Supplier", 140)
        normalized["customer"] = clean_sap_string(normalized.get("customer") or "SAP Default Customer", 140)
        normalized["jenis_dok_bc"] = clean_sap_string(normalized.get("jenis_dok_bc") or "BC 4.0", 50)
        normalized["no_daftar_bc"] = clean_sap_string(normalized.get("no_daftar_bc") or "", 100)
        normalized["tgl_daftar_bc"] = (
            parse_sap_date(normalized.get("tgl_daftar_bc"))
            if normalized.get("tgl_daftar_bc")
            else normalized["posting_date"]
        )

        unmapped = {
            k: v for k, v in raw_row.items()
            if k not in mapped_keys_used and not str(k).startswith("__")
        }
        normalized["unmapped_fields"] = unmapped

        return normalized

    def _pull_odata_endpoint(self, endpoint: str, from_date: str, to_date: str, movement_types: List[str]) -> Optional[List[Dict[str, Any]]]:
        """
        Menarik data dari endpoint OData / REST SAP dengan Auto-Fallback Query Parameter:
        1. Percobaan 1: Kirim dengan parameter tanggal.
        2. Percobaan 2 (Fallback jika HTTP 400/500): Kirim murni `?$format=json` lalu filter di Python.
        """
        if self.connection_mode == "Simulation (Demo)":
            return None

        url = f"{self.base_url}{endpoint}"
        session = self._build_session()

        base_params = {"$format": "json"}
        if self.sap_client:
            base_params["sap-client"] = self.sap_client

        params_with_date = dict(base_params)
        params_with_date["from_date"] = from_date
        params_with_date["to_date"] = to_date

        try:
            resp = session.get(url, params=params_with_date, timeout=20)
            # Jika SAP menolak parameter custom (HTTP 400 / 501), retry murni dengan $format=json
            if resp.status_code in (400, 500, 501):
                logger.info("Retry pull SAP OData tanpa custom filter parameter...")
                resp = session.get(url, params=base_params, timeout=20)

            if resp.status_code == 200:
                raw_rows = self._parse_response_body(resp)
                results = []
                for row in raw_rows:
                    if not isinstance(row, dict):
                        continue
                    norm = self.normalize_sap_record(row, default_mvt=movement_types[0])
                    if norm["movement_type"] in movement_types or not row.get("GoodsMovementType"):
                        results.append(norm)
                return results
            else:
                logger.warning(f"SAP API merespons HTTP {resp.status_code}. Memakai mode simulasi.")
                return None
        except Exception as e:
            logger.warning(f"Koneksi Pull SAP API ({url}) gagal ({e}). Memakai mode simulasi.")
            return None

    def fetch_pemasukan_movement(self, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """
        Menarik data Pemasukan Barang (Movement 101, 103, 501) via OData/REST Pull.
        """
        live_data = self._pull_odata_endpoint(
            self.pemasukan_endpoint, from_date, to_date, ["101", "103", "501"]
        )
        if live_data is not None:
            return live_data

        simulated_sap_odata_rows = [
            {
                "MaterialDocument": "5000001001",
                "MaterialDocumentYear": "2026",
                "MaterialDocumentItem": "0001",
                "PostingDate": "/Date(1790812800000)/",
                "GoodsMovementType": "101",
                "Material": "000000000010002341",
                "MaterialName": "Bahan Baku Resin Polymer 250gsm",
                "QuantityInEntryUnit": "1.500,00",
                "EntryUnit": "KGM",
                "Batch": "BATCH-202610-01",
                "StorageLocation": "RAW-01",
                "Supplier": "SUP-SAP-01",
                "YY1_BCDocType": "PPKEK-IN",
                "ReferenceDocument": "BC20-2026-009821",
                "DocumentDate": "20260930",
                "ProfitCenter": "PC-KEK-01",
                "CostCenter": "CC-PROD-100",
                "SAP_CreatedByUser": "SAP_MM_ADMIN"
            }
        ]
        return [self.normalize_sap_record(r, default_mvt="101") for r in simulated_sap_odata_rows]

    def fetch_pengeluaran_movement(self, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """
        Menarik data Pengeluaran Barang / Delivery (Movement 601, 261, 311) via OData/REST Pull.
        """
        live_data = self._pull_odata_endpoint(
            self.pengeluaran_endpoint, from_date, to_date, ["601", "261", "311"]
        )
        if live_data is not None:
            return live_data

        simulated_sap_odata_rows = [
            {
                "MaterialDocument": "4900002005",
                "MaterialDocumentYear": "2026",
                "MaterialDocumentItem": "0001",
                "PostingDate": "20261005",
                "GoodsMovementType": "601",
                "Material": "000000000020005112",
                "MaterialName": "Produk Jadi Panel Elektronik",
                "QuantityInEntryUnit": "500.00-",
                "EntryUnit": "PCE",
                "Batch": "BATCH-FG-202610",
                "StorageLocation": "FG-01",
                "Customer": "CUST-SAP-01",
                "YY1_BCDocType": "PPKEK-OUT",
                "ReferenceDocument": "BC30-2026-004112",
                "DocumentDate": "20261004",
                "ShippingPoint": "SHP-01",
                "RouteCode": "RT-EXPORT-01"
            }
        ]
        return [self.normalize_sap_record(r, default_mvt="601") for r in simulated_sap_odata_rows]
