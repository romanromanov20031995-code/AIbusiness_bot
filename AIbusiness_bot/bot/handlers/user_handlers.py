from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from bot.database import get_products, get_product, add_order
from bot.keyboards import (
    get_main_menu_keyboard,
    get_catalog_keyboard,
    get_product_detail_keyboard,
    get_faq_keyboard,
    get_order_confirmation_keyboard,
    get_cancel_keyboard,
    get_back_to_admin_keyboard
)
from bot.states import OrderStates
from bot.utils.validators import validate_phone_number, clean_phone_number
from bot.config import ADMIN_ID

router = Router()


FAQ_ANSWERS = {
    "faq_order": """
📦 <b>Как сделать заказ?</b>

1. Нажмите «📋 Каталог» в главном меню
2. Выберите товар и нажмите «🛒 Купить»
3. Введите ваше имя
4. Введите номер телефона
5. Укажите адрес доставки
6. Подтвердите заказ

После этого с вами свяжется менеджер для подтверждения!
""",
    "faq_payment": """
💳 <b>Способы оплаты</b>

• Наличными курьеру
• Перевод на карту (Сбербанк, Тинькофф)
• Онлайн-оплата через сайт

Оплата производится после подтверждения заказа менеджером.
""",
    "faq_delivery": """
🚚 <b>Доставка</b>

• Курьерская доставка по городу — 300₽
• Самовывоз (бесплатно)
• Доставка в регионы — по тарифам СДЭК/Почты России

Срок доставки: 1-3 рабочих дня.
""",
}


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    
    welcome_text = f"""
👋 Добро пожаловать, {message.from_user.first_name}!

Я бот для оформления заказов. Здесь вы можете:
• Просмотреть каталог товаров
• Оформить заказ
• Получить ответы на частые вопросы

Выберите нужный раздел в меню ниже 👇
"""
    
    if user_id == ADMIN_ID:
        welcome_text += "\n\n🔐 <b>У вас есть доступ к админ-панели.</b>\nИспользуйте команду /admin"
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "📋 Каталог")
async def show_catalog(message: Message, state: FSMContext):
    await state.clear()
    products = await get_products()
    
    if not products:
        await message.answer(
            "😔 Пока нет товаров в каталоге. Загляните позже!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    await message.answer(
        "📋 <b>Наш каталог товаров:</b>\n\nВыберите товар для подробной информации:",
        reply_markup=get_catalog_keyboard(products),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    products = await get_products()
    
    if not products:
        text = "😔 Пока нет товаров в каталоге. Загляните позже!"
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(text)
        else:
            await callback.message.edit_text(text)
        return
    
    text = "📋 <b>Наш каталог товаров:</b>\n\nВыберите товар для подробной информации:"
    kb = get_catalog_keyboard(products)
    
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("view_product:"))
async def view_product(callback: CallbackQuery):
    await callback.answer()
    product_id = int(callback.data.split(":")[1])
    product = await get_product(product_id)
    
    if not product:
        await callback.message.edit_text("❌ Товар не найден")
        return
    
    text = f"""
<b>{product['name']}</b>

{product['description']}

💰 <b>Цена:</b> {product['price']}₽
"""
    
    if product.get('image_url'):
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=product['image_url'],
            caption=text,
            reply_markup=get_product_detail_keyboard(product_id),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=get_product_detail_keyboard(product_id),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("buy_product:"))
async def start_order(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    product_id = int(callback.data.split(":")[1])
    product = await get_product(product_id)
    
    if not product:
        await callback.message.edit_text("❌ Товар не найден")
        return
    
    await state.update_data(
        product_id=product_id,
        product_name=product['name'],
        product_price=product['price']
    )
    await state.set_state(OrderStates.entering_name)
    
    text = (f"🛒 <b>Оформление заказа: {product['name']}</b>\n\n"
            f"💰 Цена: {product['price']}₽\n\n"
            f"Пожалуйста, введите ваше <b>имя</b>:")
    kb = get_cancel_keyboard()
    
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


@router.message(OrderStates.entering_name)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer(
            "❌ Имя слишком короткое. Пожалуйста, введите корректное имя:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(name=name)
    await state.set_state(OrderStates.entering_phone)
    
    await message.answer(
        f"✅ Имя: {name}\n\n"
        f"Теперь введите ваш <b>номер телефона</b>\n"
        f"(например: +79001234567):",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(OrderStates.entering_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    
    if not validate_phone_number(phone):
        await message.answer(
            "❌ Некорректный номер телефона.\n"
            "Пожалуйста, введите номер в формате +79001234567 или 89001234567:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    cleaned_phone = clean_phone_number(phone)
    await state.update_data(phone=cleaned_phone)
    await state.set_state(OrderStates.entering_address)
    
    await message.answer(
        f"✅ Телефон: {cleaned_phone}\n\n"
        f"Теперь введите <b>адрес доставки</b>\n"
        f"(город, улица, дом, квартира):",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(OrderStates.entering_address)
async def process_address(message: Message, state: FSMContext):
    address = message.text.strip()
    if len(address) < 10:
        await message.answer(
            "❌ Адрес слишком короткий. Пожалуйста, введите полный адрес:\n"
            "(город, улица, дом, квартира)",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(address=address)
    data = await state.get_data()
    
    summary = f"""
📋 <b>Проверьте данные заказа:</b>

🛒 <b>Товар:</b> {data['product_name']}
💰 <b>Цена:</b> {data['product_price']}₽

👤 <b>Имя:</b> {data['name']}
📞 <b>Телефон:</b> {data['phone']}
📍 <b>Адрес:</b> {address}

Всё верно?
"""
    
    await state.set_state(OrderStates.confirming_order)
    await message.answer(summary, reply_markup=get_order_confirmation_keyboard(), parse_mode="HTML")


@router.callback_query(OrderStates.confirming_order, F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    data = await state.get_data()
    
    product_info = f"{data['product_name']} ({data['product_price']}₽)"
    
    order_id = await add_order(
        user_id=callback.from_user.id,
        user_name=data['name'],
        phone=data['phone'],
        address=data['address'],
        product_info=product_info,
        total_amount=data['product_price']
    )
    
    # Notify admin
    admin_notification = f"""
🆕 <b>Новый заказ #{order_id}!</b>

🛒 <b>Товар:</b> {data['product_name']}
💰 <b>Сумма:</b> {data['product_price']}₽

👤 <b>Клиент:</b> {data['name']}
📞 <b>Телефон:</b> {data['phone']}
📍 <b>Адрес:</b> {data['address']}

🆔 User ID: {callback.from_user.id}
👤 Username: @{callback.from_user.username or 'не указан'}
"""
    
    try:
        await bot.send_message(ADMIN_ID, admin_notification, parse_mode="HTML")
    except Exception as e:
        print(f"Failed to notify admin: {e}")
    
    await callback.message.edit_text(
        f"✅ <b>Заказ #{order_id} успешно оформлен!</b>\n\n"
        f"Мы свяжемся с вами в ближайшее время для подтверждения.\n\n"
        f"Спасибо за покупку! 🎉",
        parse_mode="HTML"
    )
    
    await state.clear()


@router.callback_query(F.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Заказ отменён")
    await state.clear()
    await callback.message.edit_text(
        "❌ Заказ отменён.\n\nЕсли хотите начать заново, выберите товар в каталоге."
    )


@router.message(F.text == "🛒 Мои заказы")
async def show_my_orders(message: Message):
    orders = await get_orders(user_id=message.from_user.id)
    
    if not orders:
        await message.answer(
            "📭 У вас пока нет заказов.\n\nЗагляните в каталог! 📋",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    text = "📦 <b>Ваши заказы:</b>\n\n"
    for order in orders:
        status_emoji = "⏳" if order['status'] == 'pending' else "✅"
        date_str = order['created_at'][:10] if order['created_at'] else "неизвестно"
        text += f"{status_emoji} <b>Заказ #{order['id']}</b> ({date_str})\n"
        text += f"🛒 {order['product_info']}\n"
        text += f"📍 {order['address']}\n"
        text += f"💰 {order['total_amount']}₽\n\n"
    
    await message.answer(text, reply_markup=get_main_menu_keyboard(), parse_mode="HTML")


@router.message(F.text == "❓ FAQ")
async def show_faq(message: Message):
    await message.answer(
        "❓ <b>Часто задаваемые вопросы</b>\n\nВыберите интересующий вопрос:",
        reply_markup=get_faq_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("faq_"))
async def show_faq_answer(callback: CallbackQuery):
    await callback.answer()
    answer = FAQ_ANSWERS.get(callback.data, "Информация не найдена")
    
    await callback.message.edit_text(
        answer,
        reply_markup=get_faq_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "📞 Контакты")
async def show_contacts(message: Message):
    await message.answer(
        """
📞 <b>Контакты</b>

📱 Телефон: +7 (900) 123-45-67
📧 Email: info@example.com
🌐 Сайт: www.example.com

⏰ Режим работы:
Пн-Пт: 9:00 - 20:00
Сб-Вс: 10:00 - 18:00

Мы всегда рады помочь! 😊
""",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "Главное меню:",
        reply_markup=get_main_menu_keyboard()
    )
