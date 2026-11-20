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
        self.confirmed_reports = []
        self.failed_backups = []

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
        return {"gastos": [], "caja": [], "actuaciones": [], "auditoria": []}

    def terminar_mantenimiento_google(self, revision, backup):
        self.finished.append((revision, backup))

    def confirmar_informes_google(self, revision):
        self.confirmed_reports.append(revision)

    def fallar_respaldo_google(self, error):
        self.failed_backups.append(error)

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
            "auditoria": [{"Evento": "gasto_registrado", "Detalle": "Gasto 2026001 registrado"}],
        })
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            self.assertEqual(
                set(archive.namelist()),
                {
                    "gastos.csv",
                    "caja.csv",
                    "actuaciones.csv",
                    "auditoria.csv",
                    "SAFARA_Archivo_Financiero.xlsx",
                    "MANIFIESTO.json",
                },
            )
            manifest = json.loads(archive.read("MANIFIESTO.json"))
            gastos_csv = archive.read("gastos.csv")
            self.assertGreater(len(archive.read("SAFARA_Archivo_Financiero.xlsx")), 0)
        self.assertEqual(manifest["contenido"]["gastos"], 1)
        self.assertEqual(manifest["contenido"]["auditoria"], 1)
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
        self.assertEqual(database.confirmed_reports, [4])
        self.assertEqual(database.failed, [])
        self.assertIn("Informe Sincronización", google.reports)
        self.assertEqual(len(google.backups), 1)

    def test_report_sync_succeeds_when_the_optional_drive_backup_fails(self):
        class BackupUnavailableGoogle(FakeGoogle):
            def upload_backup(self, filename, content):
                raise RuntimeError("Drive no disponible")

        database = FakeDatabase()
        google = BackupUnavailableGoogle()
        self.assertTrue(run_google_maintenance(database, google))
        self.assertEqual(database.confirmed_reports, [4])
        self.assertEqual(database.finished, [])
        self.assertEqual(len(database.failed_backups), 1)
        self.assertIsNotNone(google.reports)

    def test_report_is_confirmed_before_the_optional_backup(self):
        database = FakeDatabase()
        run_google_maintenance(database, FakeGoogle())
        self.assertEqual(database.confirmed_reports, [4])
        self.assertEqual(database.finished, [(4, True)])

    def test_maintenance_treats_google_as_an_isolated_copy(self):
        class BrokenGoogle(FakeGoogle):
            def write_report_snapshot(self, reports):
                raise RuntimeError("Google temporalmente no disponible")

        database = FakeDatabase()
        self.assertFalse(run_google_maintenance(database, BrokenGoogle()))
        self.assertEqual(database.finished, [])
        self.assertEqual(len(database.failed), 1)

    def test_maintenance_skips_when_no_work_is_due(self):
        database = FakeDatabase(work=None)
        self.assertFalse(run_google_maintenance(database, FakeGoogle()))
        self.assertEqual(database.finished, [])


if __name__ == "__main__":
    unittest.main()
