import logging
from pathlib import Path

from playwright.sync_api import Browser, Page, TimeoutError as PlaywrightTimeoutError

from config import (
    CAS_KEYWORDS,
    CAS_LOGIN_URL,
    LOGIN_BUTTON_SELECTOR,
    NOTICE_LIST_URL,
    PASSWORD_SELECTOR,
    RUN_HEADLESS,
    SCHOOL_PASSWORD,
    SCHOOL_USERNAME,
    STATE_FILE,
    USERNAME_SELECTOR,
)

logger = logging.getLogger(__name__)


def create_browser(playwright):
    return playwright.chromium.launch(headless=RUN_HEADLESS)


def is_login_page(page: Page) -> bool:
    current_url = page.url.lower()
    if "cas" in current_url or "login" in current_url:
        return True

    try:
        text = page.locator("body").inner_text(timeout=3000)
    except Exception:
        text = page.content()

    return any(keyword.lower() in text.lower() for keyword in CAS_KEYWORDS)


def dump_login_debug(page: Page) -> None:
    html_head = page.content()[:1000]
    logger.error("登录失败调试信息：")
    logger.error("当前 URL: %s", page.url)
    logger.error("页面标题: %s", page.title())
    logger.error("HTML 前 1000 字:\n%s", html_head)
    logger.error(
        "请优先检查 config.py 中的 USERNAME_SELECTOR、PASSWORD_SELECTOR、LOGIN_BUTTON_SELECTOR。"
    )


def _new_context(browser: Browser, use_state: bool = True):
    state_path = Path(STATE_FILE)
    if use_state and state_path.exists():
        logger.info("发现 auth_state.json，优先复用登录态。")
        return browser.new_context(storage_state=STATE_FILE)
    return browser.new_context()


def _visit_notice_with_state(browser: Browser):
    context = _new_context(browser, use_state=True)
    page = context.new_page()
    page.goto(NOTICE_LIST_URL, wait_until="networkidle")
    if not is_login_page(page):
        logger.info("登录态有效，已进入通知列表页。")
        return context, page

    logger.info("登录态无效或已跳回 CAS 登录页，准备重新登录。")
    context.close()
    return None, None


def _perform_login(browser: Browser):
    context = _new_context(browser, use_state=False)
    page = context.new_page()
    page.goto(CAS_LOGIN_URL, wait_until="networkidle")

    try:
        page.fill(USERNAME_SELECTOR, SCHOOL_USERNAME, timeout=10000)
        page.fill(PASSWORD_SELECTOR, SCHOOL_PASSWORD, timeout=10000)
        page.click(LOGIN_BUTTON_SELECTOR, timeout=10000)
        page.wait_for_load_state("networkidle", timeout=20000)
    except PlaywrightTimeoutError:
        dump_login_debug(page)
        context.close()
        raise RuntimeError("CAS 登录元素定位失败，请修改 config.py 中的 selector。")

    page.goto(NOTICE_LIST_URL, wait_until="networkidle")
    if is_login_page(page):
        dump_login_debug(page)
        context.close()
        raise RuntimeError("CAS 自动登录失败：仍停留在登录页或被重定向回登录页。")

    context.storage_state(path=STATE_FILE)
    logger.info("CAS 登录成功，已保存新的 auth_state.json。")
    return context, page


def ensure_logged_in(browser: Browser):
    context, page = _visit_notice_with_state(browser)
    if context and page:
        return context, page
    return _perform_login(browser)
