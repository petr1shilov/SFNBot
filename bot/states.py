from aiogram.fsm.state import State, StatesGroup

class UserStates(StatesGroup):
    get_faq = State()
    get_top_k = State()
    get_all = State()