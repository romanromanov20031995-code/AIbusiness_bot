from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="📋 Каталог"), KeyboardButton(text="🛒 Мои заказы")],
        [KeyboardButton(text="❓ FAQ"), KeyboardButton(text="📞 Контакты")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_catalog_keyboard(products: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.row(
            InlineKeyboardButton(
                text=f"{product['name']} - {product['price']}₽",
                callback_data=f"view_product:{product['id']}"
            )
        )
    builder.row(InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu"))
    return builder.as_markup()


def get_product_detail_keyboard(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🛒 Купить", callback_data=f"buy_product:{product_id}"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_catalog")
    )
    return builder.as_markup()


def get_order_confirmation_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_order"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order")
    )
    return builder.as_markup()


def get_faq_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📦 Как сделать заказ?", callback_data="faq_order"))
    builder.row(InlineKeyboardButton(text="💳 Способы оплаты", callback_data="faq_payment"))
    builder.row(InlineKeyboardButton(text="🚚 Доставка", callback_data="faq_delivery"))
    builder.row(InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu"))
    return builder.as_markup()


def get_admin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product"),
        InlineKeyboardButton(text="📋 Список товаров", callback_data="admin_list_products")
    )
    builder.row(
        InlineKeyboardButton(text="📦 Все заказы", callback_data="admin_list_orders"),
        InlineKeyboardButton(text="🗑 Очистить старые заказы", callback_data="admin_clear_old_orders")
    )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu"))
    return builder.as_markup()


def get_admin_product_actions_keyboard(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"admin_edit_product:{product_id}"),
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_delete_product:{product_id}")
    )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_list_products"))
    return builder.as_markup()


def get_admin_order_actions_keyboard(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Выполнен", callback_data=f"admin_complete_order:{order_id}"),
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_delete_order:{order_id}")
    )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_list_orders"))
    return builder.as_markup()


def get_confirmation_keyboard(action: str, item_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да, подтвердить", callback_data=f"confirm_{action}:{item_id}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")
    )
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order"))
    return builder.as_markup()


def get_back_to_admin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 В админ-панель", callback_data="admin_panel"))
    return builder.as_markup()


def get_admin_add_product_confirmation_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Сохранить", callback_data="confirm_add_product"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="admin_panel")
    )
    return builder.as_markup()


def get_admin_orders_keyboard(orders: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for order in orders[:10]:  # Limit to 10 for display
        status_emoji = "⏳" if order['status'] == 'pending' else "✅"
        builder.row(
            InlineKeyboardButton(
                text=f"{status_emoji} Заказ #{order['id']} - {order['total_amount']}₽",
                callback_data=f"admin_view_order:{order['id']}"
            )
        )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel"))
    return builder.as_markup()
