// Copyright (c) 2019, MIS and contributors
// For license information, please see license.txt

function calculate_jumlah_bruto(frm) {
    let jumlah_bruto = (
        frm.doc.gaji_pensiunan + frm.doc.tunjangan_pph 
        + frm.doc.tunjangan_lainnya + frm.doc.honorarium + frm.doc.premi_asuransi 
        + frm.doc.penerimaan_natura + frm.doc.bonus
    );
    frm.set_value("jumlah_bruto", jumlah_bruto);
    calculate_spt(frm);
}

function calculate_jumlah_pengurangan(frm) {
    let jumlah_pengurangan = (
        frm.doc.biaya_jabatan + frm.doc.iuran_pensiun
    );
    frm.set_value("jumlah_pengurangan", jumlah_pengurangan);
    calculate_spt(frm);
}

function calculate_spt(frm) {
    let jumlah_netto = (
        frm.doc.jumlah_bruto - frm.doc.jumlah_pengurangan
    );
    frm.set_value("jumlah_netto", jumlah_netto);
    let penghasilan_neto_setahun = (
        frm.doc.jumlah_netto + frm.doc.penghasilan_neto_sebelumnya
    )
    frm.set_value("penghasilan_neto_setahun", penghasilan_neto_setahun);
    let penghasilan_kena_pajak = (
        frm.doc.penghasilan_neto_setahun - frm.doc.penghasilan_tidak_kena_pajak
    )
    frm.set_value("penghasilan_kena_pajak", penghasilan_kena_pajak);
    let pph_21_penghasilan_kena_pajak_setahun = (
        frm.doc.penghasilan_kena_pajak * 0.05
    )
    frm.set_value("pph_21_penghasilan_kena_pajak_setahun", pph_21_penghasilan_kena_pajak_setahun);
    let pph_21_terutang = (
        frm.doc.pph_21_penghasilan_kena_pajak_setahun
        - frm.doc.pph_21_telah_dipotong_sebelumnya
    )
    frm.set_value("pph_21_terutang", pph_21_terutang);
    frm.set_value("pph_21_26_telah_dipotong", pph_21_terutang);
}

frappe.ui.form.on('SPT 1721_A1', {
    refresh: function (frm) {

    },
    onload: function(frm){
        if (frm.doc.docstatus == 0) {
        }
    },
    gaji_pensiunan: function(frm){
        if (frm.doc.docstatus == 0) {
            calculate_jumlah_bruto(frm);
        }
    },
    tunjangan_pph: function(frm){
        if (frm.doc.docstatus == 0) {
            calculate_jumlah_bruto(frm);
        }
    },
    tunjangan_lainnya: function(frm){
        if (frm.doc.docstatus == 0) {
            calculate_jumlah_bruto(frm);
        }
    },
    honorarium: function(frm){
        if (frm.doc.docstatus == 0) {
            calculate_jumlah_bruto(frm);
        }
    },
    premi_asuransi: function(frm){
        if (frm.doc.docstatus == 0) {
            calculate_jumlah_bruto(frm);
        }
    },
    penerimaan_natura: function(frm){
        if (frm.doc.docstatus == 0) {
            calculate_jumlah_bruto(frm);
        }
    },
    bonus: function(frm){
        if (frm.doc.docstatus == 0) {
            calculate_jumlah_bruto(frm);
        }
    },
    biaya_jabatan: function(frm){
        if (frm.doc.docstatus == 0) {
            calculate_jumlah_pengurangan(frm);
        }
    },
    iuran_pensiun: function(frm){
        if (frm.doc.docstatus == 0) {
            calculate_jumlah_pengurangan(frm);
        }
    },
    penghasilan_neto_sebelumnya: function(frm){
        if (frm.doc.docstatus == 0) {
            calculate_spt(frm);
        }
    },
    penghasilan_tidak_kena_pajak: function(frm){
        if (frm.doc.docstatus == 0) {
            calculate_spt(frm);
        }
    },
    pph_21_telah_dipotong_sebelumnya: function(frm){
        if (frm.doc.docstatus == 0) {
            calculate_spt(frm);
        }
    },
});
