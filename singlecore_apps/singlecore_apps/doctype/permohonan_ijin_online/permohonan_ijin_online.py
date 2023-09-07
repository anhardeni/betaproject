# Copyright (c) 2023, AnharDeni and contributors
# For license information, please see license.txt

import frappe
from num2words import num2words
from frappe.model.document import Document


class PermohonanIjinOnline(Document):
	#def before_save(self):
		#from frappe.utils import money_in_words
		#self.jaminan_in_words = f''delapan ratus ribu rupiah''

		#self.meta.get_field("jaminan_in_words"):
			#nilai = abs(self.nilai_jaminan)
			#self.jaminan_in_words = num2words(nilai, self.currency, lang='id')
			#self.jaminan_in_words = money_in_words(nilai, self.currency)

	def get_jaminan_in_word(self):
		from frappe.utils import money_in_words
		#self.jaminan_in_words = f''delapan ratus ribu rupiah''
			#nilai = abs(self.nilai_jaminan)
			#self.jaminan_in_words = num2words(nilai, self.currency, lang='id')
		self.jaminan_in_words = money_in_words({self.nilai_jaminan}, self.currency)
		return f"{self.jaminan_in_words}"

	
