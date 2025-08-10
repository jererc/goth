import logging
import os
import time

from google_auth_oauthlib.flow import InstalledAppFlow
from playwright.sync_api import TimeoutError
from webutils.browser import State, playwright_context, save_page


logger = logging.getLogger(__name__)
logging.getLogger('asyncio').setLevel(logging.INFO)


class Autoauth:
    def __init__(self, client_secrets_file, scopes, headless=True):
        self.client_secrets_file = client_secrets_file
        self.scopes = scopes
        self.headless = headless
        self.state = State(f'{os.path.splitext(self.client_secrets_file)[0]}-state.json')
        self.debug_dir = os.path.join(os.path.dirname(self.client_secrets_file), 'debug')

    def _save_page(self, page, name):
        save_page(page, self.debug_dir, name)

    def _click(self, page, selector, timeout=10000, click_delay=500,
               raise_if_not_found=True, debug=True):
        try:
            res = page.wait_for_selector(selector, timeout=timeout)
            time.sleep(click_delay / 1000)
            res.click()
        except TimeoutError:
            logger.debug(f'{selector} not found')
            if not raise_if_not_found:
                return
            if debug:
                self._save_page(page, 'click_failed')
            raise
        logger.debug(f'clicked on {selector}')

    def _continue(self, page, timeout=5000):
        self._click(page, 'xpath=//span[contains(text(), "Continue")]', timeout=timeout)

    def _grant_permissions(self, page):
        if page.locator('xpath=//input[@type="email"]').count():
            if self.headless:
                raise Exception('requires interactive login')
            logger.debug('waiting for user to login...')
            self._continue(page, timeout=120000)
        else:
            self._click(page, 'xpath=(//div[@data-authuser])[1]', timeout=5000)
            self._continue(page, timeout=5000)
        try:
            self._click(page, 'xpath=(//input[@type="checkbox"])[1]', click_delay=1000, debug=False)
        except TimeoutError:
            logger.warning('access probably already granted')
        self._continue(page, timeout=10000)

    def _fetch_code(self, auth_url):
        with playwright_context(self.state, self.headless, stealth=self.headless) as context:
            page = context.new_page()
            page.goto(auth_url)
            self._grant_permissions(page)
            try:
                textarea = page.wait_for_selector('xpath=//textarea', timeout=5000)
            except TimeoutError:
                self._save_page(page, 'code_not_found')
                raise
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
