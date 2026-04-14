from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.database import (
    get_products, get_product, add_product, delete_product,
    get_orders, get_order, complete_order, delete_order,
    clear_old_orders, get_orders_stats
)
from bot.keyboards import (
    get_admin_keyboard, get_catalog_keyboard,
    get_admin_product_actions_keyboard, get_admin_order_actions_keyboard,
    get_confirmation_keyboard, get_back_to_admin_keyboard,
    get_main_menu_keyboard, get_admin_add_product_confirmation_keyboard,
    get_admin_orders_keyboard
)
from bot.states import AdminProductStates, AdminOrderStates
from bot.utils.validators import validate_price
from bot.filters import AdminFilter
from bot.config import ADMIN_ID, ORDER_RETENTION_DAYS

router = Router()
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    stats = await get_orders_stats()
    
    text = f"""
🔐 <b>Админ-панель</b>

📊 <b>Статистика:</b>
• Товаров: {stats['total_products']}
• Активных заказов: {stats['pending_orders']}
• Выполненных заказов: {stats['completed_orders']}

Выберите действие:
"""
    await message.answer(text, reply_markup=get_admin_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: CallbackQuery):
    await callback.answer()
    stats = await get_orders_stats()
    
    text = f"""
🔐 <b>Админ-панель</b>

📊 <b>Статистика:</b>
• Товаров: {stats['total_products']}
• Активных заказов: {stats['pending_orders']}
• Выполненных заказов: {stats['completed_orders']}

Выберите действие:
"""
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode="HTML")


# === Add Product Flow ===

@router.callback_query(F.data == "admin_add_product")
async def start_add_product(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(AdminProductStates.entering_name)
    await callback.message.edit_text(
        "➕ <b>Добавление нового товара</b>\n\n"
        "Введите <b>название</b> товара:",
        parse_mode="HTML"
    )


@router.message(AdminProductStates.entering_name)
async def process_product_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("❌ Название слишком короткое. Попробуйте снова:")
        return
    
    await state.update_data(name=name)
    await state.set_state(AdminProductStates.entering_description)
    await message.answer(
        f"✅ Название: {name}\n\n"
        f"Теперь введите <b>описание</b> товара:",
        parse_mode="HTML"
    )


@router.message(AdminProductStates.entering_description)
async def process_product_description(message: Message, state: FSMContext):
    description = message.text.strip()
    if len(description) < 10:
        await message.answer("❌ Описание слишком короткое. Попробуйте снова:")
        return
    
    await state.update_data(description=description)
    await state.set_state(AdminProductStates.entering_price)
    await message.answer(
        f"✅ Описание добавлено\n\n"
        f"Теперь введите <b>цену</b> товара (в рублях):",
        parse_mode="HTML"
    )


@router.message(AdminProductStates.entering_price)
async def process_product_price(message: Message, state: FSMContext):
    is_valid, price = validate_price(message.text)
    
    if not is_valid:
        await message.answer(
            "❌ Некорректная цена. Пожалуйста, введите положительное число:\n"
            "(например: 1500 или 1500.50)"
        )
        return
    
    await state.update_data(price=price)
    await state.set_state(AdminProductStates.entering_image)
    await message.answer(
        f"✅ Цена: {price}₽\n\n"
        f"Отправьте <b>фото</b> товара или введите <b>URL изображения</b>.\n"
        f"Если фото не нужно, отправьте «-»:",
        parse_mode="HTML"
    )


@router.message(AdminProductStates.entering_image, F.photo)
async def process_product_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    image_url = photo.file_id
    
    await state.update_data(image_url=image_url)
    await show_product_confirmation(message, state)


@router.message(AdminProductStates.entering_image)
async def process_product_image_url(message: Message, state: FSMContext):
    text = message.text.strip()
    image_url = None if text == "-" else text
    
    await state.update_data(image_url=image_url)
    await show_product_confirmation(message, state)


async def show_product_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    
    text = f"""
📋 <b>Проверьте данные товара:</b>

<b>Название:</b> {data['name']}
<b>Описание:</b> {data['description']}
<b>Цена:</b> {data['price']}₽
<b>Изображение:</b> {'✅ Есть' if data.get('image_url') else '❌ Нет'}

Всё верно?
"""
    await state.set_state(AdminProductStates.confirming)
    await message.answer(text, reply_markup=get_admin_add_product_confirmation_keyboard(), parse_mode="HTML")


@router.callback_query(AdminProductStates.confirming, F.data == "confirm_add_product")
async def confirm_add_product(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    
    product_id = await add_product(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        image_url=data.get('image_url')
    )
    
    await state.clear()
    await callback.message.edit_text(
        f"✅ Товар <b>#{product_id}</b> успешно добавлен!",
        reply_markup=get_back_to_admin_keyboard(),
        parse_mode="HTML"
    )


# === List Products ===

@router.callback_query(F.data == "admin_list_products")
async def list_products(callback: CallbackQuery):
    await callback.answer()
    products = await get_products()
    
    if not products:
        text = "📭 Товаров пока нет."
        kb = get_back_to_admin_keyboard()
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=kb)
        else:
            await callback.message.edit_text(text, reply_markup=kb)
        return
    
    text = "📋 <b>Список товаров:</b>\n\n"
    for product in products:
        text += f"• <b>{product['name']}</b> — {product['price']}₽\n"
    
    kb = get_catalog_keyboard(products)
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("view_product:"))
async def admin_view_product(callback: CallbackQuery):
    await callback.answer()
    product_id = int(callback.data.split(":")[1])
    product = await get_product(product_id)
    
    if not product:
        await callback.message.edit_text("❌ Товар не найден")
        return
    
    text = f"""
<b>{product['name']}</b>
ID: {product['id']}

{product['description']}

💰 <b>Цена:</b> {product['price']}₽
"""
    
    if product.get('image_url'):
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=product['image_url'],
            caption=text,
            reply_markup=get_admin_product_actions_keyboard(product_id),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_product_actions_keyboard(product_id),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("admin_delete_product:"))
async def confirm_delete_product(callback: CallbackQuery):
    await callback.answer()
    product_id = int(callback.data.split(":")[1])
    product = await get_product(product_id)
    
    if not product:
        await callback.message.edit_text("❌ Товар не найден")
        return
    
    text = (f"⚠️ <b>Удалить товар?</b>\n\n"
            f"<b>{product['name']}</b>\n"
            f"Это действие нельзя отменить!")
    kb = get_confirmation_keyboard("delete_product", product_id)
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("confirm_delete_product:"))
async def delete_product_confirmed(callback: CallbackQuery):
    await callback.answer()
    product_id = int(callback.data.split(":")[1])
    
    success = await delete_product(product_id)
    
    if success:
        await callback.message.edit_text(
            f"✅ Товар #{product_id} удалён",
            reply_markup=get_back_to_admin_keyboard()
        )
    else:
        await callback.message.edit_text(
            "❌ Не удалось удалить товар",
            reply_markup=get_back_to_admin_keyboard()
        )


# === List Orders ===

@router.callback_query(F.data == "admin_list_orders")
async def list_orders(callback: CallbackQuery):
    await callback.answer()
    orders = await get_orders()
    
    if not orders:
        await callback.message.edit_text(
            "📭 Заказов пока нет.",
            reply_markup=get_back_to_admin_keyboard()
        )
        return
    
    text = "📦 <b>Последние заказы:</b>\n\n"
    text += "Нажмите на кнопку ниже, чтобы увидеть детали заказа:"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_orders_keyboard(orders),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin_view_order:"))
async def admin_view_order(callback: CallbackQuery):
    await callback.answer()
    order_id = int(callback.data.split(":")[1])
    order = await get_order(order_id)
    
    if not order:
        await callback.message.edit_text("❌ Заказ не найден")
        return
    
    status_emoji = "⏳" if order['status'] == 'pending' else "✅"
    date_str = order['created_at'][:16] if order['created_at'] else "неизвестно"
    
    text = f"""
{status_emoji} <b>Заказ #{order['id']}</b>
📅 Дата: {date_str}
💰 Сумма: {order['total_amount']}₽
📊 Статус: {'В ожидании' if order['status'] == 'pending' else 'Выполнен'}

🛒 <b>Товар:</b> {order['product_info']}

👤 <b>Клиент:</b> {order['user_name']}
📞 <b>Телефон:</b> {order['phone']}
📍 <b>Адрес:</b> {order['address']}

🆔 User ID: {order['user_id']}
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_order_actions_keyboard(order_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin_complete_order:"))
async def complete_order_handler(callback: CallbackQuery):
    await callback.answer()
    order_id = int(callback.data.split(":")[1])
    
    success = await complete_order(order_id)
    
    if success:
        await callback.message.edit_text(
            f"✅ Заказ #{order_id} отмечен как выполненный",
            reply_markup=get_back_to_admin_keyboard()
        )
    else:
        await callback.message.edit_text(
            "❌ Не удалось обновить статус заказа",
            reply_markup=get_back_to_admin_keyboard()
        )


@router.callback_query(F.data.startswith("admin_delete_order:"))
async def confirm_delete_order(callback: CallbackQuery):
    await callback.answer()
    order_id = int(callback.data.split(":")[1])
    order = await get_order(order_id)
    
    if not order:
        await callback.message.edit_text("❌ Заказ не найден")
        return
    
    await callback.message.edit_text(
        f"⚠️ <b>Удалить заказ?</b>\n\n"
        f"Заказ #{order_id} от {order['user_name']}\n"
        f"Сумма: {order['total_amount']}₽\n\n"
        f"Это действие нельзя отменить!",
        reply_markup=get_confirmation_keyboard("delete_order", order_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("confirm_delete_order:"))
async def delete_order_confirmed(callback: CallbackQuery):
    await callback.answer()
    order_id = int(callback.data.split(":")[1])
    
    success = await delete_order(order_id)
    
    if success:
        await callback.message.edit_text(
            f"✅ Заказ #{order_id} удалён",
            reply_markup=get_back_to_admin_keyboard()
        )
    else:
        await callback.message.edit_text(
            "❌ Не удалось удалить заказ",
            reply_markup=get_back_to_admin_keyboard()
        )


@router.callback_query(F.data == "admin_clear_old_orders")
async def clear_old_orders_handler(callback: CallbackQuery):
    await callback.answer()
    
    deleted_count = await clear_old_orders(ORDER_RETENTION_DAYS)
    
    if deleted_count > 0:
        await callback.message.edit_text(
            f"🗑 Удалено {deleted_count} старых заказов\n"
            f"(старше {ORDER_RETENTION_DAYS} дней)",
            reply_markup=get_back_to_admin_keyboard()
        )
    else:
        await callback.message.edit_text(
            "📭 Нет старых заказов для удаления",
            reply_markup=get_back_to_admin_keyboard()
        )


@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Действие отменено")
    await state.clear()
    await show_admin_panel(callback)
