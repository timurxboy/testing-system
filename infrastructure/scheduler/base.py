from typing import Callable, Any
from logging import Logger

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


class BaseScheduler:
    """
    Infrastructure scheduler based on APScheduler.
    """

    def __init__(self, logger: Logger):
        self.logger = logger
        self.scheduler = AsyncIOScheduler()

    def add_cron_job(
        self,
        *,
        job_id: str,
        func: Callable[..., Any],
        **cron_kwargs,
    ) -> None:
        trigger = CronTrigger(**cron_kwargs)

        self.scheduler.add_job(
            func=func,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
        )

        self.logger.info(msg=f"🕒 Job '{job_id}' scheduled")

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()
            self.logger.info(msg="🚀 Scheduler started")

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info(msg="🛑 Scheduler stopped")

    def list_jobs(self) -> list[dict[str, Any]]:
        return [
            {
                "id": job.id,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(object=job.trigger),
            }
            for job in self.scheduler.get_jobs()
        ]
