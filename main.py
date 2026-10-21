import asyncio
import logging
import os
import aiohttp
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

# Render porti va tokenlarni olish
PORT = int(os.getenv("PORT", 8080))
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "123456789")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Soxta veb-server (Render uchun)
async def handle(request):
    return web.Response(text="Bilol Burger Bot ishlamoqda!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

# Uyqu rejimiga tushirmaslik uchun ping
async def keep_alive():
    await asyncio.sleep(10)
    while True:
        if RENDER_EXTERNAL_URL:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(RENDER_EXTERNAL_URL) as resp:
                        logging.info(f"Ping status: {resp.status}")
            except Exception as e:
                logging.error(f"Ping xatolik: {e}")
        await asyncio.sleep(600)

# ANIQ MENYU BAZASI
MENU = {
    "🌯 Lavash (Go'shtli)": {
        "Lavash extra": 38000,
        "Lavash Big": 33000,
        "Lavash mini": 28000,
        "Lavash extra (Sirli)": 42000,
        "Lavash Big (Sirli)": 37000,
        "Lavash mini (Sirli)": 32000,
    },
    "🌯 Lavash (Tovuqli)": {
        "Lavash extra Tovuqli": 35000,
        "Lavash big Tovuqli": 30000,
        "Lavash mini Tovuqli": 25000,
        "Lavash extra Tovuqli (Sirli)": 39000,
        "Lavash big Tovuqli (Sirli)": 34000,
        "Lavash mini Tovuqli (Sirli)": 29000,
    },
    "🥙 Donar": {
        "Donar extra": 38000,
        "Donar Big": 33000,
        "Donar extra Tovuqli": 35000,
        "Donar Big Tovuqli": 30000,
    },
    "🍔 Burgerlar": {
        "Gamburger Big (2 kotlet)": 38000,
        "Gamburger Mini (1 kotlet)": 28000,
        "Gamburger Big Sirli (2 kotlet)": 42000,
        "Gamburger Mini Sirli (1 kotlet)": 32000,
        "Zinger chicken": 33000,
        "Zinger chicken (Sirli)": 37000,
        "Chicken burger Big (2 kotlet)": 38000,
        "Chicken burger Mini (1 kotlet)": 28000,
        "Chicken burger Big Sirli": 42000,
        "Chicken burger Mini Sirli": 32000,
    },
    "🥪 Haggi & Sandwich": {
        "Haggi extra": 38000,
        "Haggi Big": 33000,
        "Haggi mini": 28000,
        "Haggi extra Tovuqli": 35000,
        "Haggi Big tovuqli": 30000,
        "Haggi mini tovuqli": 25000,
        "Clap Sandwich Chicken": 38000,
        "Clap Sandwich Go'shtli": 40000,
    },
    "🌭 Hot-Doglar": {
        "Hot-dog shashlikli extra (2 sosiska+2 shashlik)": 38000,
        "Hot-dog shashlikli mini (2 sosiska+1 shashlik)": 28000,
        "Hot-dog extra (4 sosiska)": 28000,
        "Hot-dog Big (3 sosiska)": 25000,
        "Hot-dog (2 sosiska)": 18000,
        "Hot-dog mini (1 sosiska)": 13000,
        "Hot-dog assorti (2 sosiska, kotlet, indeyka, lavash go'shti)": 38000,
    },
    "🍗 KFC & Garnir": {
        "KFC 1 kg": 110000,
        "KFC 0.5 kg": 55000,
        "KFC 1 porsiya": 30000,
        "Kartoshka Free": 15000,
    },
}

class OrderState(StatesGroup):
    choosing_category = State()
    writing_comment = State()
    sending_location = State()
    sending_phone = State()
    confirming_order = State()

# Tugmalar klaviaturasini yasash (sanoq bilan)
def build_items_keyboard(category, cart):
    items = MENU[category]
    inline_kb = []
    for item_name, price in items.items():
        qty = cart.get(item_name, 0)
        btn_text = f"{item_name} ({qty} ta) — {price:,} so'm" if qty > 0 else f"{item_name} — {price:,} so'm"
        inline_kb.append([InlineKeyboardButton(text=btn_text, callback_data=f"add_{item_name}")])
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", {})
    await state.clear()
    await state.update_data(cart=cart)
    
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍔 Menyu"), KeyboardButton(text="🛒 Savatcha")],
            [KeyboardButton(text="📞 Aloqa / Biz haqimizda")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "Assalomu aleykum! **BILOL BURGER** rasmiy botiga xush kelibsiz!\n\n"
        "Buyurtma berish uchun **🍔 Menyu** tugmasini bosing.",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@dp.message(F.text == "⬅️ Asosiy menyu")
async def back_to_main(message: types.Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍔 Menyu"), KeyboardButton(text="🛒 Savatcha")],
            [KeyboardButton(text="📞 Aloqa / Biz haqimizda")]
        ],
        resize_keyboard=True
    )
    await message.answer("Asosiy menyudasiz:", reply_markup=kb)

@dp.message(F.text == "🍔 Menyu")
async def show_categories(message: types.Message, state: FSMContext):
    buttons = [[KeyboardButton(text=cat)] for cat in MENU.keys()]
    buttons.append([KeyboardButton(text="⬅️ Asosiy menyu")])
    kb = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    await state.set_state(OrderState.choosing_category)
    await message.answer("Kerakli bo'limni tanlang:", reply_markup=kb)

@dp.message(OrderState.choosing_category, F.text.in_(MENU.keys()))
async def show_items(message: types.Message, state: FSMContext):
    category = message.text
    await state.update_data(current_category=category)
    data = await state.get_data()
    cart = data.get("cart", {})
    
    kb = build_items_keyboard(category, cart)
    await message.answer(f"**{category}** bo'limi:\n\nSavatga qo'shish uchun taomni bosing:", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: types.CallbackQuery, state: FSMContext):
    item_name = callback.data.split("add_")[1]
    data = await state.get_data()
    cart = data.get("cart", {})
    current_category = data.get("current_category")
    
    cart[item_name] = cart.get(item_name, 0) + 1
    await state.update_data(cart=cart)
    
    # Tugma sanoq bilan yangilanadi
    if current_category:
        new_kb = build_items_keyboard(current_category, cart)
        try:
            await callback.message.edit_reply_markup(reply_markup=new_kb)
        except Exception:
            pass

    await callback.answer(f"✅ {item_name} ({cart[item_name]} ta) savatda!")

@dp.message(F.text == "🛒 Savatcha")
async def show_cart(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", {})
    if not cart:
        await message.answer("🛒 Savatchangiz bo'sh. Menyu bo'limidan taom tanlang!")
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
        text += f"• **{item}** x {qty} ta = {summa:,} so'm\n"
    
    text += f"\n💰 **Jami summa:** {total:,} so'm"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Buyurtmani rasmiylashtirish", callback_data="checkout")],
        [InlineKeyboardButton(text="🗑 Savatni tozalash", callback_data="clear_cart")]
    ])
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "clear_cart")
async def clear_cart(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(cart={})
    await callback.message.edit_text("🗑 Savatchangiz tozalandi.")

# 1. IZOH SO'RASH
@dp.callback_query(F.data == "checkout")
async def checkout_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(OrderState.writing_comment)
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Yo'q ❌")]], resize_keyboard=True)
    await callback.message.answer("Buyurtmaga qo'shimcha izohingiz bormi? (Masalan: *Piyozsiz bo'lsin*):", reply_markup=kb, parse_mode="Markdown")

@dp.message(OrderState.writing_comment)
async def process_comment(message: types.Message, state: FSMContext):
    comment = message.text if message.text != "Yo'q ❌" else "Mavjud emas"
    await state.update_data(comment=comment)
    await state.set_state(OrderState.sending_location)
    
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📍 Joylashuvni yuborish", request_location=True)]], resize_keyboard=True)
    await message.answer("Rahmat! Endi yetkazib berish manzilini (**lokatsiya**) yuboring (xaritadan tanlab ham yuborishingiz mumkin):", reply_markup=kb, parse_mode="Markdown")

# 2. LOKATSIYA QABUL QILISH
@dp.message(OrderState.sending_location, F.location)
async def process_location(message: types.Message, state: FSMContext):
    await state.update_data(lat=message.location.latitude, lon=message.location.longitude)
    await state.set_state(OrderState.sending_phone)
    
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]], resize_keyboard=True)
    await message.answer("Zo'r! Endi siz bilan bog'lanishimiz uchun **telefon raqamingizni** yuboring:", reply_markup=kb, parse_mode="Markdown")

# 3. TELEFON RAQAM VA TASDIQLASH
@dp.message(OrderState.sending_phone, F.contact)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    
    data = await state.get_data()
    cart = data.get("cart", {})
    comment = data.get("comment", "Mavjud emas")
    
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
        cart_text += f"• **{item}** x {qty} ta = {summa:,} so'm\n"
        
    summary_text = (
        f"📋 **Buyurtma ma'lumotlari:**\n\n"
        f"{cart_text}\n"
        f"💰 **Jami summa:** {total:,} so'm\n"
        f"💬 **Izoh:** {comment}\n"
        f"📞 **Telefon:** {phone}\n"
        f"📍 **Manzil:** Lokatsiya biriktirildi\n\n"
        f"Barcha ma'lumotlar to'g'ri bo'lsa, pastdagi tugmani bosing:"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Buyurtma berish", callback_data="confirm_final_order")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_order")]
    ])
    
    await state.set_state(OrderState.confirming_order)
    main_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍔 Menyu"), KeyboardButton(text="🛒 Savatcha")],
            [KeyboardButton(text="📞 Aloqa / Biz haqimizda")]
        ],
        resize_keyboard=True
    )
    await message.answer(summary_text, reply_markup=main_kb, parse_mode="Markdown")
    await message.answer("Tasdiqlash uchun quyidagi tugmani bosing:", reply_markup=kb)

# 4. YAKUNIY BUYURTMA
@dp.callback_query(OrderState.confirming_order, F.data == "confirm_final_order")
async def confirm_order(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", {})
    comment = data.get("comment", "Mavjud emas")
    phone = data.get("phone", "Noma'lum")
    lat = data.get("lat")
    lon = data.get("lon")
    
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
        
    await callback.message.edit_text("🎉 **Buyurtmangiz muvaffaqiyatli qabul qilindi!**\nTez orada operatorimiz siz bilan bog'lanadi.", parse_mode="Markdown")
    
    admin_message = (
        f"🔔 **YANGI BUYURTMA! (BILOL BURGER)**\n\n"
        f"👤 **Mijoz:** {callback.from_user.full_name}\n"
        f"📞 **Tel:** {phone}\n"
        f"💬 **Izoh:** {comment}\n\n"
        f"🛒 **Tarkibi:**\n{cart_text}\n"
        f"💰 **Jami summa:** {total:,} so'm\n"
        f"📍 **Xarita:** https://maps.google.com/maps?q={lat},{lon}"
    )
    
    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message, parse_mode="Markdown")
        await bot.send_location(chat_id=ADMIN_CHAT_ID, latitude=lat, longitude=lon)
    except Exception as e:
        logging.error(f"Adminga yuborishda xatolik: {e}")
        
    await state.clear()

@dp.callback_query(F.data == "cancel_order")
async def cancel_order(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Buyurtma bekor qilindi.")

@dp.message(F.text == "📞 Aloqa / Biz haqimizda")
async def show_about(message: types.Message):
    await message.answer(
        "🍔 **BILOL BURGER**\n\n"
        "Fast-food taomlarini issiq va tezkor yetkazib berish xizmati!\n\n"
        "📞 Tel: +99917892122\n"
        "📍 Manzil: Markaziy filial",
        parse_mode="Markdown"
    )

async def main():
    logging.basicConfig(level=logging.INFO)
    await start_web_server()
    asyncio.create_task(keep_alive())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
