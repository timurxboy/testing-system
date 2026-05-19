from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from sqlalchemy import Integer, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.bot.models.bot_user import BotUser
from apps.bot.models.test_attempt import TestAttempt
from apps.testing.models.subject import Subject

PAGE_SIZE = 5


class StatsPeriod(StrEnum):
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


_PERIOD_DAYS: dict[StatsPeriod, int] = {
    StatsPeriod.WEEK: 7,
    StatsPeriod.MONTH: 30,
    StatsPeriod.YEAR: 365,
}


@dataclass(slots=True)
class SubjectStat:
    subject_name: str
    total: int
    correct: int


@dataclass(slots=True)
class UserStats:
    user_id: int
    telegram_id: int
    telegram_username: str | None
    full_name: str
    total: int
    correct: int
    by_subject: list[SubjectStat] = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        return (self.correct / self.total * 100) if self.total else 0.0


@dataclass(slots=True)
class StatsPage:
    period: StatsPeriod
    since: datetime
    offset: int
    page_size: int
    total_users: int
    total_attempts: int
    total_correct: int
    rows: list[UserStats]

    @property
    def page_index(self) -> int:
        return self.offset // self.page_size

    @property
    def total_pages(self) -> int:
        if self.total_users == 0:
            return 1
        return (self.total_users + self.page_size - 1) // self.page_size

    @property
    def has_prev(self) -> bool:
        return self.offset > 0

    @property
    def has_next(self) -> bool:
        return self.offset + len(self.rows) < self.total_users


class StatsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def since_for(period: StatsPeriod) -> datetime:
        return datetime.now(timezone.utc) - timedelta(days=_PERIOD_DAYS[period])

    async def fetch_page(
        self,
        period: StatsPeriod,
        *,
        offset: int = 0,
        page_size: int = PAGE_SIZE,
    ) -> StatsPage:
        since = self.since_for(period)
        correct_sum = func.coalesce(func.sum(TestAttempt.is_correct.cast(Integer)), 0)

        totals_result = await self.session.execute(
            select(
                func.count(TestAttempt.id),
                correct_sum,
                func.count(distinct(TestAttempt.bot_user_id)),
            ).where(TestAttempt.created_at >= since)
        )
        total_attempts, total_correct, total_users = totals_result.one()

        rows_result = await self.session.execute(
            select(
                BotUser.id,
                BotUser.telegram_id,
                BotUser.telegram_username,
                BotUser.first_name,
                BotUser.last_name,
                func.count(TestAttempt.id).label("total"),
                correct_sum.label("correct"),
            )
            .join(TestAttempt, TestAttempt.bot_user_id == BotUser.id)
            .where(TestAttempt.created_at >= since)
            .group_by(BotUser.id)
            .order_by(func.count(TestAttempt.id).desc(), BotUser.id)
            .offset(max(offset, 0))
            .limit(page_size)
        )

        rows: list[UserStats] = []
        user_id_to_row: dict[int, UserStats] = {}
        for user_id, tg_id, tg_username, first_name, last_name, total, correct in rows_result.all():
            full_name = (
                f"{first_name or ''} {last_name or ''}".strip()
                or tg_username
                or f"tg:{tg_id}"
            )
            row = UserStats(
                user_id=user_id,
                telegram_id=tg_id,
                telegram_username=tg_username,
                full_name=full_name,
                total=int(total),
                correct=int(correct),
            )
            rows.append(row)
            user_id_to_row[user_id] = row

        if rows:
            breakdown_result = await self.session.execute(
                select(
                    TestAttempt.bot_user_id,
                    Subject.name,
                    func.count(TestAttempt.id),
                    correct_sum,
                )
                .join(Subject, Subject.id == TestAttempt.subject_id)
                .where(
                    TestAttempt.created_at >= since,
                    TestAttempt.bot_user_id.in_(list(user_id_to_row.keys())),
                )
                .group_by(TestAttempt.bot_user_id, Subject.name)
                .order_by(TestAttempt.bot_user_id, func.count(TestAttempt.id).desc())
            )
            for user_id, subject_name, total, correct in breakdown_result.all():
                user_id_to_row[user_id].by_subject.append(
                    SubjectStat(
                        subject_name=subject_name,
                        total=int(total),
                        correct=int(correct),
                    )
                )

        return StatsPage(
            period=period,
            since=since,
            offset=max(offset, 0),
            page_size=page_size,
            total_users=int(total_users),
            total_attempts=int(total_attempts),
            total_correct=int(total_correct),
            rows=rows,
        )
