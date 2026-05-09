from frappe.model.document import Document
from .service import AssetAssignmentService


class AssetAssignment(Document):

    def validate(self):
        AssetAssignmentService.validate(self)

    def on_submit(self):
        AssetAssignmentService.assign(self)

    def on_cancel(self):
        AssetAssignmentService.unassign(self)
