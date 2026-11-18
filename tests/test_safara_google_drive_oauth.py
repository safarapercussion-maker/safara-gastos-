import base64
import unittest

from safara_google_drive_oauth import (
    GoogleDriveOAuthConfig,
    create_state,
    returning_user_from_state,
    verify_state,
)


class GoogleDriveOAuthStateTests(unittest.TestCase):
    def setUp(self):
        self.config = GoogleDriveOAuthConfig(
            client_id="test-client",
            client_secret="test-secret",
            redirect_uri="https://example.test/",
            encryption_key=base64.urlsafe_b64encode(b"s" * 32).decode("ascii"),
        )

    def test_signed_state_is_accepted(self):
        self.assertTrue(verify_state(self.config, create_state(self.config)))

    def test_uses_the_current_google_authorization_endpoint(self):
        self.assertEqual(
            self.config.client_config()["web"]["auth_uri"],
            "https://accounts.google.com/o/oauth2/v2/auth",
        )

    def test_modified_state_is_rejected(self):
        state = create_state(self.config)
        self.assertFalse(verify_state(self.config, state[:-1] + "x"))

    def test_returning_user_is_encrypted_and_recoverable(self):
        state = create_state(self.config, "Administración Prueba")
        self.assertNotIn("Administración", state)
        self.assertEqual(
            returning_user_from_state(self.config, state), "Administración Prueba"
        )

    def test_returning_user_is_not_recovered_from_tampered_state(self):
        state = create_state(self.config, "Administración Prueba")
        self.assertIsNone(
            returning_user_from_state(self.config, state[:-1] + "x")
        )


if __name__ == "__main__":
    unittest.main()
