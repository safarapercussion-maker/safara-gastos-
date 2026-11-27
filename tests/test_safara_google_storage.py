import unittest
import json
from unittest.mock import Mock

from safara_google_storage import GoogleSafaraStorage, GoogleStorageConfig, StorageConfigurationError, is_enabled


class GoogleStorageConfigTests(unittest.TestCase):
  def test_recognises_explicit_enablement(self):
    self.assertTrue(is_enabled({"enable_google_sheets_sync": True}))
    self.assertTrue(is_enabled({"enable_google_sheets_sync": "sí"}))
    self.assertFalse(is_enabled({"enable_google_sheets_sync": False}))

  def test_uses_the_saved_google_configuration_when_no_extra_switch_exists(self):
    self.assertTrue(is_enabled({
        "safara_google_storage": {
            "spreadsheet_id": "1wywxlZ2Uju-EKIK9B7QJ-x1X2AFGS_qGf7HTDIHccvk",
            "receipts_folder_id": "1cv0RifxRqrkiB916A6gXnMuFrKSYWTK7",
        },
        "gcp_service_account": {"type": "service_account"},
    }))

  def test_accepts_complete_service_account_configuration(self):
    config = GoogleStorageConfig.from_secrets({
        "safara_google_storage": {
            "spreadsheet_id": "1wywxlZ2Uju-EKIK9B7QJ-x1X2AFGS_qGf7HTDIHccvk",
            "receipts_folder_id": "1cv0RifxRqrkiB916A6gXnMuFrKSYWTK7",
        },
        "gcp_service_account": {
            "type": "service_account",
            "project_id": "safarapercussion",
            "private_key": "not-a-real-key-used-only-for-validation",
            "client_email": "test@safarapercussion.iam.gserviceaccount.com",
            "token_uri": "https://oauth2.googleapis.com/token",
        },
    })
    self.assertEqual(config.spreadsheet_id, "1wywxlZ2Uju-EKIK9B7QJ-x1X2AFGS_qGf7HTDIHccvk")

  def test_rejects_missing_service_account_values(self):
    with self.assertRaises(StorageConfigurationError):
      GoogleStorageConfig.from_secrets({
          "safara_google_storage": {"spreadsheet_id": "short", "receipts_folder_id": "short"},
          "gcp_service_account": {},
      })

  def test_accepts_json_service_account_secret(self):
    service_account = {
        "type": "service_account",
        "project_id": "safarapercussion",
        "private_key": "not-a-real-key-used-only-for-validation",
        "client_email": "test@safarapercussion.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    config = GoogleStorageConfig.from_secrets({
        "safara_google_storage": {
            "spreadsheet_id": "1wywxlZ2Uju-EKIK9B7QJ-x1X2AFGS_qGf7HTDIHccvk",
            "receipts_folder_id": "1cv0RifxRqrkiB916A6gXnMuFrKSYWTK7",
        },
        "gcp_service_account_json": json.dumps(service_account),
    })
    self.assertEqual(config.service_account["client_email"], service_account["client_email"])

  def test_renewed_permission_reuses_writable_receipts_folder(self):
    drive = Mock()
    drive.files.return_value.get.return_value.execute.return_value = {
        "id": "A" * 25,
        "mimeType": "application/vnd.google-apps.folder",
        "trashed": False,
        "capabilities": {"canAddChildren": True},
    }
    storage = object.__new__(GoogleSafaraStorage)
    storage._folder_id = ""
    storage._drive_client = lambda: drive
    self.assertTrue(storage.reutilizar_carpeta_justificantes("A" * 25))
    self.assertEqual(storage._folder_id, "A" * 25)
    drive.files.return_value.get.assert_called_once()

  def test_renewed_permission_rejects_unwritable_folder(self):
    drive = Mock()
    drive.files.return_value.get.return_value.execute.return_value = {
        "mimeType": "application/vnd.google-apps.folder",
        "capabilities": {"canAddChildren": False},
    }
    storage = object.__new__(GoogleSafaraStorage)
    storage._folder_id = ""
    storage._drive_client = lambda: drive
    self.assertFalse(storage.reutilizar_carpeta_justificantes("A" * 25))
    self.assertEqual(storage._folder_id, "")


if __name__ == "__main__":
  unittest.main()
