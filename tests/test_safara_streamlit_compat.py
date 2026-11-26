"""Keep the Administration navigation visible with the pinned Streamlit version."""

import ast
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class Streamlit151CompatibilityTests(unittest.TestCase):
    def test_administration_uses_labeled_buttons_instead_of_segments(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("streamlit==1.51.0", requirements)
        tree = ast.parse((ROOT / "app_safara_test.py").read_text(encoding="utf-8"))
        segmented = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "st"
            and node.func.attr == "segmented_control"
        ]
        self.assertEqual(segmented, [])
        source = (ROOT / "app_safara_test.py").read_text(encoding="utf-8")
        self.assertIn('("Actividad", "Safarers", "Control")', source)
        self.assertIn('key=f"admin_tab_{clave}"', source)
        self.assertIn('on_click=seleccionar_area_administracion', source)


if __name__ == "__main__":
    unittest.main()
