import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# ===== НАСТРОЙКИ =====
BOT_TOKEN = os.getenv("BOT_TOKEN", "8731952281:AAHlcIryCTRTF1ZBG11LFQdGfUv4mr29BgA")
HR_ID = int(os.getenv("HR_ID", "546403983"))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# ===== ХРАНЕНИЕ =====
user_lang = {}
user_data = {}
user_step = {}

# ===== МАГАЗИНЫ =====
stores = {
    "Chilonzor — Andalus": {
        "lat": 41.2756,
        "lon": 69.2034,
        "address_uz": "Toshkent shahri, Chilonzor tumani, Andalus savdo markazi, 2-qavat",
        "address_ru": "г. Ташкент, Чиланзарский район, ТЦ Andalus, 2-этаж",
    },
    "Chilonzor — Integro": {
        "lat": 41.2730,
        "lon": 69.2050,
        "address_uz": "Toshkent shahri, Chilonzor tumani, Integro savdo markazi",
        "address_ru": "г. Ташкент, Чиланзарский район, ТЦ Integro",
    },
    "Risoviy bozor — Magnit": {
        "lat": 41.2995,
        "lon": 69.2401,
        "address_uz": "Toshkent shahri, Mirzo Ulug‘bek tumani, Risoviy bozor, Magnit savdo markazi",
        "address_ru": "г. Ташкент, Мирзо-Улугбекский район, Рисовый базар, ТЦ Magnit",
    },
    "Beruniy metro — Korzinka": {
        "lat": 41.3447,
        "lon": 69.2067,
        "address_uz": "Toshkent shahri, Olmazor tumani, Beruniy metro yonida, Korzinka, 2-qavat",
        "address_ru": "г. Ташкент, Алмазарский район, рядом с метро Beruniy, Korzinka, 2-этаж",
    },
    "Shaxriston — Korzinka": {
        "lat": 41.3655,
        "lon": 69.2922,
        "address_uz": "Toshkent shahri, Yunusobod tumani, Shaxriston metro yonida, Korzinka, 2-qavat",
        "address_ru": "г. Ташкент, Юнусабадский район, рядом с метро Shaxriston, Korzinka, 2-этаж",
    },
    "Shayxontohur — Makon supermarketi": {
        "lat": 41.3112,
        "lon": 69.2473,
        "address_uz": "Toshkent shahri, Shayxontohur tumani, Zafarobod mahallasi, Makon supermarketi",
        "address_ru": "г. Ташкент, Шайхантахурский район, махалля Zafarobod, супермаркет Makon",
    },
    "Ofis — Andalus Chilonzor": {
        "lat": 41.2756,
        "lon": 69.2034,
        "address_uz": "Toshkent shahri, Chilonzor tumani, Andalus, BUTTON ofisi",
        "address_ru": "г. Ташкент, Чиланзарский район, ТЦ Andalus, офис BUTTON",
    },
}

# ===== ВАКАНСИИ =====
vacancy_to_stores = {
    "Sotuvchi-maslahatchi": [
        "Chilonzor — Andalus",
        "Chilonzor — Integro",
        "Risoviy bozor — Magnit",
        "Beruniy metro — Korzinka",
        "Shaxriston — Korzinka",
    ],
    "Kassir": [
        "Chilonzor — Andalus",
        "Chilonzor — Integro",
        "Risoviy bozor — Magnit",
        "Beruniy metro — Korzinka",
        "Shaxriston — Korzinka",
    ],
    "Oxrana": [
        "Chilonzor — Andalus",
        "Chilonzor — Integro",
        "Risoviy bozor — Magnit",
        "Beruniy metro — Korzinka",
        "Shaxriston — Korzinka",
        "Shayxontohur — Makon supermarketi",
    ],
    "Tozalik hodimasi": [
        "Chilonzor — Andalus",
        "Chilonzor — Integro",
        "Risoviy bozor — Magnit",
        "Beruniy metro — Korzinka",
        "Shaxriston — Korzinka",
    ],
    "Helper": [
        "Chilonzor — Andalus",
        "Chilonzor — Integro",
        "Risoviy bozor — Magnit",
        "Beruniy metro — Korzinka",
        "Shaxriston — Korzinka",
    ],
    "Omborchi": [
        "Shayxontohur — Makon supermarketi",
    ],
    "Rekruter": [
        "Ofis — Andalus Chilonzor",
    ],
    "Kadrovik": [
        "Ofis — Andalus Chilonzor",
    ],
    "SSM": [
        "Ofis — Andalus Chilonzor",
    ],
}

vacancy_map_ru_to_internal = {
    "Продавец-консультант": "Sotuvchi-maslahatchi",
    "Кассир": "Kassir",
    "Охранник": "Oxrana",
    "Сотрудник по уборке": "Tozalik hodimasi",
    "Хелпер": "Helper",
    "Кладовщик": "Omborchi",
    "Рекрутер": "Rekruter",
    "Кадровик": "Kadrovik",
    "ССМ": "SSM",
}

vacancy_map_internal_to_ru = {
    "Sotuvchi-maslahatchi": "Продавец-консультант",
    "Kassir": "Кассир",
    "Oxrana": "Охранник",
    "Tozalik hodimasi": "Сотрудник по уборке",
    "Helper": "Хелпер",
    "Omborchi": "Кладовщик",
    "Rekruter": "Рекрутер",
    "Kadrovik": "Кадровик",
    "SSM": "ССМ",
}

TEXTS = {
    "uz": {
        "choose_lang": "🇺🇿 Tilni tanlang / 🇷🇺 Выберите язык",
        "choose_vacancy": "Vakansiyani tanlang:",
        "choose_store": "Filialni tanlang:",
        "location_question": "Shu filialda ishlash sizga qulaymi?",
        "yes_location": "Ha, qulay ✅",
        "no_location": "Boshqa filial 🔄",
        "ask_name": "Ism va familiyangizni kiriting:",
        "ask_phone": "Telefon raqamingizni yuboring:",
        "ask_photo": "📷 Iltimos, o‘zingizni rasmingizni yuboring",
        "ask_consent": "✅ Kiritilgan ma’lumotlar to‘g‘riligini tasdiqlaysizmi?",
        "consent": "Roziman ✅",
        "done": "✅ Arizangiz qabul qilindi. Tez orada siz bilan bog‘lanamiz.",
        "wrong_photo": "❌ Iltimos, faqat rasmingizni yuboring.",
        "share_phone": "Telefon raqamni yuborish 📞",
        "cancel": "❌ Bekor qilish",
    },
    "ru": {
        "choose_lang": "🇺🇿 Tilni tanlang / 🇷🇺 Выберите язык",
        "choose_vacancy": "Выберите вакансию:",
        "choose_store": "Выберите филиал:",
        "location_question": "Вам удобно работать в этом филиале?",
        "yes_location": "Да, удобно ✅",
        "no_location": "Выбрать другой 🔄",
        "ask_name": "Введите имя и фамилию:",
        "ask_phone": "Отправьте номер телефона:",
        "ask_photo": "📷 Пожалуйста, отправьте своё фото",
        "ask_consent": "✅ Подтверждаете правильность данных?",
        "consent": "Согласен ✅",
        "done": "✅ Ваша анкета принята. Скоро с вами свяжутся.",
        "wrong_photo": "❌ Пожалуйста, отправьте только своё фото.",
        "share_phone": "Отправить номер 📞",
        "cancel": "❌ Отмена",
    },
}

# ===== КЛАВИАТУРЫ =====
def lang_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🇺🇿 O‘zbekcha"), KeyboardButton("🇷🇺 Русский"))
    return kb

def vacancy_keyboard(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if lang == "uz":
        buttons = [
            "Sotuvchi-maslahatchi", "Kassir", "Oxrana",
            "Tozalik hodimasi", "Helper", "Omborchi",
            "Rekruter", "Kadrovik", "SSM"
        ]
    else:
        buttons = [
            "Продавец-консультант", "Кассир", "Охранник",
            "Сотрудник по уборке", "Хелпер", "Кладовщик",
            "Рекрутер", "Кадровик", "ССМ"
        ]
    for btn in buttons:
        kb.add(KeyboardButton(btn))
    kb.add(KeyboardButton(TEXTS[lang]["cancel"]))
    return kb

def store_keyboard(store_list, lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    for store in store_list:
        kb.add(KeyboardButton(store))
    kb.add(KeyboardButton(TEXTS[lang]["cancel"]))
    return kb

def location_confirm_keyboard(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton(TEXTS[lang]["yes_location"]))
    kb.add(KeyboardButton(TEXTS[lang]["no_location"]))
    kb.add(KeyboardButton(TEXTS[lang]["cancel"]))
    return kb

def phone_keyboard(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton(TEXTS[lang]["share_phone"], request_contact=True))
    kb.add(KeyboardButton(TEXTS[lang]["cancel"]))
    return kb

def consent_keyboard(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton(TEXTS[lang]["consent"]))
    kb.add(KeyboardButton(TEXTS[lang]["cancel"]))
    return kb

# ===== ВСПОМОГАТЕЛЬНЫЕ =====
def reset_user(user_id):
    user_data[user_id] = {}
    user_step[user_id] = "choose_lang"

def get_lang(user_id):
    return user_lang.get(user_id, "uz")

async def send_to_hr(user_id):
    data = user_data.get(user_id, {})
    lang = get_lang(user_id)
    vacancy = data.get("vacancy", "-")
    if lang == "ru":
        vacancy = vacancy_map_internal_to_ru.get(vacancy, vacancy)

    text = (
        f"📥 <b>Новый кандидат</b>\n\n"
        f"<b>Язык:</b> {'O‘zbekcha' if lang == 'uz' else 'Русский'}\n"
        f"<b>Вакансия:</b> {vacancy}\n"
        f"<b>Филиал:</b> {data.get('store', '-')}\n"
        f"<b>ФИО:</b> {data.get('full_name', '-')}\n"
        f"<b>Телефон:</b> {data.get('phone', '-')}\n"
    )

    photo_id = data.get("photo_file_id")
    if photo_id:
        await bot.send_photo(HR_ID, photo_id, caption=text)
    else:
        await bot.send_message(HR_ID, text)

# ===== СТАРТ =====
@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    reset_user(user_id)
    await message.answer(TEXTS["uz"]["choose_lang"], reply_markup=lang_keyboard())

# ===== ОТМЕНА =====
@dp.message_handler(lambda m: m.text in ["❌ Bekor qilish", "❌ Отмена"])
async def cancel_form(message: types.Message):
    user_id = message.from_user.id
    reset_user(user_id)
    await message.answer("Bekor qilindi / Отменено. Qayta boshlash uchun /start", reply_markup=ReplyKeyboardRemove())

# ===== ЯЗЫК =====
@dp.message_handler(lambda m: m.text in ["🇺🇿 O‘zbekcha", "🇷🇺 Русский"])
async def choose_lang(message: types.Message):
    user_id = message.from_user.id
    user_lang[user_id] = "uz" if message.text == "🇺🇿 O‘zbekcha" else "ru"
    lang = get_lang(user_id)
    user_step[user_id] = "vacancy"
    await message.answer(TEXTS[lang]["choose_vacancy"], reply_markup=vacancy_keyboard(lang))

# ===== ВАКАНСИЯ =====
@dp.message_handler(lambda m: m.text in list(vacancy_to_stores.keys()) + list(vacancy_map_ru_to_internal.keys()))
async def choose_vacancy(message: types.Message):
    user_id = message.from_user.id
    lang = get_lang(user_id)

    vacancy = message.text
    if vacancy in vacancy_map_ru_to_internal:
        vacancy = vacancy_map_ru_to_internal[vacancy]

    user_data.setdefault(user_id, {})
    user_data[user_id]["vacancy"] = vacancy
    user_step[user_id] = "store"

    stores_list = vacancy_to_stores.get(vacancy, [])
    await message.answer(TEXTS[lang]["choose_store"], reply_markup=store_keyboard(stores_list, lang))

# ===== МАГАЗИН =====
@dp.message_handler(lambda m: m.text in stores)
async def choose_store(message: types.Message):
    user_id = message.from_user.id
    lang = get_lang(user_id)

    vacancy = user_data.get(user_id, {}).get("vacancy")
    if not vacancy:
        user_step[user_id] = "vacancy"
        await message.answer(TEXTS[lang]["choose_vacancy"], reply_markup=vacancy_keyboard(lang))
        return

    if message.text not in vacancy_to_stores.get(vacancy, []):
        await message.answer(TEXTS[lang]["choose_store"], reply_markup=store_keyboard(vacancy_to_stores[vacancy], lang))
        return

    user_data[user_id]["store"] = message.text
    user_step[user_id] = "confirm_store"

    store = stores[message.text]
    address = store["address_uz"] if lang == "uz" else store["address_ru"]

    await bot.send_location(message.chat.id, store["lat"], store["lon"])
    await message.answer(
        f"🏬 {message.text}\n📍 {address}\n\n{TEXTS[lang]['location_question']}",
        reply_markup=location_confirm_keyboard(lang)
    )

# ===== ПОДТВЕРЖДЕНИЕ ФИЛИАЛА =====
@dp.message_handler(lambda m: m.text in ["Ha, qulay ✅", "Boshqa filial 🔄", "Да, удобно ✅", "Выбрать другой 🔄"])
async def confirm_store(message: types.Message):
    user_id = message.from_user.id
    lang = get_lang(user_id)

    if message.text == TEXTS[lang]["yes_location"]:
        user_step[user_id] = "name"
        await message.answer(TEXTS[lang]["ask_name"], reply_markup=ReplyKeyboardRemove())
    else:
        vacancy = user_data.get(user_id, {}).get("vacancy")
        if not vacancy:
            user_step[user_id] = "vacancy"
            await message.answer(TEXTS[lang]["choose_vacancy"], reply_markup=vacancy_keyboard(lang))
            return
        user_step[user_id] = "store"
        await message.answer(TEXTS[lang]["choose_store"], reply_markup=store_keyboard(vacancy_to_stores[vacancy], lang))

# ===== КОНТАКТ =====
@dp.message_handler(content_types=types.ContentType.CONTACT)
async def get_contact(message: types.Message):
    user_id = message.from_user.id
    lang = get_lang(user_id)

    if user_step.get(user_id) != "phone":
        return

    user_data[user_id]["phone"] = message.contact.phone_number
    user_step[user_id] = "photo"
    await message.answer(TEXTS[lang]["ask_photo"], reply_markup=ReplyKeyboardRemove())

# ===== ФОТО =====
@dp.message_handler(content_types=types.ContentType.PHOTO)
async def get_photo(message: types.Message):
    user_id = message.from_user.id
    lang = get_lang(user_id)

    if user_step.get(user_id) != "photo":
        return

    user_data[user_id]["photo_file_id"] = message.photo[-1].file_id
    user_step[user_id] = "consent"
    await message.answer(TEXTS[lang]["ask_consent"], reply_markup=consent_keyboard(lang))

# ===== СОГЛАСИЕ =====
@dp.message_handler(lambda m: m.text in ["Roziman ✅", "Согласен ✅"])
async def final_consent(message: types.Message):
    user_id = message.from_user.id
    lang = get_lang(user_id)

    if user_step.get(user_id) != "consent":
        return

    await send_to_hr(user_id)
    user_step[user_id] = "done"
    await message.answer(TEXTS[lang]["done"], reply_markup=ReplyKeyboardRemove())

# ===== ОСНОВНОЙ ПОТОК =====
@dp.message_handler()
async def main_flow(message: types.Message):
    user_id = message.from_user.id
    lang = get_lang(user_id)

    if user_id not in user_step:
        reset_user(user_id)
        await message.answer(TEXTS["uz"]["choose_lang"], reply_markup=lang_keyboard())
        return

    step = user_step.get(user_id)

    if step == "name":
        user_data[user_id]["full_name"] = message.text
        user_step[user_id] = "phone"
        await message.answer(TEXTS[lang]["ask_phone"], reply_markup=phone_keyboard(lang))
        return

    if step == "phone":
        user_data[user_id]["phone"] = message.text
        user_step[user_id] = "photo"
        await message.answer(TEXTS[lang]["ask_photo"], reply_markup=ReplyKeyboardRemove())
        return

    if step == "photo":
        await message.answer(TEXTS[lang]["wrong_photo"])
        return

    if step == "vacancy":
        await message.answer(TEXTS[lang]["choose_vacancy"], reply_markup=vacancy_keyboard(lang))
        return

    if step == "store":
        vacancy = user_data.get(user_id, {}).get("vacancy")
        if vacancy:
            await message.answer(TEXTS[lang]["choose_store"], reply_markup=store_keyboard(vacancy_to_stores[vacancy], lang))
        else:
            await message.answer(TEXTS[lang]["choose_vacancy"], reply_markup=vacancy_keyboard(lang))
        return

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
