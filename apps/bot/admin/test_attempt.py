from sqladmin import ModelView

from apps.bot.models.test_attempt import TestAttempt


class TestAttemptAdmin(ModelView, model=TestAttempt):
    name = "Test attempt"
    name_plural = "Test attempts"
    category = "Bot"
    icon = "fa-solid fa-clipboard-check"

    column_list = [
        TestAttempt.id,
        TestAttempt.bot_user,
        TestAttempt.subject,
        TestAttempt.question,
        TestAttempt.is_correct,
        TestAttempt.created_at,
    ]
    column_sortable_list = [TestAttempt.id, TestAttempt.is_correct, TestAttempt.created_at]

    can_create = False
    can_edit = False
    can_delete = True
