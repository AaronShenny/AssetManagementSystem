import frappe

def execute(filters=None):

    columns = [
        {
            "label": "Metric",
            "fieldname": "metric",
            "fieldtype": "Data",
            "width": 250
        },
        {
            "label": "Count",
            "fieldname": "count",
            "fieldtype": "Int",
            "width": 150
        }
    ]

    data = [
        ["Total Assets", frappe.db.count("BYT Asset")],
        ["Allocated Assets", frappe.db.count("BYT Asset", {"status": "Allocated"})],
        ["Maintenance Assets", frappe.db.count("BYT Asset", {"status": "Maintenance"})],
        ["Deregistered Assets", frappe.db.count("BYT Asset", {"status": "Deregistered"})],
    ]

    return columns, data