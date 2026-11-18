import io
import hashlib
import json
import unittest
import zipfile

from safara_google_storage import REPORT_SCHEMA
from safara_maintenance import _create_financial_archive, run_google_maintenance


class FakeDatabase:
    def __init__(self, work="DEFAULT"):
        self.work = {
            "sheets_revision": 4,
            "respaldo_pendiente": True,
        } if work == "DEFAULT" else work
        self.finished = []
        self.failed = []

    def iniciar_mantenimiento_google(self):
        return self.work

    def obtener_informes_google(self):
        return {
            "Informe Socios": [{"Nombre": "Ana", "Rol": "admin", "Instrumento": "Caja", "Activo desde": "2026-11-16"}],
            "Informe Invitaciones": [],
            "Informe Votos": [],
            "Informe Actuaciones": [],
            "Informe Gastos": [],
            "Informe Caja": [],
        }

    def obtener_archivo_financiero(self):
        return {"gastos": [], "caja": [], "actuaciones": []}

    def terminar_mantenimiento_google(self, revision, backup):
        self.finished.append((revision, backup))

    def fallar_mantenimiento_google(self, error):
        self.failed.append(error)


class FakeGoogle:
    def __init__(self):
        self.reports = None
        self.backups = []

    def write_report_snapshot(self, reports):
        self.reports = reports

    def upload_backup(self, filename, content):
        self.backups.append((filename, content))
        return "drive-file-id"


class MaintenanceTests(unittest.TestCase):
    def test_report_schema_excludes_sensitive_columns(self):
        headers = {header.lower() for values in REPORT_SCHEMA.values() for header in values}
        for sensitive in ("password_hash", "password_salt", "teléfono", "fecha de nacimiento", "código"):
            self.assertNotIn(sensitive, headers)

    def test_archive_contains_financial_tables_and_manifest(self):
        payload = _create_financial_archive({
            "gastos": [{"ID": 1, "Importe": 24.5}],
            "caja": [{"Concepto": "Saldo de caja", "Importe": 10}],
            "actuaciones": [],
        })
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            self.assertEqual(set(archive.namelist()), {"gastos.csv", "caja.csv", "actuaciones.csv", "MANIFIESTO.json"})
            manifest = json.loads(archive.read("MANIFIESTO.json"))
            gastos_csv = archive.read("gastos.csv")
        self.assertEqual(manifest["contenido"]["gastos"], 1)
        self.assertIn("gastos.csv", manifest["sha256_archivos"])
        self.assertEqual(
            manifest["sha256_archivos"]["gastos.csv"],
            hashlib.sha256(gastos_csv).hexdigest(),
        )

    def test_maintenance_writes_report_and_daily_backup(self):
        database = FakeDatabase()
        google = FakeGoogle()
        self.assertTrue(run_google_maintenance(database, google))
        self.assertEqual(database.finished, [(4, True)])
        self.assertEqual(database.failed, [])
        self.assertIn("Informe Sincronización", google.reports)
        self.assertEqual(len(google.backups), 1)

    def test_maintenance_skips_when_no_work_is_due(self):
        database = FakeDatabase(work=None)
        self.assertFalse(run_google_maintenance(database, FakeGoogle()))
        self.assertEqual(database.finished, [])


if __name__ == "__main__":
    unittest.main()
