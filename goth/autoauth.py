from contextlib import contextmanager
import logging
import os
import time

from google_auth_oauthlib.flow import InstalledAppFlow
from playwright.sync_api import sync_playwright, TimeoutError
from svcutils.notifier import notify, clear_notif

from goth import NAME, WORK_DIR


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
        return os.path.join(dirname, f'{os.path.splitext(basename)[0]}-state.json')

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

    def _save_debug_data(self, page, name):
        debug_dir = os.path.join(WORK_DIR, 'debug')
        os.makedirs(debug_dir, exist_ok=True)
        basename = f'{int(time.time())}-{name}'
        source_file = os.path.join(debug_dir, f'{basename}.html')
        with open(source_file, 'w', encoding='utf-8') as f:
            f.write(page.content())
        logger.warning(f'saved page content to {source_file}')
        if self.headless:
            screenshot_file = os.path.join(debug_dir, f'{basename}.png')
            page.screenshot(path=screenshot_file)
            logger.warning(f'saved page screenshot to {screenshot_file}')

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
                self._save_debug_data(page, 'click_failed')
            raise
        logger.debug(f'clicked on {selector}')

    def _continue(self, page, timeout=5000):
        self._click(page, 'xpath=//span[contains(text(), "Continue")]', timeout=timeout)

    def _auth(self, page):
        if page.locator('xpath=//input[@type="email"]').count():
            if self.headless:
                raise Exception('requires interactive login')
            logger.debug('waiting for user to login...')
            self._continue(page, timeout=120000)
            return

        if self.headless:
            self._click(page, 'xpath=(//div[@data-button-type])[1]/button', timeout=5000)
            try:
                challenge = page.wait_for_selector('xpath=//samp', timeout=5000)
            except TimeoutError:
                pass
            else:
                challenge_value = challenge.text_content()
                if not challenge_value:
                    self._save_debug_data(page, 'challenge_not_found')
                    raise Exception('challenge not found')
                logger.info(f'{challenge_value=}')
                notify(title='challenge', body=challenge_value, app_name=NAME, replace_key='challenge')
                time.sleep(60)
                clear_notif(app_name=NAME, replace_key='challenge')
                self._save_debug_data(page, 'challenge_solved')
        else:
            self._click(page, 'xpath=(//div[@data-authuser])[1]', timeout=5000)
            self._continue(page, timeout=5000)

    def _grant(self, page):
        if self.headless:
            # No need to select permissions
            self._click(page, 'xpath=//button[@id="submit_approve_access" and not(@disabled)]', timeout=5000)
        else:
            try:
                self._click(page, 'xpath=(//input[@type="checkbox"])[1]', click_delay=1000, debug=False)
            except TimeoutError:
                logger.warning('access probably already granted')
            self._continue(page, timeout=10000)

    def _fetch_code(self, auth_url):
        with self.playwright_context() as context:
            page = context.new_page()
            page.goto(auth_url)
            self._auth(page)
            self._grant(page)
            try:
                textarea = page.wait_for_selector('xpath=//textarea', timeout=5000)
            except TimeoutError:
                self._save_debug_data(page, 'code_not_found')
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
