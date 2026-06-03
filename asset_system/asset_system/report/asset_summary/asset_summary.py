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
        ["Allocated", frappe.db.count("BYT Asset", {"status": "Assigned"})],
        ["Available", frappe.db.count("BYT Asset", {"status": "Available"})],
        ["Under Maintenance", frappe.db.count("BYT Asset", {"status": "Maintenance"})],
        ["Deregistered", frappe.db.count("BYT Asset", {"status": "Deregistered"})],
    ]

    return columns, data
