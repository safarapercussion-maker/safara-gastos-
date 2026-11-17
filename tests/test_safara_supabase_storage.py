import unittest

from safara_supabase_storage import (
    SupabaseSafaraStorage,
    SupabaseStorageOperationError,
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


if __name__ == "__main__":
    unittest.main()
