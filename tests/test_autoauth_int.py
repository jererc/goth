import json
import logging
import os
import shutil
import unittest
from unittest.mock import patch

from tests import WORK_DIR
from goth import autoauth as module


SECRETS_FILE = os.path.expanduser('~/gcs-savegame.json')
SCOPES = [
    'https://www.googleapis.com/auth/contacts.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
]


class BaseAutoauthTestCase(unittest.TestCase):
    """
    https://myaccount.google.com/connections
    """
    def setUp(self):
        os.makedirs(WORK_DIR, exist_ok=True)
        self.secrets_file = os.path.join(WORK_DIR, 'secrets.json')
        shutil.copy(SECRETS_FILE, self.secrets_file)

    def _check_output(self, output):
        self.assertTrue(output)
        creds_json = output.to_json()
        print(creds_json)
        creds_dict = json.loads(creds_json)
        self.assertTrue(creds_dict.get('token'))


class HeadfulTestCase(BaseAutoauthTestCase):
    def test_workflow(self):
        with patch('os.path.expanduser', return_value=WORK_DIR):
            ao = module.Autoauth(self.secrets_file, scopes=SCOPES, headless=False)
        res = ao.acquire_credentials()
        self._check_output(res)


class HeadlessTestCase(BaseAutoauthTestCase):
    def test_workflow(self):
        with patch('os.path.expanduser', return_value=WORK_DIR):
            ao = module.Autoauth(self.secrets_file, scopes=SCOPES, headless=True)
        res = ao.acquire_credentials()
        self._check_output(res)
