import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# Render portini olish
PORT = int(os.getenv("PORT", 8080))
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "123456789")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Soxta veb-server (Render to'xtatib qo'ymasligi uchun)
async def handle(request):
    return web.Response(text="Bot ishlamoqda!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

# MENYU BAZASI (BILOL BURGER)
MENU = {
    "Lavash (Go'shtli)": {
        "Lavash Extra": 38000,
        "Lavash Big": 33000,
        "Lavash Mini": 28000,
    },
    "Lavash (Tovuqli)": {
        "Lavash Extra Tovuqli": 35000,
        "Lavash Big Tovuqli": 30000,
        "Lavash Mini Tovuqli": 25000,
    },
    "Donar": {
        "Donar Extra": 38000,
        "Donar Big": 33000,
        "Donar Extra Tovuqli": 35000,
        "Donar Big Tovuqli": 30000,
        "Donar Mini Tovuqli": 25000,
    },
    "Burgerlar": {
        "Gamburger Big (2 kotlet)": 38000,
        "Gamburger Mini (1 kotlet)": 28000,
        "Zinger Chicken": 33000,
        "Chicken Burger Big (2 kotlet)": 38000,
        "Chicken Burger Mini (1 kotlet)": 28000,
    },
    "Haggi & Sandwich": {
        "Haggi Extra": 38000,
        "Haggi Big": 33000,
        "Haggi Mini": 28000,
        "Haggi Extra Tovuqli": 35000,
        "Haggi Big Tovuqli": 30000,
        "Haggi Mini Tovuqli": 25000,
        "Clap Sandwich Chicken": 38000,
        "Clap Sandwich Go'shtli": 40000,
    },
    "Hot-Dog & Kabob": {
        "Hot-dog shashlikli extra": 38000,
        "Hot-dog shashlikli mini": 28000,
        "Hot-dog extra (4 sosiska)": 28000,
        "Hot-dog Big (3 sosiska)": 25000,
        "Hot-dog (2 sosiska)": 18000,
    },
    "KFC & Garnir": {
        "Kartoshka Free": 15000,
        "KFC 1 kg": 110000,
        "KFC 0.5 kg": 55000,
        "KFC 1 porsiya": 30000,
    },
}

class OrderState(StatesGroup):
    choosing_category = State()
    choosing_item = State()
    writing_comment = State()
    sending_phone = State()
    sending_location = State()

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await state.update_data(cart={})
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍔 Menyu"), KeyboardButton(text="🛒 Savatcha")],
            [KeyboardButton(text="📞 Aloqa / Do'kon haqida")]
        ],
        resize_keyboard=True
    )
    await message.answer("Assalomu aleykum! **BILOL BURGER** botiga xush kelibsiz!\nBuyurtma berish uchun **🍔 Menyu** tugmasini bosing.", reply_markup=kb)

@dp.message(F.text == "🍔 Menyu")
async def show_categories(message: types.Message, state: FSMContext):
    buttons = [[KeyboardButton(text=cat)] for cat in MENU.keys()]
    buttons.append([KeyboardButton(text="⬅️ Orqaga / Asosiy menyu")])
    kb = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    await state.set_state(OrderState.choosing_category)
    await message.answer("Kategoriyani tanlang:", reply_markup=kb)

@dp.message(OrderState.choosing_category, F.text.in_(MENU.keys()))
async def show_items(message: types.Message, state: FSMContext):
    category = message.text
    items = MENU[category]
    inline_kb = []
    for item_name, price in items.items():
        inline_kb.append([InlineKeyboardButton(text=f"{item_name} - {price:,} so'm", callback_data=f"add_{item_name}")])
    kb = InlineKeyboardMarkup(inline_keyboard=inline_kb)
    await message.answer(f"**{category}** bo'limi:\nKerakli taomni bosing:", reply_markup=kb)

@dp.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: types.CallbackQuery, state: FSMContext):
    item_name = callback.data.split("add_")[1]
    data = await state.get_data()
    cart = data.get("cart", {})
    cart[item_name] = cart.get(item_name, 0) + 1
    await state.update_data(cart=cart)
    await callback.answer(f"{item_name} savatchaga qo'shildi! 🛒")

@dp.message(F.text == "🛒 Savatcha")
async def show_cart(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", {})
    if not cart:
        await message.answer("Savatchangiz bo'sh. Menyu bo'limidan taom tanlang!")
        return
    total = 0
    text = "🛒 **Sizning savatchangiz:**\n\n"
    for item, qty in cart.items():
        price = 0
        for cat in MENU.values():
            if item in cat:
                price = cat[item]
                break
        summa = price * qty
        total += summa
        text += f"• {item} x {qty} ta = {summa:,} so'm\n"
    text += f"\n💰 **Jami summa:** {total:,} so'm"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Buyurtmani rasmiylashtirish", callback_data="checkout")],
        [InlineKeyboardButton(text="🗑 Savatni tozalash", callback_data="clear_cart")]
    ])
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "clear_cart")
async def clear_cart(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(cart={})
    await callback.message.edit_text("Savatchangiz tozalandi.")

@dp.callback_query(F.data == "checkout")
async def checkout_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(OrderState.writing_comment)
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Izoh yo'q (O'tkazib yuborish)")]], resize_keyboard=True)
    await callback.message.answer("Buyurtmaga qo'shimcha izohingiz bormi? (Masalan: *Piyozsiz bo'lsin*):", reply_markup=kb, parse_mode="Markdown")

@dp.message(OrderState.writing_comment)
async def process_comment(message: types.Message, state: FSMContext):
    comment = message.text if message.text != "Izoh yo'q (O'tkazib yuborish)" else "Mavjud emas"
    await state.update_data(comment=comment)
    await state.set_state(OrderState.sending_phone)
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]], resize_keyboard=True)
    await message.answer("Iltimos, telefon raqamingizni yuboring:", reply_markup=kb)

@dp.message(OrderState.sending_phone, F.contact)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(OrderState.sending_location)
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📍 Joylashuvni yuborish", request_location=True)]], resize_keyboard=True)
    await message.answer("Rahmat! Endi buyurtma yetkazib berilishi kerak bo'lgan **jonli joylashuvni** yuboring:", reply_markup=kb)

@dp.message(OrderState.sending_location, F.location)
async def process_location(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", {})
    comment = data.get("comment", "Yo'q")
    phone = data.get("phone", "Noma'lum")
    lat = message.location.latitude
    lon = message.location.longitude
    
    total = 0
    cart_text = ""
    for item, qty in cart.items():
        price = 0
        for cat in MENU.values():
            if item in cat:
                price = cat[item]
                break
        summa = price * qty
        total += summa
        cart_text += f" - {item} x {qty} ta = {summa:,} so'm\n"
        
    main_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🍔 Menyu"), KeyboardButton(text="🛒 Savatcha")]],
        resize_keyboard=True
    )
    await message.answer("✅ **Buyurtmangiz qabul qilindi!**\nTez orada admin siz bilan bog'lanadi va buyurtma yetkaziladi.", reply_markup=main_kb)
    
    admin_message = (
        f"🔔 **YANGI BUYURTMA!**\n\n"
        f"👤 **Mijoz:** {message.from_user.full_name}\n"
        f"📞 **Tel:** {phone}\n"
        f"💬 **Izoh:** {comment}\n\n"
        f"🛒 **Tarkib:**\n{cart_text}\n"
        f"💰 **Jami summa:** {total:,} so me\n"
        f"📍 **Xarita:** https://maps.google.com/maps?q={lat},{lon}"
    )
    
    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message)
        await bot.send_location(chat_id=ADMIN_CHAT_ID, latitude=lat, longitude=lon)
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        
    await state.clear()

@dp.message(F.text == "⬅️ Orqaga / Asosiy menyu")
async def back_to_main(message: types.Message, state: FSMContext):
    await cmd_start(message, state)

async def main():
    logging.basicConfig(level=logging.INFO)
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
