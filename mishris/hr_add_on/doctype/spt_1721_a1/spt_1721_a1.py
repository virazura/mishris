# -*- coding: utf-8 -*-
# Copyright (c) 2019, MIS and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import getdate

from openpyxl import load_workbook
from openpyxl.styles import Font


class SPT1721_A1(Document):
    def validate(self):
        self.fill_missing()

    def fill_missing(self):
        self.jumlah_bruto = (
            self.gaji_pensiunan
            + self.tunjangan_pph
            + self.tunjangan_lainnya
            + self.honorarium
            + self.premi_asuransi
            + self.penerimaan_natura
            + self.bonus
        )
        self.jumlah_pengurangan = self.biaya_jabatan + self.iuran_pensiun
        self.jumlah_netto = self.jumlah_bruto - self.jumlah_pengurangan
        self.penghasilan_neto_setahun = (
            self.jumlah_netto + self.penghasilan_neto_sebelumnya
        )
        self.penghasilan_kena_pajak = (
            self.penghasilan_neto_setahun - self.penghasilan_tidak_kena_pajak
        )
        self.pph_21_penghasilan_kena_pajak_setahun = int(
            self.penghasilan_kena_pajak * 0.05
        )
        self.pph_21_terutang = int(
            self.pph_21_penghasilan_kena_pajak_setahun
            - self.pph_21_telah_dipotong_sebelumnya
        )
        self.pph_21_26_telah_dipotong = self.pph_21_terutang

    def before_submit(self):
        self.spt_document()

    def spt_document(self):
        spt_template = self.get_spt_doc_template()
        filename = self.create_spt_doc(spt_template)
        self.attach_spt_doc(filename)
        filename = self.create_spt_pdf(filename)
        self.attach_spt_doc(filename)

    def attach_spt_doc(self, filename):
        self.spt_doc = "/{dir}/{filename}".format(dir="files", filename=filename)

        attach_doc = frappe.get_doc(
            {
                "doctype": "File",
                "file_name": filename,
                "file_url": self.spt_doc,
                "attached_to_name": self.name,
                "attached_to_doctype": self.doctype,
                "is_private": 0,
            }
        )
        attach_doc.insert()

    def create_spt_doc(self, workbook):
        worksheet = workbook.get_sheet_by_name("1721 - A1")

        self.insert_data_spt_doc(worksheet)

        # self.apply_styles(worksheet)

        filename = "{}-{}.xlsx".format(self.name.replace("/", "_"), self.modified)
        dest_filename = "{site_path}/{dir}/{filename}".format(
            site_path=frappe.get_site_path(), dir="public/files", filename=filename
        )
        workbook.save(dest_filename)
        return filename

    def create_spt_pdf(self, filename):
        import subprocess

        dest_dir = "{site_path}/{dir}".format(
            site_path=frappe.get_site_path(), dir="public/files"
        )
        dest_filename = "{site_path}/{dir}/{filename}".format(
            site_path=frappe.get_site_path(), dir="public/files", filename=filename
        )
        cmd = [
            "libreoffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            dest_dir,
            dest_filename,
        ]
        process = subprocess.Popen(cmd)
        process.wait()
        return filename.replace(".xlsx", ".pdf")

    def insert_data_spt_doc(self, worksheet):
        self.insert_document_number(worksheet)
        self.insert_perusahaan_pemotong(worksheet)
        self.insert_identitas_penerima_penghasilan(worksheet)
        self.insert_rincian_penghasilan(worksheet)
        self.insert_identitas_pemotong(worksheet)

    def insert_document_number(self, worksheet):
        # nomor spt
        spt_nomor = self.nomor.split("-")
        spt_nomor_1 = spt_nomor[0].split(".")
        worksheet["AU11"] = spt_nomor_1[0]
        worksheet["AZ11"] = spt_nomor_1[1]
        worksheet["BE11"] = spt_nomor[1]
        worksheet["BM11"] = spt_nomor[2]
        worksheet["BX11"] = "{}".format(spt_nomor[3])

        # masa perolehan penghasilan
        worksheet["DA12"] = "{}".format(self.dari)
        worksheet["DI12"] = "{}".format(self.sampai)

    def insert_perusahaan_pemotong(self, worksheet):
        npwp_pemotong = self.npwp_perusahaan_pemotong.split("-")
        worksheet["V16"] = npwp_pemotong[0]
        worksheet["BA16"] = "{}".format(npwp_pemotong[1])
        worksheet["BL16"] = "{}".format(npwp_pemotong[2])
        worksheet["V18"] = self.nama_perusahaan_pemotong

    def insert_identitas_penerima_penghasilan(self, worksheet):
        npwp_penerima = self.npwp.split("-")
        worksheet["R24"] = npwp_penerima[0]
        worksheet["AV24"] = "{}".format(npwp_penerima[1])
        worksheet["BF24"] = "{}".format(npwp_penerima[2])
        worksheet["R26"] = "{}".format(self.nik_no_paspor)
        worksheet["R29"] = self.nama
        worksheet["R32"] = self.alamat
        if self.jenis_kelamin == "Laki-Laki":
            worksheet["X36"] = "X"
            worksheet["AR36"] = ""
        else:
            worksheet["AR36"] = "X"
            worksheet["X36"] = ""
        worksheet["BS26"] = self.tanggungan_k or ""
        worksheet["CJ26"] = self.tanggungan_tk or ""
        worksheet["CZ26"] = self.tanggungan_hb or ""
        worksheet["CK29"] = self.nama_jabatan
        worksheet["CO32"] = "X" if self.karyawan_asing == "Ya" else ""
        worksheet["CR34"] = self.kode_negara_domisili

    def insert_rincian_penghasilan(self, worksheet):
        if self.kode_objek_pajak == "21-100-01":
            worksheet["W43"] = "X"
            worksheet["AM43"] = ""
        elif self.kode_objek_pajak == "21-100-02":
            worksheet["AM43"] = "X"
            worksheet["W43"] = ""

        # Penghasilan Bruto
        worksheet["CP46"] = "{}".format(self.gaji_pensiunan) or "0"
        worksheet["CP47"] = "{}".format(self.tunjangan_pph) or "0"
        worksheet["CP48"] = "{}".format(self.tunjangan_lainnya) or "0"
        worksheet["CP49"] = "{}".format(self.honorarium) or "0"
        worksheet["CP50"] = "{}".format(self.premi_asuransi) or "0"
        worksheet["CP51"] = "{}".format(self.penerimaan_natura) or "0"
        worksheet["CP52"] = "{}".format(self.bonus) or "0"
        worksheet["CP53"] = "{}".format(self.jumlah_bruto) or "0"

        # Pengurangan
        worksheet["CP55"] = "{}".format(self.biaya_jabatan) or "0"
        worksheet["CP56"] = "{}".format(self.iuran_pensiun) or "0"
        worksheet["CP57"] = "{}".format(self.jumlah_pengurangan) or "0"

        # Penghitungan PPh 21
        worksheet["CP59"] = "{}".format(self.jumlah_netto) or "0"
        worksheet["CP60"] = "{}".format(self.penghasilan_neto_sebelumnya) or "0"
        worksheet["CP61"] = "{}".format(self.penghasilan_neto_setahun) or "0"
        worksheet["CP62"] = "{}".format(self.penghasilan_tidak_kena_pajak) or "0"
        worksheet["CP63"] = "{}".format(self.penghasilan_kena_pajak) or "0"
        worksheet["CP64"] = (
            "{}".format(self.pph_21_penghasilan_kena_pajak_setahun) or "0"
        )
        worksheet["CP65"] = "{}".format(self.pph_21_telah_dipotong_sebelumnya) or "0"
        worksheet["CP66"] = "{}".format(self.pph_21_terutang) or "0"
        worksheet["CP67"] = "{}".format(self.pph_21_26_telah_dipotong) or "0"

    def insert_identitas_pemotong(self, worksheet):
        npwp_pemotong = self.npwp_pemotong.split("-")
        worksheet["P72"] = npwp_pemotong[0]
        worksheet["AV72"] = npwp_pemotong[1]
        worksheet["BG72"] = npwp_pemotong[2]
        worksheet["P75"] = self.nama_pemotong
        tanggal = getdate(self.tanggal)
        worksheet["BW75"] = "{}".format(tanggal.day)
        worksheet["CF75"] = "{}".format(tanggal.month)
        worksheet["CL75"] = "{}".format(tanggal.year)

    def apply_styles(self, worksheet):
        arial_7 = Font(name="Arial", sz=7)
        col = worksheet.column_dimensions["E"]
        col.font = arial_7

    def get_spt_doc_template(self):
        template_path = frappe.get_module_path(
            "hr_add_on",
            "doctype",
            "spt_1721_a1",
            "isi_formulir_1721_a1_tahun_2017_template.xlsx",
        )
        workbook = load_workbook(template_path)
        return workbook
