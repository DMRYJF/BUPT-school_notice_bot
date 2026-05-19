import logging
from datetime import date
from typing import Dict, List

from playwright.sync_api import Page

from config import NOTICE_LIST_LIMIT_WHEN_DATE_UNKNOWN, NOTICE_LIST_URL
from parser import is_today_or_unknown, parse_notice_detail, parse_notice_list

logger = logging.getLogger(__name__)


def crawl_today_notices(page: Page) -> List[Dict[str, str]]:
    logger.info("打开通知列表页：%s", NOTICE_LIST_URL)
    page.goto(NOTICE_LIST_URL, wait_until="networkidle")
    list_html = page.content()
    candidates = parse_notice_list(list_html)
    logger.info("列表页解析到候选通知 %s 条。", len(candidates))

    today = date.today().isoformat()
    dated_today = [item for item in candidates if item.get("publish_date") == today]

    if dated_today:
        detail_targets = dated_today
    else:
        detail_targets = candidates[:NOTICE_LIST_LIMIT_WHEN_DATE_UNKNOWN]
        logger.info(
            "列表页未提取到当天日期，回退抓取前 %s 条详情页。",
            len(detail_targets),
        )

    results = []
    for item in detail_targets:
        logger.info("抓取详情页：%s", item["title"])
        page.goto(item["url"], wait_until="networkidle")
        detail = parse_notice_detail(page.content())

        publish_date = item.get("publish_date")
        if publish_date == "unknown":
            publish_date = detail.get("publish_date", "unknown")

        notice = {
            "title": item["title"],
            "url": item["url"],
            "publish_date": publish_date or "unknown",
            "content": detail.get("content", ""),
        }

        if is_today_or_unknown(notice["publish_date"]):
            results.append(notice)

    logger.info("本次保留当天或 unknown 通知 %s 条。", len(results))
    return results
