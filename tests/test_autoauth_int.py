import json
import os
from pprint import pprint
import shutil
import unittest

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
        creds_dict = json.loads(output.to_json())
        pprint(creds_dict)
        self.assertTrue(creds_dict.get('token'))
        self.assertEqual(sorted(creds_dict['scopes']), sorted(SCOPES))


class LoginTestCase(BaseAutoauthTestCase):
    def setUp(self):
        super().setUp()
        self.state_file = os.path.join(WORK_DIR, 'test-state.json')
        if os.path.exists(self.state_file):
            os.remove(self.state_file)

    def test_workflow(self):
        ao = module.Autoauth(self.secrets_file, scopes=SCOPES, headless=False)
        ao.state.file = self.state_file
        res = ao.acquire_credentials()
        self._check_output(res)
        self.assertTrue(os.path.exists(self.state_file))


class HeadfulTestCase(BaseAutoauthTestCase):
    def test_workflow(self):
        ao = module.Autoauth(self.secrets_file, scopes=SCOPES, headless=False)
        res = ao.acquire_credentials()
        self._check_output(res)


class HeadlessTestCase(BaseAutoauthTestCase):
    def test_workflow(self):
        ao = module.Autoauth(self.secrets_file, scopes=SCOPES, headless=True)
        res = ao.acquire_credentials()
        self._check_output(res)
