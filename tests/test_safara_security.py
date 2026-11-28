import unittest

from safara_security import (
    generate_invitation_code,
    hash_invitation_code,
    hash_password,
    normalize_display_name,
    validate_display_name,
    validate_password,
    verify_bootstrap_token,
    verify_invitation_code,
    verify_password,
    validate_receipt_upload,
)


class SafaraSecurityTests(unittest.TestCase):

  def test_password_is_hashed_and_verifiable(self):
    salt, password_hash = hash_password("SafaraPrueba2026")
    self.assertNotEqual(password_hash, "SafaraPrueba2026")
    self.assertTrue(verify_password("SafaraPrueba2026", salt, password_hash))
    self.assertFalse(verify_password("SafaraPrueba2027", salt, password_hash))

  def test_password_policy_rejects_short_passwords(self):
    self.assertIsNotNone(validate_password("Corta1"))
    self.assertIsNone(validate_password("ContrasenaLarga1"))

  def test_bootstrap_requires_real_configured_secret(self):
    token = "a" * 32
    self.assertTrue(verify_bootstrap_token(token, token))
    self.assertFalse(verify_bootstrap_token(token, ""))
    self.assertFalse(verify_bootstrap_token("otro", token))

  def test_bootstrap_accepts_unicode_secret(self):
    token = "Tambor-Iruña-2026-Ensayo-Fuego-Ámbar"
    self.assertTrue(verify_bootstrap_token(token, token))

  def test_name_validation_and_normalization(self):
    self.assertEqual(normalize_display_name("  Ana   Pérez "), "Ana Pérez")
    self.assertIsNone(validate_display_name("Ana Pérez"))
    self.assertIsNotNone(validate_display_name("<script>"))

  def test_invitation_is_random_and_verifiable(self):
    code = generate_invitation_code()
    self.assertGreaterEqual(len(code), 20)
    self.assertTrue(verify_invitation_code(code, hash_invitation_code(code)))
    self.assertFalse(verify_invitation_code("otro", hash_invitation_code(code)))

  def test_receipt_rejects_bad_content_and_large_files(self):
    self.assertEqual(
        validate_receipt_upload("ticket.pdf", 5, b"%PDF-")[0], "pdf"
    )
    self.assertIsNotNone(
        validate_receipt_upload("ticket.pdf", 5, b"texto")[1]
    )
    self.assertIsNotNone(
        validate_receipt_upload("ticket.jpg", 11 * 1024 * 1024, b"\xff\xd8\xff")[1]
    )


if __name__ == "__main__":
  unittest.main()
