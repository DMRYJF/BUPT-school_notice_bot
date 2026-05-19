import logging
from pathlib import Path

from playwright.sync_api import Browser, Page, TimeoutError as PlaywrightTimeoutError

from config import (
    CAS_LOGIN_URL,
    NOTICE_LIST_URL,
    RUN_HEADLESS,
    SCHOOL_PASSWORD,
    SCHOOL_USERNAME,
    STATE_FILE,
)

logger = logging.getLogger(__name__)


def create_browser(playwright):
    return playwright.chromium.launch(headless=RUN_HEADLESS)


def _new_context(browser: Browser, use_state: bool = True):
    state_path = Path(STATE_FILE)
    if use_state and state_path.exists():
        logger.info("发现 auth_state.json，优先复用登录态。")
        return browser.new_context(storage_state=STATE_FILE)
    return browser.new_context()


def _visit_notice_with_state(browser: Browser):
    context = _new_context(browser, use_state=True)
    page = context.new_page()
    page.goto(NOTICE_LIST_URL, wait_until="networkidle", timeout=30000)
    if "authserver" not in page.url:
        logger.info("登录态有效，已进入通知列表页。")
        return context, page
    logger.info("登录态无效，CAS 重定向回登录页，准备重新登录。")
    context.close()
    return None, None


def _perform_login(browser: Browser):
    context = _new_context(browser, use_state=False)
    page = context.new_page()
    page.goto(CAS_LOGIN_URL, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(3000)

    # BUPT CAS uses an iframe for the actual login form
    frame = page.frame(name="loginIframe")
    if not frame:
        frame = page.frame(url=lambda u: "login-normal" in u)

    if frame:
        logger.info("检测到 iframe 登录表单，切换至密码登录 tab。")
        # Switch to password login tab
        pwd_tab = frame.locator('a:has-text("密码登录")')
        if pwd_tab.count() > 0:
            pwd_tab.click()
            page.wait_for_timeout(500)

        # Fill credentials inside iframe
        frame.fill("#username", SCHOOL_USERNAME, timeout=10000)
        frame.fill("#password", SCHOOL_PASSWORD, timeout=10000)
        frame.click('input[value="账号登录"]', timeout=10000)
    else:
        # Fallback: legacy non-iframe CAS login
        logger.info("未检测到 iframe，使用传统表单登录。")
        page.fill('input[name="username"]', SCHOOL_USERNAME, timeout=10000)
        page.fill('input[name="password"]', SCHOOL_PASSWORD, timeout=10000)
        page.click('input[type="submit"]', timeout=10000)

    page.wait_for_load_state("networkidle", timeout=30000)
    page.wait_for_timeout(3000)

    if "authserver" in page.url:
        context.close()
        raise RuntimeError("CAS 自动登录失败：仍停留在登录页，请检查账号密码是否正确。")

    context.storage_state(path=STATE_FILE)
    logger.info("CAS 登录成功，已保存 auth_state.json。")
    return context, page


def ensure_logged_in(browser: Browser):
    context, page = _visit_notice_with_state(browser)
    if context and page:
        return context, page
    return _perform_login(browser)
