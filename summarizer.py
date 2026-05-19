import logging
from typing import Dict

import requests

from config import AI_API_KEY, AI_BASE_URL, AI_MODEL

logger = logging.getLogger(__name__)


SUMMARY_PROMPT = """你是大学通知助理。请阅读学校通知，生成适合微信推送的中文摘要。

要求：

1. 第一行给出通知标题。
2. 第二行给出一句话结论。
3. 提取时间、地点、对象、截止日期、需要做什么。
4. 如果通知与普通学生关系不大，标记“可能无需处理”。
5. 不要编造原文没有的信息。
6. 总长度不超过 250 字。
"""


def summarize_notice(notice: Dict[str, str]) -> str:
    if not AI_API_KEY or AI_API_KEY == "在这里填 AI API Key":
        logger.warning("AI_API_KEY 未配置，返回占位摘要。")
        return f"{notice['title']}\nAI_API_KEY 未配置，暂未生成摘要。"

    endpoint = AI_BASE_URL.rstrip("/") + "/chat/completions"
    payload = {
        "model": AI_MODEL,
        "messages": [
            {"role": "system", "content": SUMMARY_PROMPT},
            {
                "role": "user",
                "content": (
                    f"标题：{notice.get('title', '')}\n"
                    f"发布时间：{notice.get('publish_date', 'unknown')}\n"
                    f"链接：{notice.get('url', '')}\n\n"
                    f"正文：\n{notice.get('content', '')[:6000]}"
                ),
            },
        ],
        "temperature": 0.2,
    }

    response = requests.post(
        endpoint,
        headers={
            "Authorization": f"Bearer {AI_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()
