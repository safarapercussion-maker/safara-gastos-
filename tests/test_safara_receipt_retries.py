"""Regresiones de la cola segura de tickets y sus reintentos."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
STORAGE = (ROOT / "safara_supabase_storage.py").read_text(encoding="utf-8")
MIGRATION = (
    ROOT / "supabase" / "migrations"
    / "20261120121500_harden_pending_receipts_and_rehearsal_indexes.sql"
).read_text(encoding="utf-8")


class ReceiptRetryTests(unittest.TestCase):
    def test_retry_schedule_is_persisted_privately(self):
        self.assertIn("proximo_intento_en", MIGRATION)
        self.assertIn("ultimo_intento_en", MIGRATION)
        self.assertIn("justificantes_pendientes_reintento_idx", MIGRATION)

    def test_reserved_ticket_gets_a_delay_and_never_duplicates(self):
        start = STORAGE.index("def reservar_justificantes_pendientes")
        section = STORAGE[start: STORAGE.index("def confirmar_justificante_drive", start)]
        self.assertIn("for update skip locked", section)
        self.assertIn("proximo_intento_en = now() + interval '5 minutes'", section)

    def test_failed_drive_transfer_uses_backoff(self):
        start = STORAGE.index("def marcar_justificante_pendiente")
        section = STORAGE[start: STORAGE.index("def listar_justificantes_pendientes", start)]
        self.assertIn("least(60, power(2", section)
        self.assertIn("PENDIENTE_DRIVE", section)


if __name__ == "__main__":
    unittest.main()
