"""Regression checks for refreshable sessions without storing passwords."""

import unittest

from safara_session_persistence import (
    SESSION_BRIDGE_JS,
    new_session_token,
    session_token_hash,
)
from safara_supabase_storage import SupabaseSafaraStorage


class FakeCursor:
    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.statements = []

    def execute(self, sql, params=None):
        self.statements.append((sql, params))

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None


def storage_with_cursor(cursor):
    storage = object.__new__(SupabaseSafaraStorage)
    storage._run = lambda callback: callback(cursor)
    return storage


class SessionPersistenceTests(unittest.TestCase):
    def test_tokens_are_random_and_invalid_values_are_rejected(self):
        first, second = new_session_token(), new_session_token()
        self.assertNotEqual(first, second)
        self.assertEqual(len(first), 43)
        self.assertEqual(len(session_token_hash(first)), 64)
        for invalid in ("", "plain-password", "x" * 500, "../" * 20, None):
            self.assertIsNone(session_token_hash(invalid))

    def test_browser_keeps_only_an_opaque_tab_token(self):
        self.assertIn("sessionStorage.setItem", SESSION_BRIDGE_JS)
        self.assertIn("sessionStorage.removeItem", SESSION_BRIDGE_JS)
        self.assertNotIn("localStorage", SESSION_BRIDGE_JS)
        self.assertNotIn("password", SESSION_BRIDGE_JS.lower())

    def test_login_restore_and_logout_use_a_revocable_database_row(self):
        digest = session_token_hash(new_session_token())
        create_cursor = FakeCursor([{"token_hash": digest}])
        storage = storage_with_cursor(create_cursor)
        self.assertTrue(storage.crear_sesion_navegador("Prueba", digest))
        self.assertEqual(create_cursor.statements[-1][1], (digest, "Prueba"))

        restore_cursor = FakeCursor([{"nombre": "Prueba"}])
        storage = storage_with_cursor(restore_cursor)
        self.assertEqual(storage.confirmar_sesion_navegador(digest), "Prueba")
        self.assertIn("u.activo", restore_cursor.statements[0][0])
        self.assertIn("password_hash_al_crear = u.password_hash", restore_cursor.statements[0][0])

        revoke_cursor = FakeCursor()
        storage = storage_with_cursor(revoke_cursor)
        storage.revocar_sesion_navegador(digest)
        self.assertEqual(revoke_cursor.statements[0][1], (digest,))


if __name__ == "__main__":
    unittest.main()
