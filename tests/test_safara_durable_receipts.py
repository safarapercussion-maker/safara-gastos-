"""Regresiones del circuito de justificantes sin depender de Google externo."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
APP_SOURCE = (ROOT / "app_safara_test.py").read_text(encoding="utf-8")
STORAGE_SOURCE = (ROOT / "safara_google_storage.py").read_text(encoding="utf-8")
MIGRATION_SOURCE = (
    ROOT / "supabase" / "migrations" / "20261119100500_add_durable_receipt_queue.sql"
).read_text(encoding="utf-8")


class DurableReceiptTests(unittest.TestCase):
    def test_schema_keeps_pending_receipts_private(self):
        self.assertIn("safara.justificantes_pendientes", MIGRATION_SOURCE)
        self.assertIn("enable row level security", MIGRATION_SOURCE)
        self.assertIn("using (false)", MIGRATION_SOURCE)
        self.assertIn("octet_length(contenido) between 1 and 10485760", MIGRATION_SOURCE)

    def test_expense_is_protected_before_drive_upload(self):
        saved = APP_SOURCE.index("crear_gasto_con_justificante_pendiente")
        uploaded = APP_SOURCE.index("almacenamiento_drive.upload_receipt", saved)
        self.assertLess(saved, uploaded)
        self.assertIn("REINTENTAR JUSTIFICANTES PENDIENTES", APP_SOURCE)

    def test_drive_does_not_initialize_sheets(self):
        start = STORAGE_SOURCE.index("def _drive_client")
        end = STORAGE_SOURCE.index("def crear_carpeta_justificantes_propietaria", start)
        self.assertNotIn("gspread", STORAGE_SOURCE[start:end])
        self.assertIn("crear_carpeta_justificantes_propietaria", STORAGE_SOURCE)


if __name__ == "__main__":
    unittest.main()
