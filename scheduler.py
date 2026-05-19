import logging
import signal
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from main import run_once, setup_logging


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
    for hour, minute in ((8, 30), (12, 30), (18, 30)):
        scheduler.add_job(
            run_once,
            CronTrigger(hour=hour, minute=minute),
            id=f"school_notice_bot_{hour}_{minute}",
            replace_existing=True,
            max_instances=1,
        )

    scheduler.start()
    logger.info("定时任务已启动：每天 08:30、12:30、18:30 运行。")
    print("定时任务已启动：每天 08:30、12:30、18:30 运行。按 Ctrl+C 退出。")

    stop = False

    def handle_stop(signum, frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGTERM, handle_stop)

    while not stop:
        time.sleep(1)

    scheduler.shutdown()
    logger.info("定时任务已停止。")


if __name__ == "__main__":
    main()
