"""Prevent unsupported Streamlit widget arguments from breaking Administration."""

import ast
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SEGMENTED_CONTROL_151_KEYWORDS = {
    "selection_mode", "default", "format_func", "key", "help", "on_change",
    "args", "kwargs", "disabled", "label_visibility", "width",
}


class Streamlit151CompatibilityTests(unittest.TestCase):
    def test_administration_control_uses_supported_arguments(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("streamlit==1.51.0", requirements)
        tree = ast.parse((ROOT / "app_safara_test.py").read_text(encoding="utf-8"))
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "st"
            and node.func.attr == "segmented_control"
        ]
        self.assertEqual(len(calls), 1)
        unsupported = {
            keyword.arg for keyword in calls[0].keywords
            if keyword.arg not in SEGMENTED_CONTROL_151_KEYWORDS
        }
        self.assertEqual(unsupported, set())


if __name__ == "__main__":
    unittest.main()
