import logging
import os
import sys
from datetime import date

from playwright.sync_api import sync_playwright

from auth import create_browser, ensure_logged_in
from config import LOG_DIR
from crawler import crawl_today_notices
from db import (
    content_hash,
    get_unsent_notices,
    init_db,
    insert_notice,
    mark_sent,
    update_summary,
)
from summarizer import summarize_notice


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def setup_logging() -> None:
    configure_stdio()
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, "bot.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stderr),
        ],
        force=True,
    )


def _row_to_notice(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "url": row["url"],
        "publish_date": row["publish_date"],
        "content": row["content"],
        "summary": row["summary"],
    }


def _build_digest(notices) -> str:
    today = date.today().isoformat()
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][
        date.today().weekday()
    ]
    parts = [f"北邮通知日报 | {today} {weekday}", f"共 {len(notices)} 条"]

    for index, notice in enumerate(notices, 1):
        summary = notice.get("summary") or f"{notice['title']}\n摘要暂未生成。"
        parts.append(
            "\n".join(
                [
                    "",
                    f"{index}. {summary}",
                    f"原文链接：{notice['url']}",
                ]
            )
        )

    return "\n".join(parts).strip()


def build_pending_digest(logger: logging.Logger) -> str:
    notices = []
    for row in get_unsent_notices():
        notice = _row_to_notice(row)
        if not notice.get("summary"):
            logger.info("生成待输出通知摘要：%s", notice["title"])
            summary = summarize_notice(notice)
            update_summary(notice["id"], summary)
            notice["summary"] = summary
        notices.append(notice)

    if not notices:
        logger.info("本次没有待输出的新通知。")
        return "今日暂无新通知。"

    digest = _build_digest(notices)

    for notice in notices:
        mark_sent(notice["id"])

    logger.info("已输出 %s 条通知给 OpenClaw。", len(notices))
    return digest


def run_once() -> str:
    setup_logging()
    logger = logging.getLogger(__name__)
    init_db()

    added_count = 0

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

        finally:
            if context:
                context.close()
            browser.close()

    digest = build_pending_digest(logger)
    logger.info("本次运行完成：新增 %s 条。", added_count)
    return digest


if __name__ == "__main__":
    print(run_once())
