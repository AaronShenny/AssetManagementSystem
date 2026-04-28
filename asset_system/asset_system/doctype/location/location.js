frappe.ui.form.on("Location", {
    refresh: function (frm) {
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__("View Assets Here"), function () {
                frappe.set_route("List", "BYT Asset", { location: frm.doc.name });
            });
        }
    }
});
