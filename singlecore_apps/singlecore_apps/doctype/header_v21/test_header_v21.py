# Copyright (c) 2024, AnharDeni and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from unittest.mock import patch


class TestHEADERV21(FrappeTestCase):
	def setUp(self):
		# Buat dokumen HEADER V21 dummy untuk pengetesan
		self.doc = frappe.get_doc({
			"doctype": "HEADER V21",
			"kode_dokumen": "23",  # BC 2.3 (Impor)
			"kode_kantor": "040300",
			"kode_valuta": "USD",
			"ndpbm": 15000.0,
			"company": "Test Company",
			"entitas": [
				{
					"doctype": "ENTITAS",
					"kode_entitas": "1",  # Importir
					"nama_entitas": "PT TEST IMPORTIR",
					"nomor_identitas": "012345678901234"
				}
			],
			"dokumen": [
				{
					"doctype": "DOKUMEN",
					"kode_dokumen": "705",  # Bill of Lading
					"nomor_dokumen": "BL123456",
					"tanggal_dokumen": "2026-06-10"
				}
			]
		})

	@patch('singlecore_apps.api.ceisa_api.kurs.get_kurs')
	@patch('singlecore_apps.api.ceisa_api.manifes.get_manifes')
	def test_successful_validation_and_sync(self, mock_get_manifes, mock_get_kurs):
		# Mock API Kurs
		mock_get_kurs.return_value = {
			"status": "success",
			"data": {
				"data": [{"nilaiKurs": "16500"}]
			}
		}
		
		# Mock API Manifest
		mock_get_manifes.return_value = {
			"status": "success",
			"data": {
				"data": [
					{
						"noBc11": "000123",
						"tglBc11": "2026-06-15",
						"noPos": "0001",
						"namaPenerima": "PT TEST IMPORTIR"
					}
				]
			}
		}
		
		# Jalankan validasi
		self.doc.before_submit()
		
		# Pastikan field diperbarui secara otomatis
		self.assertEqual(self.doc.ndpbm, 16500.0)
		self.assertEqual(self.doc.nomor_bc11, "000123")
		self.assertEqual(self.doc.tanggal_bc11, "2026-06-15")
		self.assertEqual(self.doc.nomor_pos, "0001")

	def test_missing_bl_throws_error(self):
		# Hapus BL dari child table dokumen
		self.doc.dokumen = []
		
		with self.assertRaises(frappe.ValidationError):
			self.doc.before_submit()

	@patch('singlecore_apps.api.ceisa_api.kurs.get_kurs')
	@patch('singlecore_apps.api.ceisa_api.manifes.get_manifes')
	def test_importer_name_mismatch_throws_error(self, mock_get_manifes, mock_get_kurs):
		# Mock API Kurs
		mock_get_kurs.return_value = {
			"status": "success",
			"data": {
				"data": [{"nilaiKurs": "16500"}]
			}
		}
		
		# Mock API Manifest dengan nama penerima yang berbeda signifikan
		mock_get_manifes.return_value = {
			"status": "success",
			"data": {
				"data": [
					{
						"noBc11": "000123",
						"tglBc11": "2026-06-15",
						"noPos": "0001",
						"namaPenerima": "PT LAIN YANG BERBEDA"
					}
				]
			}
		}
		
		with self.assertRaises(frappe.ValidationError):
			self.doc.before_submit()

	@patch('singlecore_apps.api.ceisa_api.kurs.get_kurs')
	@patch('singlecore_apps.api.ceisa_api.manifes.get_manifes')
	def test_fuzzy_importer_name_matching(self, mock_get_manifes, mock_get_kurs):
		# Mock API Kurs
		mock_get_kurs.return_value = {
			"status": "success",
			"data": {
				"data": [{"nilaiKurs": "16500"}]
			}
		}
		
		# Test cases of different fuzzy matches that SHOULD succeed
		fuzzy_cases = [
			("PT. TEST IMPORTIR, Tbk.", "PT TEST IMPORTIR"),
			("TEST IMPORTIR PT", "PT TEST IMPORTIR"),
			("  test   importir  ", "PT TEST IMPORTIR"),
			("PT TEST IMPORTIR (PERSERO)", "PT. TEST IMPORTIR TBK")
		]
		
		for ceisa_name, local_name in fuzzy_cases:
			# Update local document name
			self.doc.entitas[0].nama_entitas = local_name
			
			# Mock manifest response
			mock_get_manifes.return_value = {
				"status": "success",
				"data": {
					"data": [
						{
							"noBc11": "000123",
							"tglBc11": "2026-06-15",
							"noPos": "0001",
							"namaPenerima": ceisa_name
						}
					]
				}
			}
			
			# This should NOT raise any ValidationError
			try:
				self.doc.before_submit()
			except frappe.ValidationError as e:
				self.fail(f"Fuzzy matching failed for CEISA name: '{ceisa_name}' and Local name: '{local_name}'. Error: {str(e)}")
