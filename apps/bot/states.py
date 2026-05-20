from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_for_student_id = State()
    waiting_for_question_count = State()


class Settings(StatesGroup):
    choosing_question_count = State()


class Testing(StatesGroup):
    choosing_subject = State()
    answering = State()
