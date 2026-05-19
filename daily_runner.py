import json
import sys
from datetime import date, datetime, time
from pathlib import Path

from main import run_once


STATE_PATH = Path(__file__).resolve().parent / "daily_runner_state.json"
NOON = time(12, 0)


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def _load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_state(state: dict) -> None:
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def should_run_now(now: datetime) -> bool:
    if now.time() < NOON:
        return False

    state = _load_state()
    return state.get("last_run_date") != date.today().isoformat()


def main() -> None:
    configure_stdio()
    quiet_skip = "--quiet-skip" in sys.argv
    now = datetime.now()
    if not should_run_now(now):
        if not quiet_skip:
            print("今日 12:00 日报已执行，或当前尚未到 12:00。")
        return

    digest = run_once()
    _save_state(
        {
            "last_run_date": date.today().isoformat(),
            "last_run_at": now.isoformat(timespec="seconds"),
        }
    )
    print(digest)


if __name__ == "__main__":
    main()
