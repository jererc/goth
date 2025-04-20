import json
import logging
import os
import shutil
import unittest
from unittest.mock import patch

from goth import autoauth as module


WORK_DIR = os.path.join(os.path.expanduser('~'), '_tests', 'goth')
SECRETS_FILE = os.path.join(os.path.expanduser('~'), 'gcs-savegame.json')
SCOPES = [
    'https://www.googleapis.com/auth/contacts.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
]

module.logger.setLevel(logging.DEBUG)


class AutoauthTestCase(unittest.TestCase):
    def setUp(self):
        # if os.path.exists(WORK_DIR):
        #     shutil.rmtree(WORK_DIR)
        if not os.path.exists(WORK_DIR):
            os.makedirs(WORK_DIR)
        self.secrets_file = os.path.join(WORK_DIR, 'secrets.json')
        shutil.copy(SECRETS_FILE, self.secrets_file)

    def _check_output(self, output):
        self.assertTrue(output)
        creds_json = output.to_json()
        print(creds_json)
        creds_dict = json.loads(creds_json)
        self.assertTrue(creds_dict.get('token'))

    def test_workflow(self):
        # Interactive workflow
        with patch('os.path.expanduser', return_value=WORK_DIR):
            ao = module.Autoauth(self.secrets_file,
                scopes=SCOPES,
                headless=False,
            )
        res = ao.acquire_credentials()
        self._check_output(res)

        # Headless workflow
        with patch('os.path.expanduser', return_value=WORK_DIR):
            ao = module.Autoauth(self.secrets_file,
                scopes=SCOPES,
                headless=True,
            )
        res = ao.acquire_credentials()
        self._check_output(res)


class DebugTestCase(unittest.TestCase):
    def setUp(self):
        if not os.path.exists(WORK_DIR):
            os.makedirs(WORK_DIR)
        self.secrets_file = os.path.join(WORK_DIR, 'secrets.json')
        shutil.copy(SECRETS_FILE, self.secrets_file)

    def _check_output(self, output):
        self.assertTrue(output)
        creds_json = output.to_json()
        print(creds_json)
        creds_dict = json.loads(creds_json)
        self.assertTrue(creds_dict.get('token'))

    def test_workflow(self):
        with patch('os.path.expanduser', return_value=WORK_DIR):
            ao = module.Autoauth(self.secrets_file,
                scopes=SCOPES,
                headless=True,
            )
        res = ao.acquire_credentials()
        self._check_output(res)
