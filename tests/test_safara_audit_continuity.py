"""Regresiones de la trazabilidad financiera crítica."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
STORAGE = (ROOT / "safara_supabase_storage.py").read_text(encoding="utf-8")
APP = (ROOT / "app_safara_test.py").read_text(encoding="utf-8")


class FinancialAuditContinuityTests(unittest.TestCase):
    def test_ticket_expense_and_audit_are_in_the_same_storage_operation(self):
        start = STORAGE.index("def crear_gasto_con_justificante_pendiente")
        end = STORAGE.index("def obtener_justificante_pendiente", start)
        section = STORAGE[start:end]
        self.assertIn("insert into safara.justificantes_pendientes", section)
        self.assertIn("insert into safara.auditoria", section)
        self.assertIn("gasto_registrado", section)

    def test_reimbursement_writes_an_audit_trace_only_when_it_succeeds(self):
        start = STORAGE.index("def marcar_gasto_abonado")
        end = STORAGE.index("def guardar_confesion", start)
        section = STORAGE[start:end]
        self.assertIn("if actualizado:", section)
        self.assertIn("insert into safara.auditoria", section)
        self.assertIn("gasto_abonado", section)

    def test_financial_package_contains_recent_audit_records(self):
        start = STORAGE.index("def obtener_archivo_financiero")
        section = STORAGE[start:]
        self.assertIn('"auditoria": self._run(callback)', section)
        self.assertIn("from safara.auditoria", section)
        self.assertIn("limit 1000", section)

    def test_app_does_not_create_a_second_async_audit_for_finance_events(self):
        self.assertNotIn('registrar_auditoria(\n                "gasto_registrado"', APP)
        self.assertNotIn('registrar_auditoria("gasto_abonado"', APP)


if __name__ == "__main__":
    unittest.main()
