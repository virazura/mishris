function show_upload_form (frm) {
    var $wrapper = $(cur_frm.fields_dict.upload_attendance.wrapper).empty();
    frappe.upload.make({
        parent: $wrapper,
        args: {
            method: 'mishris.hr_add_on.upload_attendance_add_on.upload'
        },
        no_socketio: true,
        sample_url: "e.g. http://example.com/attendance.csv",
        callback: function (attachment, r) {
            var $log_wrapper = $(cur_frm.fields_dict.import_log.wrapper).empty();
            if (!r.messages) {
                r.messages = [];
            }
            if (r.exc || r.error) {
                r.messages = $.map(r.message.messages, function (v) {
                    var msg = v.replace("Inserted", "Valid")
                        .replace("Updated", "Valid").split("<");
                    if (msg.length > 1) {
                        v = msg[0] + (msg[1].split(">").slice(-1)[0]);
                    } else {
                        v = msg[0];
                    }
                    return v;
                });
                r.messages = ["<h4 style='color:red'>" + __("Import Failed!") + "</h4>"]
                    .concat(r.messages)
            } else {
                r.messages = ["<h4 style='color:green'>" + __("Import Successful!") + "</h4>"].
                concat(r.message.messages)
            }
            $.each(r.messages, function (i, v) {
                var $p = $('<p>').html(v).appendTo($log_wrapper);
                if (v.substr(0, 5) == 'Error') {
                    $p.css('color', 'red');
                } else if (v.substr(0, 8) == 'Inserted') {
                    $p.css('color', 'green');
                } else if (v.substr(0, 7) == 'Updated') {
                    $p.css('color', 'green');
                } else if (v.substr(0, 5) == 'Valid') {
                    $p.css('color', '#777');
                }
            });
            // rename button
            $wrapper.find('form input[type="submit"]')
                .attr('value', 'Upload and Import')
        }
    });
}


frappe.ui.form.on("Upload Attendance", {
    download_template_button: function(frm){
        window.location.href = repl(frappe.request.url +
            '?cmd=%(cmd)s&from_date=%(from_date)s&to_date=%(to_date)s', {
            cmd: "mishris.hr_add_on.upload_attendance_add_on.download_template",
            from_date: frm.doc.att_fr_date,
            to_date: frm.doc.att_to_date,
        });
    },
    refresh: function(frm){
        show_upload_form(frm);
    }
    
});