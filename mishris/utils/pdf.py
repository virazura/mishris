from __future__ import unicode_literals
import frappe

base_template_path = "templates/www/printview.html"
standard_format = "templates/print_formats/standard.html"

@frappe.whitelist()
def batch(html, doctype, format=None):
    import json
    output = PdfFileWriter()

    if not isinstance(doctype, dict):
        result = json.loads(doctype)
        
        for i, ss in enumerate(result):
            pass

def get_pdf(html, options=None, output = None):
	html = scrub_urls(html)
	html, options = prepare_options(html, options)
	fname = os.path.join("/tmp", "frappe-pdf-{0}.pdf".format(frappe.generate_hash()))

	options.update({
		"disable-javascript": "",
		"disable-local-file-access": "",
	})

	try:
		pdfkit.from_string(html, fname, options=options or {})
		if output:
			append_pdf(PdfFileReader(fname),output)
		else:
			with open(fname, "rb") as fileobj:
				filedata = fileobj.read()

	except IOError as e:
		if ("ContentNotFoundError" in e.message
			or "ContentOperationNotPermittedError" in e.message
			or "UnknownContentError" in e.message
			or "RemoteHostClosedError" in e.message):

			# allow pdfs with missing images if file got created
			if os.path.exists(fname):
				if output:
					append_pdf(PdfFileReader(file(fname,"rb")),output)
				else:
					with open(fname, "rb") as fileobj:
						filedata = fileobj.read()

			else:
				frappe.throw(_("PDF generation failed because of broken image links"))
		else:
			raise

	finally:
		cleanup(fname, options)

	if output:
		return output

	return filedata

