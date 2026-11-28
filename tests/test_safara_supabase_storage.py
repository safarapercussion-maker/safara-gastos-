import unittest

from safara_supabase_storage import (
    SupabaseSafaraStorage,
    SupabaseStorageConfig,
    SupabaseStorageOperationError,
    is_enabled,
)


class FakeCursor:
    def __init__(self, records):
        self.records = list(records)
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((" ".join(query.split()), params))

    def fetchone(self):
        return self.records.pop(0)


def storage_with(cursor):
    storage = object.__new__(SupabaseSafaraStorage)
    storage._run = lambda callback: callback(cursor)
    return storage


class RoleManagementTests(unittest.TestCase):
    def test_admin_can_promote_a_normal_user_and_audit_is_written(self):
        cursor = FakeCursor([
            {"id": "admin-id", "rol": "admin"},
            {"id": "user-id", "rol": "usuario", "nombre": "Persona Prueba"},
        ])

        updated = storage_with(cursor).actualizar_rol_usuario(
            "Persona Prueba", "admin", "Administración Prueba"
        )

        self.assertTrue(updated)
        queries = [query for query, _ in cursor.calls]
        self.assertTrue(any("pg_advisory_xact_lock" in query for query in queries))
        self.assertTrue(any("update safara.usuarios set rol=%s" in query for query in queries))
        self.assertTrue(any("insert into safara.auditoria" in query for query in queries))

    def test_cannot_demote_the_last_administrator(self):
        cursor = FakeCursor([
            {"id": "admin-id", "rol": "admin"},
            {"id": "other-admin-id", "rol": "admin", "nombre": "Otro Admin"},
            {"total": 1},
        ])

        with self.assertRaises(SupabaseStorageOperationError):
            storage_with(cursor).actualizar_rol_usuario(
                "Otro Admin", "usuario", "Administración Prueba"
            )


class ConfigurationCompatibilityTests(unittest.TestCase):
    URL = "postgresql://postgres.example:secret@aws-1-eu-west-1.pooler.supabase.com:5432/postgres?sslmode=require"

    def test_accepts_existing_root_level_configuration(self):
        secrets = {"enable_supabase_storage": True, "database_url": self.URL}
        self.assertTrue(is_enabled(secrets))
        self.assertEqual(SupabaseStorageConfig.from_secrets(secrets).database_url, self.URL)

    def test_accepts_configuration_under_the_supabase_section(self):
        secrets = {"safara_supabase_storage": {"database_url": self.URL}}
        self.assertTrue(is_enabled(secrets))
        self.assertEqual(SupabaseStorageConfig.from_secrets(secrets).database_url, self.URL)

    def test_recovers_legacy_url_moved_into_google_section(self):
        secrets = {
            "safara_google_storage": {
                "enable_supabase_storage": "sí",
                "database_url": self.URL,
            }
        }
        self.assertTrue(is_enabled(secrets))
        self.assertEqual(SupabaseStorageConfig.from_secrets(secrets).database_url, self.URL)


if __name__ == "__main__":
    unittest.main()
