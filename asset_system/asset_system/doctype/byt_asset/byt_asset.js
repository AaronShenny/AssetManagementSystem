frappe.ui.form.on("BYT Asset", {
    refresh: function (frm) {
        // Quick action buttons
	
        if (!frm.doc.__islocal) {
            if (frm.doc.status !== "Scrapped") {
                frm.add_custom_button(__("Move Asset"), function () {
                    frappe.new_doc("Asset Movement", {
                        asset: frm.doc.name,
                        from_location: frm.doc.location
                    });
                }, __("Actions"));

                frm.add_custom_button(__("Assign Asset"), function () {
                    frappe.new_doc("Asset Assignment", {
                        asset: frm.doc.name,
                        assigned_to: frm.doc.assigned_to
                    });
                }, __("Actions"));
            }

            frm.add_custom_button(__("View Movement History"), function () {
                frappe.set_route("List", "Asset Movement", { asset: frm.doc.name });
            }, __("History"));

            frm.add_custom_button(__("View Assignment History"), function () {
                frappe.set_route("List", "Asset Assignment", { asset: frm.doc.name });
            }, __("History"));
        }

        // Colour indicators
        if (frm.doc.status === "Available") {
            frm.page.set_indicator(__("Available"), "green");
        } else if (frm.doc.status === "Assigned") {
            frm.page.set_indicator(__("Assigned"), "blue");
        } else if (frm.doc.status === "Maintenance") {
            frm.page.set_indicator(__("Maintenance"), "orange");
        } else if (frm.doc.status === "Deregistered") {
            frm.page.set_indicator(__("Deregistered"), "red");
        }
    },

    assigned_to: function (frm) {
        if (frm.doc.assigned_to && frm.doc.status === "Available") {
            frm.set_value("status", "Assigned");
        }
        if (!frm.doc.assigned_to && frm.doc.status === "Assigned") {
            frm.set_value("status", "Available");
        }
    }
});

frappe.ui.form.on("BYT Asset", {
    setup(frm) {

        frm.fields_dict.specification.grid
            .get_field("specs").get_query = function(doc) {

            return {
                filters: {
                    category: doc.asset_category
                }
            };
        };
    }
});
