import logging
import os

from playwright.sync_api import sync_playwright

from auth import create_browser, ensure_logged_in
from crawler import crawl_today_notices
from db import content_hash, init_db, insert_notice, mark_sent, update_summary
from sender_openclaw import send_wechat_message
from summarizer import summarize_notice
from config import LOG_DIR


def setup_logging() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, "bot.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def run_once() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)
    init_db()

    added_count = 0
    sent_count = 0

    with sync_playwright() as playwright:
        browser = create_browser(playwright)
        context = None
        try:
            context, page = ensure_logged_in(browser)
            notices = crawl_today_notices(page)

            for notice in notices:
                notice["content_hash"] = content_hash(notice.get("content", ""))
                notice_id = insert_notice(notice)
                if notice_id is None:
                    logger.info("跳过已存在通知：%s", notice["title"])
                    continue

                added_count += 1
                summary = summarize_notice(notice)
                update_summary(notice_id, summary)

                message = f"{summary}\n\n原文链接：{notice['url']}"
                send_wechat_message(message)
                mark_sent(notice_id)
                sent_count += 1

        finally:
            if context:
                context.close()
            browser.close()

    logger.info("本次运行完成：新增 %s 条，发送 %s 条。", added_count, sent_count)
    print(f"本次运行完成：新增 {added_count} 条，发送 {sent_count} 条。")


if __name__ == "__main__":
    run_once()
