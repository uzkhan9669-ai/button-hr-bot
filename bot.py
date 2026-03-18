import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
HR_CHAT_ID = os.getenv("HR_CHAT_ID")

dp = Dispatcher(storage=MemoryStorage())

# =========================
# DATA
# =========================

TEXTS = {
    "uz": {
        "start": "Assalomu alaykum! BUTTON kompaniyasiga xush kelibsiz.\nTilni tanlang:",
        "choose_branch": "Filialni tanlang:",
        "choose_vacancy": "Vakansiyani tanlang:",
        "full_name": "Ism va familiyangizni kiriting:",
        "phone": "Telefon raqamingizni yuboring yoki yozing:",
        "consent": "Ma'lumotlaringizni BUTTON kompaniyasiga yuborishga rozimisiz?",
        "thanks": "Rahmat! Anketangiz yuborildi ✅",
        "cancel": "Bekor qilindi.",
        "send_phone": "📱 Raqamni yuborish",
        "yes": "Roziman ✅",
        "no": "Bekor qilish ❌",
    },
    "ru": {
        "start": "Здравствуйте! Добро пожаловать в BUTTON.\nВыберите язык:",
        "choose_branch": "Выберите филиал:",
        "choose_vacancy": "Выберите вакансию:",
        "full_name": "Введите имя и фамилию:",
        "phone": "Отправьте номер телефона или введите его:",
        "consent": "Вы согласны отправить свои данные в компанию BUTTON?",
        "thanks": "Спасибо! Ваша анкета отправлена ✅",
        "cancel": "Отменено.",
        "send_phone": "📱 Отправить номер",
        "yes": "Согласен ✅",
        "no": "Отмена ❌",
    },
}

BRANCHES = {
    "andalus": {
        "uz": "Chilonzor — Andalus",
        "ru": "Чиланзар — Andalus",
        "map": "https://maps.app.goo.gl/oYSJC9WdxCHJJCi9A",
        "vacancies": ["seller", "cashier", "security", "cleaner"],
    },
    "integro": {
        "uz": "Chilonzor — Integro",
        "ru": "Чиланзар — Integro",
        "map": "https://maps.app.goo.gl/qkpAoaWKAMcnsNT68",
        "vacancies": ["seller", "cashier", "security", "cleaner"],
    },
    "beruniy": {
        "uz": "Beruniy — Korzinka",
        "ru": "Беруний — Korzinka",
        "map": "https://maps.app.goo.gl/kJG4gRnn6H5aDm6F8",
        "vacancies": ["seller", "cashier", "security", "cleaner"],
    },
    "risoviy": {
        "uz": "Risoviy bozor — Magnit",
        "ru": "Рисовый базар — Magnit",
        "map": "https://maps.app.goo.gl/SYLeo8T8hLAQ92s76",
        "vacancies": ["seller", "cashier", "security", "cleaner"],
    },
    "shaxriston": {
        "uz": "Shaxriston — Korzinka",
        "ru": "Шахристон — Korzinka",
        "map": "https://maps.app.goo.gl/wtqnQgRQKhhksgQ38",
        "vacancies": ["seller", "cashier", "security", "cleaner"],
    },
    "makon": {
        "uz": "Shayxontohur — Makon",
        "ru": "Шайхонтохур — Makon",
        "map": "https://maps.app.goo.gl/MCsg4vuu8fiXYm8N7",
        "vacancies": ["seller", "cashier", "security", "cleaner", "storekeeper"],
    },
    "office": {
        "uz": "Ofis — Andalus",
        "ru": "Офис — Andalus",
        "map": "https://maps.app.goo.gl/GDgu8ar46ffh1zb46",
        "vacancies": ["hr", "operator"],
    },
}

VACANCIES = {
    "seller": {"uz": "Sotuvchi-maslahatchi", "ru": "Продавец-консультант"},
    "cashier": {"uz": "Kassir", "ru": "Кассир"},
    "security": {"uz": "Oxrana", "ru": "Охрана"},
    "cleaner": {"uz": "Tozalik hodimasi", "ru": "Уборщица"},
    "storekeeper": {"uz": "Kladovshik", "ru": "Кладовщик"},
    "hr": {"uz": "HR", "ru": "HR"},
    "operator": {"uz": "Operator", "ru": "Оператор"},
}

# =========================
# FSM
# =========================

class Form(StatesGroup):
    lang = State()
    branch = State()
    vacancy = State()
    full_name = State()
    phone = State()
    consent = State()

# =========================
# HELPERS
# =========================

def t(lang, key):
    return TEXTS[lang][key]

def lang_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="O‘zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="Русский", callback_data="lang_ru")],
    ])

def branch_keyboard(lang):
    buttons = []
    for key, item in BRANCHES.items():
        buttons.append([InlineKeyboardButton(text=item[lang], callback_data=f"branch_{key}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def vacancy_keyboard(lang, branch_key):
    buttons = []
    for key in BRANCHES[branch_key]["vacancies"]:
        buttons.append([InlineKeyboardButton(text=VACANCIES[key][lang], callback_data=f"vacancy_{key}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def phone_keyboard(lang):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(lang, "send_phone"), request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def consent_keyboard(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "yes"), callback_data="consent_yes")],
        [InlineKeyboardButton(text=t(lang, "no"), callback_data="consent_no")],
    ])

def valid_phone(phone: str):
    phone = phone.replace(" ", "").replace("-", "")
    return len(phone) >= 9

# =========================
# HANDLERS
# =========================

@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Form.lang)
    await message.answer("BUTTON HR BOT", reply_markup=ReplyKeyboardRemove())
    await message.answer("Выберите язык / Tilni tanlang:", reply_markup=lang_keyboard())

@dp.callback_query(F.data.startswith("lang_"))
async def language_handler(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    await state.update_data(lang=lang)
    await state.set_state(Form.branch)
    await callback.message.edit_text(t(lang, "choose_branch"), reply_markup=branch_keyboard(lang))
    await callback.answer()

@dp.callback_query(F.data.startswith("branch_"))
async def branch_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    branch_key = callback.data.split("_", 1)[1]

    await state.update_data(branch=branch_key)
    await state.set_state(Form.vacancy)
    await callback.message.edit_text(t(lang, "choose_vacancy"), reply_markup=vacancy_keyboard(lang, branch_key))
    await callback.answer()

@dp.callback_query(F.data.startswith("vacancy_"))
async def vacancy_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    vacancy_key = callback.data.split("_", 1)[1]
    branch_key = data["branch"]

    await state.update_data(vacancy=vacancy_key)
    await callback.message.edit_text(
        f"<b>{BRANCHES[branch_key][lang]}</b>\n📍 {BRANCHES[branch_key]['map']}",
        parse_mode=ParseMode.HTML
    )
    await callback.message.answer(t(lang, "full_name"))
    await state.set_state(Form.full_name)
    await callback.answer()

@dp.message(Form.full_name)
async def full_name_handler(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    data = await state.get_data()
    lang = data["lang"]
    await state.set_state(Form.phone)
    await message.answer(t(lang, "phone"), reply_markup=phone_keyboard(lang))

@dp.message(Form.phone, F.contact)
async def phone_contact_handler(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone

    await state.update_data(phone=phone)
    data = await state.get_data()
    lang = data["lang"]
    await state.set_state(Form.consent)
    await message.answer(t(lang, "consent"), reply_markup=ReplyKeyboardRemove())
    await message.answer(t(lang, "consent"), reply_markup=consent_keyboard(lang))

@dp.message(Form.phone)
async def phone_text_handler(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not valid_phone(phone):
        data = await state.get_data()
        await message.answer(t(data["lang"], "phone"))
        return

    if not phone.startswith("+"):
        phone = "+" + phone

    await state.update_data(phone=phone)
    data = await state.get_data()
    lang = data["lang"]
    await state.set_state(Form.consent)
    await message.answer(t(lang, "consent"), reply_markup=ReplyKeyboardRemove())
    await message.answer(t(lang, "consent"), reply_markup=consent_keyboard(lang))

@dp.callback_query(F.data == "consent_yes")
async def consent_yes_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    lang = data["lang"]

    text = (
        f"<b>📥 Yangi anketa / Новая анкета</b>\n\n"
        f"<b>Til / Язык:</b> {lang}\n"
        f"<b>Filial / Филиал:</b> {BRANCHES[data['branch']][lang]}\n"
        f"<b>Vakansiya / Вакансия:</b> {VACANCIES[data['vacancy']][lang]}\n"
        f"<b>Lokatsiya:</b> {BRANCHES[data['branch']]['map']}\n"
        f"<b>F.I.Sh / ФИО:</b> {data['full_name']}\n"
        f"<b>Telefon / Телефон:</b> {data['phone']}\n"
    )

    try:
        await bot.send_message(chat_id=int(HR_CHAT_ID), text=text, parse_mode=ParseMode.HTML)
    except Exception as e:
        await callback.message.answer(f"Xatolik / Ошибка: {e}")
        await callback.answer()
        return

    await callback.message.edit_text(t(lang, "thanks"))
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "consent_no")
async def consent_no_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.clear()
    await callback.message.edit_text(t(lang, "cancel"))
    await callback.answer()

@dp.message()
async def fallback_handler(message: Message):
    await message.answer("Iltimos, /start bosing. / Пожалуйста, нажмите /start")

# =========================
# MAIN
# =========================

async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN topilmadi")
    if not HR_CHAT_ID:
        raise ValueError("HR_CHAT_ID topilmadi")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
