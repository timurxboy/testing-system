from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_for_student_id = State()


class Testing(StatesGroup):
    choosing_subject = State()
    answering = State()
