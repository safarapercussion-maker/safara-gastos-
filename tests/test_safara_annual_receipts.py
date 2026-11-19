"""Regresiones del archivo anual de justificantes."""

from pathlib import Path
import unittest

from safara_supabase_storage import SupabaseSafaraStorage


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_SOURCE = (
    ROOT / "supabase" / "migrations" / "20261119224000_add_annual_receipt_references.sql"
).read_text(encoding="utf-8")
GOOGLE_SOURCE = (ROOT / "safara_google_storage.py").read_text(encoding="utf-8")


class FakeCursor:
    def __init__(self):
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((" ".join(query.split()), params))

    def fetchone(self):
        return {"siguiente": 4}


class AnnualReceiptTests(unittest.TestCase):
    def test_reference_migration_is_unique_and_year_based(self):
        self.assertIn("referencia_anual", MIGRATION_SOURCE)
        self.assertIn("gastos_referencia_anual_formato", MIGRATION_SOURCE)
        self.assertIn("gastos_referencia_anual_unica_idx", MIGRATION_SOURCE)

    def test_new_ticket_name_keeps_only_safe_extension(self):
        self.assertEqual(
            SupabaseSafaraStorage._nombre_ticket("2026-004", "entrada.JPG"),
            "2026-004_ticket.jpg",
        )
        self.assertEqual(
            SupabaseSafaraStorage._nombre_ticket("2026-004", "entrada.exe"),
            "2026-004_ticket.bin",
        )

    def test_next_reference_is_locked_for_concurrent_registrations(self):
        storage = object.__new__(SupabaseSafaraStorage)
        cursor = FakeCursor()
        self.assertEqual(storage._siguiente_referencia_gasto(cursor, "2026-11-20"), "2026-004")
        self.assertIn("pg_advisory_xact_lock", cursor.calls[0][0])
        self.assertIn("referencia_anual like", cursor.calls[1][0])

    def test_drive_archive_uses_a_root_and_year_folder_without_changing_file_ids(self):
        self.assertIn('body={"name": "RECIBOS SAFARA"}', GOOGLE_SOURCE)
        self.assertIn("def _carpeta_anual", GOOGLE_SOURCE)
        self.assertIn("addParents=carpeta_anual", GOOGLE_SOURCE)
        self.assertIn("f\"{referencia}_ticket{extension}\"", (ROOT / "safara_supabase_storage.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
