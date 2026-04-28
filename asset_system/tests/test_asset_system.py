"""
Unit tests for Asset Management System.

Run:
    python -m pytest asset_system/asset_system/tests/ -v

The conftest.py in this directory installs a frappe mock BEFORE any imports.
"""
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Tests for asset.py controller logic
# ---------------------------------------------------------------------------

class TestAssetController(unittest.TestCase):

    def test_allowed_transition_available_to_in_use(self):
        """Available → In Use must be permitted."""
        from asset_system.asset_system.doctype.byt_asset.byt_asset import ALLOWED_TRANSITIONS
        self.assertIn("In Use", ALLOWED_TRANSITIONS["Available"])

    def test_disallowed_transition_scrapped_to_available(self):
        """Scrapped state must have no allowed transitions (terminal)."""
        from asset_system.asset_system.doctype.byt_asset.byt_asset import ALLOWED_TRANSITIONS
        self.assertEqual(ALLOWED_TRANSITIONS["Scrapped"], [])

    def test_all_statuses_present_in_transitions(self):
        from asset_system.asset_system.doctype.byt_asset.byt_asset import ALLOWED_TRANSITIONS
        for status in ("Available", "In Use", "Maintenance", "Scrapped"):
            self.assertIn(status, ALLOWED_TRANSITIONS)

    def test_maintenance_can_transition_to_available(self):
        from asset_system.asset_system.doctype.byt_asset.byt_asset import ALLOWED_TRANSITIONS
        self.assertIn("Available", ALLOWED_TRANSITIONS["Maintenance"])

    def test_in_use_can_transition_to_scrapped(self):
        from asset_system.asset_system.doctype.byt_asset.byt_asset import ALLOWED_TRANSITIONS
        self.assertIn("Scrapped", ALLOWED_TRANSITIONS["In Use"])


# ---------------------------------------------------------------------------
# Tests for asset_movement.py controller logic
# ---------------------------------------------------------------------------

class TestAssetMovementController(unittest.TestCase):

    def test_same_location_raises(self):
        """Validate raises when from_location == to_location."""
        import frappe as mock_frappe
        mock_frappe.db.get_value.return_value = "Available"
        mock_frappe.session.user = "Administrator"

        from asset_system.asset_system.doctype.asset_movement.asset_movement import AssetMovement

        doc = AssetMovement.__new__(AssetMovement)
        doc.asset = "AST-0001"
        doc.from_location = "Warehouse A"
        doc.to_location = "Warehouse A"
        doc.moved_by = None

        with self.assertRaises((ValueError, Exception)):
            doc._validate_locations()

    def test_different_locations_passes(self):
        """Different from/to locations should not raise."""
        import frappe as mock_frappe
        original_throw = mock_frappe.throw
        mock_frappe.throw = MagicMock()

        from asset_system.asset_system.doctype.asset_movement.asset_movement import AssetMovement

        doc = AssetMovement.__new__(AssetMovement)
        doc.asset = "AST-0001"
        doc.from_location = "Warehouse A"
        doc.to_location = "Warehouse B"
        doc.moved_by = None
        doc._validate_locations()

        mock_frappe.throw.assert_not_called()
        mock_frappe.throw = original_throw

    def test_scrapped_asset_raises(self):
        """Validate raises when asset is Scrapped."""
        import frappe as mock_frappe
        mock_frappe.db.get_value.return_value = "Scrapped"

        from asset_system.asset_system.doctype.asset_movement.asset_movement import AssetMovement

        doc = AssetMovement.__new__(AssetMovement)
        doc.asset = "AST-0001"

        with self.assertRaises((ValueError, Exception)):
            doc._validate_not_scrapped()

    def test_non_scrapped_asset_passes(self):
        """Available asset should not raise."""
        import frappe as mock_frappe
        mock_frappe.db.get_value.return_value = "Available"
        original_throw = mock_frappe.throw
        mock_frappe.throw = MagicMock()

        from asset_system.asset_system.doctype.asset_movement.asset_movement import AssetMovement

        doc = AssetMovement.__new__(AssetMovement)
        doc.asset = "AST-0001"
        doc._validate_not_scrapped()

        mock_frappe.throw.assert_not_called()
        mock_frappe.throw = original_throw


# ---------------------------------------------------------------------------
# Tests for asset_assignment.py controller logic
# ---------------------------------------------------------------------------

class TestAssetAssignmentController(unittest.TestCase):

    def test_return_before_assigned_raises(self):
        """Return date must not precede assigned date."""
        from asset_system.asset_system.doctype.asset_assignment.asset_assignment import AssetAssignment

        doc = AssetAssignment.__new__(AssetAssignment)
        doc.assigned_date = "2024-06-01"
        doc.return_date = "2024-05-01"  # before assigned date

        with self.assertRaises((ValueError, Exception)):
            doc._validate_dates()

    def test_valid_dates_pass(self):
        """Return date on or after assigned date should not raise."""
        import frappe as mock_frappe
        original_throw = mock_frappe.throw
        mock_frappe.throw = MagicMock()

        from asset_system.asset_system.doctype.asset_assignment.asset_assignment import AssetAssignment

        doc = AssetAssignment.__new__(AssetAssignment)
        doc.assigned_date = "2024-06-01"
        doc.return_date = "2024-06-15"
        doc._validate_dates()

        mock_frappe.throw.assert_not_called()
        mock_frappe.throw = original_throw

    def test_scrapped_asset_cannot_be_assigned(self):
        import frappe as mock_frappe
        mock_frappe.db.get_value.return_value = "Scrapped"

        from asset_system.asset_system.doctype.asset_assignment.asset_assignment import AssetAssignment

        doc = AssetAssignment.__new__(AssetAssignment)
        doc.asset = "AST-0001"

        with self.assertRaises((ValueError, Exception)):
            doc._validate_asset_available()

    def test_available_asset_can_be_assigned(self):
        import frappe as mock_frappe
        mock_frappe.db.get_value.return_value = "Available"
        original_throw = mock_frappe.throw
        mock_frappe.throw = MagicMock()

        from asset_system.asset_system.doctype.asset_assignment.asset_assignment import AssetAssignment

        doc = AssetAssignment.__new__(AssetAssignment)
        doc.asset = "AST-0001"
        doc._validate_asset_available()

        mock_frappe.throw.assert_not_called()
        mock_frappe.throw = original_throw


# ---------------------------------------------------------------------------
# Tests for API methods (api/asset_api.py)
# ---------------------------------------------------------------------------

class TestAssetAPI(unittest.TestCase):

    def test_create_asset_missing_name_raises(self):
        from asset_system.api.asset_api import create_asset
        with self.assertRaises((ValueError, Exception)):
            create_asset(asset_name="", category="Electronics")

    def test_create_asset_missing_category_raises(self):
        from asset_system.api.asset_api import create_asset
        with self.assertRaises((ValueError, Exception)):
            create_asset(asset_name="Laptop", category="")

    def test_get_assets_returns_dict(self):
        import frappe as mock_frappe
        mock_frappe.db.count.return_value = 2
        mock_frappe.get_all.return_value = [
            {"name": "AST-0001", "asset_name": "Laptop", "status": "Available"},
            {"name": "AST-0002", "asset_name": "Monitor", "status": "In Use"},
        ]

        from asset_system.api.asset_api import get_assets

        result = get_assets()
        self.assertIn("assets", result)
        self.assertIn("total", result)
        self.assertEqual(result["total"], 2)
        self.assertEqual(len(result["assets"]), 2)

    def test_get_assets_pagination(self):
        import frappe as mock_frappe
        mock_frappe.db.count.return_value = 50
        mock_frappe.get_all.return_value = []

        from asset_system.api.asset_api import get_assets

        result = get_assets(page=2, page_length=10)
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["page_length"], 10)

    def test_get_asset_history_returns_structure(self):
        import frappe as mock_frappe
        mock_frappe.get_doc.return_value = MagicMock()
        mock_frappe.get_all.return_value = []

        from asset_system.api.asset_api import get_asset_history

        result = get_asset_history("AST-0001")
        self.assertIn("movements", result)
        self.assertIn("assignments", result)
        self.assertEqual(result["asset"], "AST-0001")

    def test_get_asset_history_missing_asset_raises(self):
        from asset_system.api.asset_api import get_asset_history
        with self.assertRaises((ValueError, Exception)):
            get_asset_history("")

    def test_get_dashboard_stats_keys(self):
        import frappe as mock_frappe
        mock_frappe.db.count.return_value = 5

        from asset_system.api.asset_api import get_dashboard_stats

        result = get_dashboard_stats()
        for key in ("total", "available", "in_use", "maintenance", "scrapped"):
            self.assertIn(key, result)

    def test_move_asset_missing_args_raises(self):
        from asset_system.api.asset_api import move_asset
        with self.assertRaises((ValueError, Exception)):
            move_asset(asset="", to_location="Warehouse B")

    def test_assign_asset_missing_args_raises(self):
        from asset_system.api.asset_api import assign_asset
        with self.assertRaises((ValueError, Exception)):
            assign_asset(asset="AST-0001", assigned_to="")


if __name__ == "__main__":
    unittest.main()
