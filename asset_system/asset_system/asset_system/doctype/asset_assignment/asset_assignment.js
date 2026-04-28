frappe.ui.form.on("Asset Assignment", {
    refresh: function (frm) {
        if (frm.doc.docstatus === 1 && !frm.doc.return_date) {
            frm.add_custom_button(__("Return Asset"), function () {
                frappe.prompt(
                    {
                        fieldname: "return_date",
                        fieldtype: "Date",
                        label: __("Return Date"),
                        reqd: 1,
                        default: frappe.datetime.get_today()
                    },
                    function (values) {
                        frappe.call({
                            method: "asset_system.api.asset_api.return_asset",
                            args: {
                                assignment_name: frm.doc.name,
                                return_date: values.return_date
                            },
                            callback: function (r) {
                                if (!r.exc) {
                                    frm.reload_doc();
                                }
                            }
                        });
                    },
                    __("Set Return Date"),
                    __("Return")
                );
            });
        }
    },

    asset: function (frm) {
        if (frm.doc.asset) {
            frappe.db.get_value("Asset", frm.doc.asset, "assigned_to", function (r) {
                if (r && r.assigned_to && !frm.doc.assigned_to) {
                    frm.set_value("assigned_to", r.assigned_to);
                }
            });
        }
    }
});
