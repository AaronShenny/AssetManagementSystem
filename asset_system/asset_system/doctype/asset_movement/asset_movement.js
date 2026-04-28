frappe.ui.form.on("Asset Movement", {
    refresh: function (frm) {
        if (frm.doc.docstatus === 1) {
            frm.page.set_indicator(__("Submitted"), "blue");
        }
    },

    asset: function (frm) {
        if (frm.doc.asset) {
            frappe.db.get_value("BYT Asset", frm.doc.asset, "location", function (r) {
                if (r && r.location) {
                    frm.set_value("from_location", r.location);
                }
            });
        }
    }
});
