frappe.ui.form.on("Asset Assignment", {

    asset: function (frm) {

        if (frm.doc.asset) {

            frappe.db.get_value(
                "BYT Asset",
                frm.doc.asset,
                "assigned_to",

                function (r) {

                    if (
                        r &&
                        r.assigned_to &&
                        !frm.doc.assigned_to
                    ) {

                        frm.set_value(
                            "assigned_to",
                            r.assigned_to
                        );
                    }
                }
            );
        }
    }
});