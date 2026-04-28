/* Asset Management System – client-side utilities */

frappe.provide("asset_system");

/**
 * Show a quick-action dialog for adding a new Asset.
 */
asset_system.quick_add_asset = function () {
    const d = new frappe.ui.Dialog({
        title: __("Add New Asset"),
        fields: [
            {
                fieldname: "asset_name",
                fieldtype: "Data",
                label: __("Asset Name"),
                reqd: 1
            },
            {
                fieldname: "category",
                fieldtype: "Link",
                label: __("Category"),
                options: "Asset Category",
                reqd: 1
            },
            {
                fieldname: "location",
                fieldtype: "Link",
                label: __("Location"),
                options: "Location"
            },
            {
                fieldname: "serial_number",
                fieldtype: "Data",
                label: __("Serial Number")
            },
            {
                fieldname: "purchase_date",
                fieldtype: "Date",
                label: __("Purchase Date")
            },
            {
                fieldname: "purchase_value",
                fieldtype: "Currency",
                label: __("Purchase Value")
            }
        ],
        primary_action_label: __("Create"),
        primary_action: function (values) {
            frappe.call({
                method: "asset_system.api.asset_api.create_asset",
                args: values,
                callback: function (r) {
                    if (r.message) {
                        d.hide();
                        frappe.show_alert({
                            message: __("Asset {0} created.", [r.message.asset_id]),
                            indicator: "green"
                        });
                        frappe.set_route("Form", "Asset", r.message.asset_id);
                    }
                }
            });
        }
    });
    d.show();
};

/**
 * Show a quick-action dialog to move an asset.
 *
 * @param {string} asset - Asset name (e.g. AST-0001)
 */
asset_system.quick_move_asset = function (asset) {
    const d = new frappe.ui.Dialog({
        title: __("Move Asset"),
        fields: [
            {
                fieldname: "asset",
                fieldtype: "Link",
                label: __("Asset"),
                options: "Asset",
                reqd: 1,
                default: asset || ""
            },
            {
                fieldname: "to_location",
                fieldtype: "Link",
                label: __("To Location"),
                options: "Location",
                reqd: 1
            },
            {
                fieldname: "movement_date",
                fieldtype: "Date",
                label: __("Movement Date"),
                default: frappe.datetime.get_today()
            },
            {
                fieldname: "remarks",
                fieldtype: "Small Text",
                label: __("Remarks")
            }
        ],
        primary_action_label: __("Move"),
        primary_action: function (values) {
            frappe.call({
                method: "asset_system.api.asset_api.move_asset",
                args: values,
                callback: function (r) {
                    if (r.message) {
                        d.hide();
                        frappe.show_alert({
                            message: __("Asset moved to {0}.", [r.message.to_location]),
                            indicator: "green"
                        });
                    }
                }
            });
        }
    });
    d.show();
};

/**
 * Show a quick-action dialog to assign an asset to a user.
 *
 * @param {string} asset - Asset name (e.g. AST-0001)
 */
asset_system.quick_assign_asset = function (asset) {
    const d = new frappe.ui.Dialog({
        title: __("Assign Asset"),
        fields: [
            {
                fieldname: "asset",
                fieldtype: "Link",
                label: __("Asset"),
                options: "Asset",
                reqd: 1,
                default: asset || ""
            },
            {
                fieldname: "assigned_to",
                fieldtype: "Link",
                label: __("Assign To"),
                options: "User",
                reqd: 1
            },
            {
                fieldname: "assigned_date",
                fieldtype: "Date",
                label: __("Assigned Date"),
                default: frappe.datetime.get_today()
            },
            {
                fieldname: "return_date",
                fieldtype: "Date",
                label: __("Expected Return Date")
            },
            {
                fieldname: "remarks",
                fieldtype: "Small Text",
                label: __("Remarks")
            }
        ],
        primary_action_label: __("Assign"),
        primary_action: function (values) {
            frappe.call({
                method: "asset_system.api.asset_api.assign_asset",
                args: values,
                callback: function (r) {
                    if (r.message) {
                        d.hide();
                        frappe.show_alert({
                            message: __("Asset assigned to {0}.", [r.message.assigned_to]),
                            indicator: "green"
                        });
                    }
                }
            });
        }
    });
    d.show();
};

// Expose quick actions on the global frappe namespace for easy access
frappe.provide("frappe.asset_system");
frappe.asset_system = asset_system;
