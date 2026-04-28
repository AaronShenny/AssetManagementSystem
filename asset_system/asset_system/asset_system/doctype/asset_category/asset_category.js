frappe.ui.form.on("Asset Category", {
    refresh: function (frm) {
        frm.set_intro(
            frm.doc.__islocal
                ? __("Define the category for assets, including depreciation settings.")
                : ""
        );
    }
});
