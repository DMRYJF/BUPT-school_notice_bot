import re
from datetime import date, datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import PORTAL_BASE_URL


TITLE_KEYWORDS = ("通知", "公告", "关于", "公示")
DATE_PATTERNS = (
    r"20\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2}日?",
    r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日",
)


def normalize_url(url: str) -> str:
    return urljoin(PORTAL_BASE_URL, (url or "").strip())


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def parse_date(text: str) -> Optional[str]:
    text = text or ""
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text)
        if not match:
            continue
        raw = match.group(0)
        normalized = (
            raw.replace("年", "-")
            .replace("月", "-")
            .replace("日", "")
            .replace("/", "-")
            .replace(".", "-")
        )
        normalized = re.sub(r"\s+", "", normalized).strip("-")
        parts = normalized.split("-")
        if len(parts) >= 3:
            try:
                dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                return dt.date().isoformat()
            except ValueError:
                continue
    return None


def is_today_or_unknown(publish_date: str) -> bool:
    return publish_date == "unknown" or publish_date == date.today().isoformat()


def parse_notice_list(html: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    notices = []
    seen_urls = set()

    for link in soup.find_all("a"):
        title = _clean_text(link.get_text(" ", strip=True))
        href = link.get("href")
        if not title or not href:
            continue
        if not any(keyword in title for keyword in TITLE_KEYWORDS):
            continue

        url = normalize_url(href)
        if url in seen_urls:
            continue
        seen_urls.add(url)

        context_text = _clean_text(link.parent.get_text(" ", strip=True) if link.parent else title)
        publish_date = parse_date(context_text) or "unknown"
        notices.append(
            {
                "title": title,
                "url": url,
                "publish_date": publish_date,
            }
        )

    return notices


def parse_notice_detail(html: str) -> Dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    content_node = None
    for selector in ("article", ".article", ".content", ".main", "#content"):
        content_node = soup.select_one(selector)
        if content_node:
            break

    if content_node is None:
        content_node = soup.body or soup

    content = content_node.get_text("\n", strip=True)
    content = re.sub(r"\n{3,}", "\n\n", content).strip()
    publish_date = parse_date(content) or "unknown"

    return {
        "content": content,
        "publish_date": publish_date,
    }
