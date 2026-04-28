"""
conftest.py – Set up frappe mock before any test module imports our code.
"""
import sys
import types
from unittest.mock import MagicMock


def _build_frappe_mock():
    """Return a fully-featured frappe mock that satisfies all module-level imports."""
    # -----------------------------------------------------------------------
    # Build real ModuleType objects for frappe and its sub-modules so that
    # `from frappe.utils import ...` and similar imports resolve correctly.
    # -----------------------------------------------------------------------
    frappe_pkg = types.ModuleType("frappe")
    frappe_pkg.__path__ = []  # mark as package
    frappe_pkg.__package__ = "frappe"

    # frappe.utils
    utils_mod = types.ModuleType("frappe.utils")
    utils_mod.today = lambda: "2024-01-01"
    utils_mod.now = lambda: "2024-01-01 00:00:00"
    utils_mod.now_datetime = lambda: "2024-01-01 00:00:00"
    frappe_pkg.utils = utils_mod
    sys.modules["frappe.utils"] = utils_mod

    # frappe.model
    model_mod = types.ModuleType("frappe.model")
    model_mod.__path__ = []
    frappe_pkg.model = model_mod
    sys.modules["frappe.model"] = model_mod

    # frappe.model.document
    doc_base = type("Document", (), {
        "is_new": lambda self: False,
        "insert": MagicMock(),
        "save": MagicMock(),
        "submit": MagicMock(),
    })
    model_doc_mod = types.ModuleType("frappe.model.document")
    model_doc_mod.Document = doc_base
    model_mod.document = model_doc_mod
    sys.modules["frappe.model.document"] = model_doc_mod

    # -----------------------------------------------------------------------
    # Core frappe namespace attributes
    # -----------------------------------------------------------------------
    frappe_pkg._ = lambda x, *a, **kw: x
    frappe_pkg.whitelist = lambda fn=None, **kw: (fn if fn else lambda f: f)
    frappe_pkg.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
    frappe_pkg.ValidationError = type("ValidationError", (ValueError,), {})
    frappe_pkg.PermissionError = type("PermissionError", (PermissionError,), {})

    def _throw(msg, *a, **kw):
        raise ValueError(msg)

    frappe_pkg.throw = _throw
    frappe_pkg.session = types.SimpleNamespace(user="Administrator")
    frappe_pkg.db = MagicMock()
    frappe_pkg.get_doc = MagicMock()
    frappe_pkg.get_all = MagicMock(return_value=[])
    frappe_pkg.sendmail = MagicMock()

    return frappe_pkg


# Install mock BEFORE any test imports our source modules
_frappe_mock = _build_frappe_mock()
sys.modules["frappe"] = _frappe_mock

