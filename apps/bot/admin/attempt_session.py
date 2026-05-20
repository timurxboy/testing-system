from sqladmin import ModelView

from apps.bot.models.attempt_session import AttemptSession


class AttemptSessionAdmin(ModelView, model=AttemptSession):
    name = "Test urinish"
    name_plural = "Test urinishlar"
    category = "Bot"
    icon = "fa-solid fa-hourglass-half"

    column_list = [
        AttemptSession.id,
        AttemptSession.bot_user,
        AttemptSession.subject,
        AttemptSession.round_number,
        AttemptSession.attempt_number,
        AttemptSession.status,
        AttemptSession.current_index,
        AttemptSession.correct_count,
        AttemptSession.started_at,
        AttemptSession.ended_at,
    ]
    column_sortable_list = [
        AttemptSession.id,
        AttemptSession.status,
        AttemptSession.attempt_number,
        AttemptSession.round_number,
        AttemptSession.started_at,
        AttemptSession.ended_at,
    ]
    column_labels = {
        "id": "ID",
        "bot_user": "Foydalanuvchi",
        "subject": "Fan",
        "round_number": "Aylana #",
        "attempt_number": "Urinish #",
        "status": "Holat",
        "current_index": "Joriy savol",
        "correct_count": "To'g'ri",
        "question_ids": "Savol IDlari",
        "started_at": "Boshlangan",
        "ended_at": "Tugatilgan",
    }

    can_create = False
    can_edit = False
    can_delete = True
