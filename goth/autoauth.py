from contextlib import contextmanager
import logging
import os

from google_auth_oauthlib.flow import InstalledAppFlow
from playwright.sync_api import sync_playwright


logger = logging.getLogger(__name__)
logging.getLogger('asyncio').setLevel(logging.INFO)


class Autoauth:
    def __init__(self, client_secrets_file, scopes, headless=True):
        self.client_secrets_file = client_secrets_file
        self.scopes = scopes
        self.headless = headless
        self.state_file = self._get_state_file()

    def _get_state_file(self):
        dirname, basename = os.path.split(self.client_secrets_file)
        name, ext = os.path.splitext(basename)
        return os.path.join(dirname, f'{name}-state.json')

    @contextmanager
    def playwright_context(self):
        with sync_playwright() as p:
            context = None
            try:
                browser = p.chromium.launch(
                    headless=self.headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                    ],
                )
                context = browser.new_context(storage_state=self.state_file
                    if os.path.exists(self.state_file) else None)
                yield context
            finally:
                if context:
                    context.storage_state(path=self.state_file)
                    context.close()

    def _click(self, page, selector, timeout=10000):
        page.wait_for_selector(selector, timeout=timeout).click()
        logger.debug(f'clicked on {selector}')

    def _interactive_workflow(self, page, timeout=120000):
        # self._click(page,
        #     'xpath=//div[@data-authuser="0"]')
        self._click(page,
            'xpath=//span[contains(text(), "Continue")]',
            timeout=timeout)
        self._click(page,
            'xpath=//input[@type="checkbox" and @aria-label="Select all"]')
        self._click(page,
            'xpath=//span[contains(text(), "Continue")]')

    def _headless_worklow(self, page):
        self._click(page,
            'xpath=//button[@id="choose-account-0"]')
        self._click(page,
            'xpath=//button[@id="submit_approve_access" and not(@disabled)]')

    def _fetch_code(self, auth_url):
        with self.playwright_context() as context:
            page = context.new_page()
            page.goto(auth_url)
            if page.locator('xpath=//input[@type="email"]').count():
                if self.headless:
                    raise Exception('requires interactive login')
                self._interactive_workflow(page)
            else:
                self._headless_worklow(page)
            textarea = page.wait_for_selector('xpath=//textarea', timeout=5000)
            return textarea.text_content()

    def acquire_credentials(self):
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secrets_file=self.client_secrets_file,
            scopes=self.scopes,
            redirect_uri='urn:ietf:wg:oauth:2.0:oob',
        )
        auth_url, _ = flow.authorization_url(prompt='consent')
        logger.debug(f'auth url: {auth_url}')
        code = self._fetch_code(auth_url)
        flow.fetch_token(code=code)
        return flow.credentials
