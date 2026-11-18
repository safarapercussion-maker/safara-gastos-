import base64
import unittest

from safara_google_drive_oauth import GoogleDriveOAuthConfig, create_state, verify_state


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

    def test_modified_state_is_rejected(self):
        state = create_state(self.config)
        self.assertFalse(verify_state(self.config, state[:-1] + "x"))


if __name__ == "__main__":
    unittest.main()
