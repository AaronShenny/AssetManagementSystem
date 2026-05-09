import frappe
from frappe import _


def validate_dates(assigned_date, return_date):

    if return_date and assigned_date:

        if return_date < assigned_date:

            frappe.throw(
                _("Return Date cannot be before Assigned Date.")
            )
