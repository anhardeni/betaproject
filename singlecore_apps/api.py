from os import stat
import frappe
from frappe.query_builder import DocType

SUCCESS = 200
NOT_FOUND = 400

@frappe.whitelist(allow_guest=True)
def get_all_header():
    header = frappe.db.sql("""SELECT `tabHEADER V2`.name AS nomorAju,  JSON_ARRAYAGG(tabENTITAS.seri) AS seriEntitas     FROM `tabHEADER V2`INNER JOIN tabENTITAS ON  `tabHEADER V2`.`name` = tabENTITAS.parent;""", as_dict=True)

    return header


@frappe.whitelist(allow_guest=True)
def get_all_headerg():
    headerg = frappe.db.sql("""SELECT kode_kantor_bongkar AS kodeKantorBongkar, kode_dokumen  FROM `tabHEADER` ;""", as_dict=True)

    return headerg

@frappe.whitelist(allow_guest=True)
def get_all_headera1():
    headera1 = frappe.db.sql("""SELECT kode_kantor_bongkar AS kodeKantorBongkar, JSON_ARRAYAGG(kode_dokumen) FROM `tabHEADER V2` ;""", as_dict=True)

    return headera1


@frappe.whitelist(allow_guest=True)
def get_all_headerq():
    #headerq = frappe.qb.Table("tabHEADER")
    headerq = frappe.qb.from_('HEADER').select('name' , 'owner', 'nomor_aju' , 'kode_dokumen' ).run(as_dict=True)
    #headerq = frappe.qb.from_('HEADER').select('name').as_('nomorAju').run(as_dict=True)
    return headerq
    #str(query)
    # SELECT "id","fname","lname","phone" FROM "tabCustomer"

    #query.get_sql()
    # SELECT "id","fname","lname","phone" FROM "tabCustomer"

    #str(query) == query.get_sql()



    #headerq = frappe.qb.DocType('HEADER')
        #filtered_data = (
            #frappe.qb.from_(headerq)
                #.select(headerq.kode_kantor_bongkar, headerq.nomoraju, headerq.name, headerq.referensi_kantor)
                #.where((customer.fname == 'Max') | customer.id.like('RA%'))
                #.where(customer.lname == 'Mustermann')
        #).run(as_dict=True)

    #return headerq

@frappe.whitelist(allow_guest=True)
def get_all_bc20():
    bc20 = frappe.db.sql("""SELECT 
    name AS nomorAju,
    kode_kantor_bongkar AS kodeKantorBongkar, 
    kode_dokumen  
    FROM `tabHEADER V2` ;""", as_dict=True)

    return bc20


@frappe.whitelist(allow_guest=True)
def get_all_bc30():
    bc30 = frappe.db.sql("""SELECT 
    asaldata	AS	asalData	,
    asuransi	AS	asuransi	,
    barang_tidak_berwujud	AS	barang_tidak_berwujud	,
    biaya_pengurang	AS	biaya_pengurang	,
    biaya_tambahan	AS	biaya_tambahan	,
    bruto	AS	bruto	,
    cif	AS	cif	,
    kode_kantor_bongkar AS kodeKantorBongkar, 
    kode_dokumen  
    FROM `tabHEADER V2`
    WHERE `tabHEADER V2`.kode_dokumen = "30" ;""", as_dict=True)

    return bc30

@frappe.whitelist(allow_guest=True)
def get_all_headerq30():
    #headerq30 = frappe.qb.Table("tabHEADER")
    #headerq30 = frappe.qb.from_('HEADER').select('name' , 'owner', 'nomor_aju' , 'kode_dokumen' ).where('kode_dokumen' == '261').walk(as_dict=True)
    headerq30 = frappe.qb.from_('HEADER V2').select('name' , 'owner', 'nomoraju' , 'kode_dokumen' ).run(as_dict=True)
    #headerq30 = frappe.qb.from_('HEADER V2').select('name').as_('nomorAju').run(as_dict=True)
    return headerq30

@frappe.whitelist(allow_guest=True)
def get_all_headerl1():
    frappe.get_list("HEADER V2")
    #headerq = frappe.qb.from_('HEADER').select('name' , 'owner', 'nomor_aju' , 'kode_dokumen' ).run(as_dict=True)
    #headerq30 = frappe.qb.from_('HEADER V2').select('name').as_('nomorAju').run(as_dict=True)
 