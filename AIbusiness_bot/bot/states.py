from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    selecting_product = State()
    entering_name = State()
    entering_phone = State()
    entering_address = State()
    confirming_order = State()


class AdminProductStates(StatesGroup):
    entering_name = State()
    entering_description = State()
    entering_price = State()
    entering_image = State()
    confirming = State()


class AdminOrderStates(StatesGroup):
    selecting_order = State()
    confirming_delete = State()
