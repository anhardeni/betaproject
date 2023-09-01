# Copyright (c) 2023, AnharDeni and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PermohonanIjinOnline(Document):
	def validate(self):
		from frappe.utils import money_in_words

		if self.meta.get_field("jaminan_in_words"):
			nilai = abs(self.nilai_jaminan)
			self.jaminan_in_words = money_in_words(nilai, self.currency)

	
