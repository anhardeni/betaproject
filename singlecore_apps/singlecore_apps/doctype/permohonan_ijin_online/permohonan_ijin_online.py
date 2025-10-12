# Copyright (c) 2023, AnharDeni and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PermohonanIjinOnline(Document):
	def get_jaminan_in_word(self):
		from frappe.utils import money_in_words
		self.jaminan_in_words = money_in_words(self.nilai_jaminan, self.currency)
		return f"{self.jaminan_in_words}"

	
