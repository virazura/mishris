from __future__ import unicode_literals
import frappe
import filetype

"""
NEED IMPORT LOCAL LANG FROM FRAPPE
"""
def attach_print(doctype, name, file_name=None, print_format=None, style=None, html=None, doc=None, lang=None, encrypt=False, password=None, print_letterhead=True):
    from frappe.utils import scrub_urls
    from PyPDF2 import PdfFileWriter
    from PyPDF2 import PdfFileReader
    from frappe.utils.print_format import read_multi_pdf

    output = PdfFileWriter()

    if not file_name: file_name = name
    file_name = file_name.replace(' ','').replace('/','-')

    print_settings = frappe.db.get_singles_dict("Print Settings")
    hr_settings = frappe.db.get_singles_dict("HR Settings")
     
    # Not Check Lang on this print format
    #_lang = local.lang
    #set lang as specified in print format attachment
    #if lang: local.lang = lang
    #local.flags.ignore_print_permissions = True

    no_letterhead = not print_letterhead

    if int(print_settings.send_print_as_pdf or 0):
        output = frappe.get_print(doctype, name, print_format=print_format, style=style, html=html, as_pdf=True, doc=doc, no_letterhead=no_letterhead, output=output)

        if int(hr_settings.encrypt_salary_slip):
            output.encrypt(password)        
            salary_slip = read_multi_pdf(output)
            # butuh diubah ke bytes
             
        out = {
            "fname": file_name + ".pdf",
            "fcontent": salary_slip 
          }
    else:
        out = {
            "fname": file_name + ".html",
            "fcontent": scrub_urls(get_print(doctype, name, print_format=print_format, style=style, html=html, doc=doc, no_letterhead=no_letterhead)).encode("utf-8")
        }

    #local.flags.ignore_print_permissions = False
    #reset lang to original local lang
    #local.lang = _lang

    return out

