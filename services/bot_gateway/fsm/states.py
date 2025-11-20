from aiogram.fsm.state import State, StatesGroup


class RequestFormStates(StatesGroup):
    warehouse = State()
    category = State()
    subcategory = State()
    amount = State()
    comment = State()
    file = State()
    confirmation = State()
    rejection_comment = State()  # Состояние для ввода комментария при отклонении заявки

