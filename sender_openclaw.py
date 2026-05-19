import logging

import requests

from config import OPENCLAW_SEND_URL

logger = logging.getLogger(__name__)


def send_wechat_message(message: str) -> bool:
    """
    Send a message through OpenClaw.

    TODO: If your OpenClaw endpoint uses a different field name, auth header,
    or receiver parameter, modify this function only.
    Current assumed API:
        POST OPENCLAW_SEND_URL
        JSON: {"message": "..."}
    """
    if not OPENCLAW_SEND_URL or "127.0.0.1:8000/send" in OPENCLAW_SEND_URL:
        logger.warning("OPENCLAW_SEND_URL 仍是默认占位地址，请在 config.py 中修改。")

    response = requests.post(
        OPENCLAW_SEND_URL,
        json={"message": message},
        timeout=30,
    )
    response.raise_for_status()
    logger.info("OpenClaw 推送成功。")
    return True
