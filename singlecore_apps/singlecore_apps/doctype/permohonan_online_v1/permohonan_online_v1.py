# Copyright (c) 2023, AnharDeni and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from num2words import num2words



class PermohonanOnlineV1(Document):
	def validate(self):
		#self.get_jaminan_in_words() 
	  	frappe.msgprint("testtt event")

	def get_jaminan_in_words(self):
			#nilai = abs(self.nilai_jaminan)
			nilai = frappe.get_doc('PERMOHONAN ONLINE V1', 'nilai_jaminan')
			self.get_jaminan_in_words = num2words(nilai, lang='id')
			frappe.db.set_value("PERMOHONAN ONLINE V1",{"name":doc.name},{"jaminan_in_words":str(self.get_jaminan_in_words)})
			#doc.db_set('jaminan_in_words', self.jaminan_in_words , notify=True)
			#self.jaminan_in_words = money_in_words(nilai, self.currency)

	def validate(self):
		self.save_document()

	def save_document(self):
		doc.jaminan_in_words = 'tujuh ratus'
		doc.save()

	##from frappe.utils import money_in_words
		#self.jaminan_in_words = f''delapan ratus ribu rupiah''
			#nilai = abs(self.nilai_jaminan)
			#self.jaminan_in_words = num2words(nilai, self.currency, lang='id')
		#self.jaminan_in_words = money_in_words({self.nilai_jaminan}, self.currency)
		#return f"{self.jaminan_in_words}"
