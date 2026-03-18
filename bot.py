import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

BOT_TOKEN = "YOUR_BOT_TOKEN"
HR_CHAT_ID = -1001234567890  # сюда ID чата/группы HR

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# =========================
# ХРАНЕНИЕ ДАННЫХ
# =========================
user_lang = {}
user_data = {}
user_step = {}

# =========================
# СПРАВОЧНИКИ
# =========================
stores = {
    "Chilonzor — Andalus": {
        "lat": 41.2756,
        "lon": 69.2034,
        "address_uz": "Toshkent shahri, Chilonzor tumani, Andalus savdo markazi, 2-qavat",
        "address_ru": "г. Ташкент, Чиланзарский район, ТЦ Andalus, 2-этаж"
    },
    "Chilonzor — Integro": {
        "lat": 41.2730,
        "lon": 69.2050,
        "address_uz": "Toshkent shahri, Chilonzor tumani, Integro savdo markazi",
        "address_ru": "г. Ташкент, Чиланзарский район, ТЦ Integro"
    },
    "Risoviy bozor — Magnit": {
        "lat": 41.2995,
        "lon": 69.2401,
        "address_uz": "Toshkent shahri, Mirzo Ulug‘bek tumani, Risoviy bozor, Magnit savdo markazi",
        "address_ru": "г. Ташкент, Мирзо-Улугбекский район, Рисовый базар, ТЦ Magnit"
    },
    "Beruniy metro — Korzinka": {
        "lat": 41.3447,
        "lon": 69.2067,
        "address_uz": "Toshkent shahri, Olmazor tumani, Beruniy metro yonida, Korzinka, 2-qavat",
        "address_ru": "г. Ташкент, Алмазарский район, рядом с метро Beruniy, Korzinka, 2-этаж"
    },
    "Shaxriston — Korzinka": {
        "lat": 41.3655,
        "lon": 69.2922,
        "address_uz": "Toshkent shahri, Yunusobod tumani, Shaxriston metro yonida, Korzinka, 2-qavat",
        "address_ru": "г. Ташкент, Юнусабадский район, рядом с метро Shaxriston, Korzinka, 2-этаж"
    },
    "Shayxontohur — Makon supermarketi": {
        "lat": 41.3112,
        "lon": 69.2473,
        "address_uz": "Toshkent shahri, Shayxontohur tumani, Zafarobod mahallasi, Makon supermarketi",
        "address_ru": "г. Ташкент, Шайхантахурский район, махалля Zafarobod, супермаркет Makon"
    },
    "Ofis — Andalus Chilonzor": {
        "lat": 41.2756,
        "lon": 69.2034,
        "address_uz": "Toshkent shahri, Chilonzor tumani, Andalus, BUTTON ofisi",
        "address_ru": "г. Ташкент, Чиланзарский район, ТЦ Andalus, офис BUTTON"
    }
}

vacancy_to_stores = {
    "Sotuvchi-maslahatchi": [
        "Chilonzor — Andalus",
        "Chilonzor — Integro",
        "Risoviy bozor — Magnit",
        "Beruniy metro — Korzinka",
        "Shaxriston — Korzinka"
    ],
    "Kassir": [
        "Chilonzor — Andalus",
        "Chilonzor — Integro",
        "Risoviy bozor — Magnit",
        "Beruniy metro — Korzinka",
        "Shaxriston — Korzinka"
    ],
    "Oxrana": [
        "Chilonzor — Andalus",
        "Chilonzor — Integro",
        "Risoviy bozor — Magnit",
        "Beruniy metro — Korzinka",
        "Shaxriston — Korzinka",
        "Shayxontohur — Makon supermarketi"
    ],
    "Tozalik hodimasi": [
        "Chilonzor — Andalus",
        "Chilonzor — Integro",
        "Risoviy bozor — Magnit",
        "Beruniy metro — Korzinka",
        "Shaxriston — Korzinka"
    ],
    "Helper": [
        "Chilonzor — Andalus",
        "Chilonzor — Integro",
        "Risoviy bozor — Magnit",
        "Beruniy metro — Korzinka",
        "Shaxriston — Korzinka"
    ],
    "Omborchi": [
        "Shayxontohur — Makon supermarketi"
    ],
    "Rekruter": [
        "Ofis — Andalus Chilonzor"
    ],
    "Kadrovik": [
        "Ofis — Andalus Chilonzor"
    ],
    "SSM": [
        "Ofis — Andalus Chilonzor"
    ]
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
    "ССМ": "SSM"
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
    "SSM": "ССМ"
}

TEXTS = {
    "uz": {
        "choose_lang": "🇺🇿 Tilni tanlang / 🇷🇺 Выберите язык",
        "welcome": "BUTTON botiga xush kelibsiz!",
        "choose_vacancy": "Vakansiyani tanlang:",
        "choose_store": "Filialni tanlang:",
        "location_question": "Shu filialda ishlash sizga qulaymi?",
        "ask_name": "Ism va familiyangizni kiriting:",
        "ask_phone": "Telefon raqamingizni yuboring:",
        "ask_district": "Yashash hududingizni yozing:",
        "ask_marital": "Oilaviy holatingizni tanlang:",
        "ask_education": "Ma'lumotingizni tanlang:",
        "ask_study": "Hozirda o‘qiyapsizmi?",
        "ask_study_form": "Ta'lim shaklini tanlang:",
        "ask_work_exp": "Oxirgi ish joyingiz yoki ish tajribangizni yozing:",
        "ask_start_date": "Qachondan ish boshlay olasiz?",
        "ask_photo": "📷 Iltimos, o‘zingizni rasmingizni yuboring",
        "ask_consent": "✅ Kiritilgan ma’lumotlar to‘g‘riligini tasdiqlaysizmi va ularni qayta ishlashga rozimisiz?",
        "done": "✅ Arizangiz qabul qilindi. Tez orada siz bilan bog‘lanamiz.",
        "wrong_photo": "❌ Iltimos, faqat o‘zingizning rasmingizni yuboring.",
        "location_sent": "📍 Siz tanlagan filial lokatsiyasi yuborildi.",
        "yes_location": "Ha, qulay ✅",
        "no_location": "Boshqa filial 🔄",
        "consent": "Roziman ✅",
        "restart": "Qayta boshlash 🔄",
        "share_phone": "Telefon raqamni yuborish 📞",
        "marital_options": [
            "Uylanmagan / Turmushga chiqmagan",
            "Uylangan / Turmushga chiqqan",
            "Ajrashgan",
            "Beva"
        ],
        "education_options": [
            "O‘rta maktab",
            "Kollej / Texnikum",
            "Institut / Universitet"
        ],
        "study_options": ["Ha", "Yo‘q"],
        "study_form_options": ["Kunduzgi", "Sirtqi", "Kechki"]
    },
    "ru": {
        "choose_lang": "🇺🇿 Tilni tanlang / 🇷🇺 Выберите язык",
        "welcome": "Добро пожаловать в бот BUTTON!",
        "choose_vacancy": "Выберите вакансию:",
        "choose_store": "Выберите филиал:",
        "location_question": "Вам удобно работать в этом филиале?",
        "ask_name": "Введите имя и фамилию:",
        "ask_phone": "Отправьте номер телефона:",
        "ask_district": "Напишите район проживания:",
        "ask_marital": "Выберите семейное положение:",
        "ask_education": "Укажите образование:",
        "ask_study": "Вы сейчас учитесь?",
        "ask_study_form": "Выберите форму обучения:",
        "ask_work_exp": "Напишите последнее место работы или опыт работы:",
        "ask_start_date": "С какого дня готовы выйти на работу?",
        "ask_photo": "📷 Пожалуйста, отправьте своё фото",
        "ask_consent": "✅ Подтверждаете правильность данных и согласны на их обработку?",
        "done": "✅ Ваша анкета принята. Скоро с вами свяжутся.",
        "wrong_photo": "❌ Пожалуйста, отправьте только своё фото.",
        "location_sent": "📍 Локация выбранного филиала отправлена.",
        "yes_location": "Да, удобно ✅",
        "no_location": "Выбрать другой 🔄",
        "consent": "Согласен ✅",
        "restart": "Начать заново 🔄",
        "share_phone": "Отправить номер 📞",
        "marital_options": [
            "Холост / Не замужем",
            "Женат / Замужем",
            "Разведён / Разведена",
            "Вдовец / Вдова"
        ],
        "education_options": [
            "Средняя школа",
            "Колледж / Техникум",
            "Институт / Университет"
        ],
        "study_options": ["Да", "Нет"],
        "study_form_options": ["Очная", "Заочная", "Вечерняя"]
    }
}

# =========================
# КЛАВИАТУРЫ
# =========================
def lang_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🇺🇿 O‘zbekcha"))
    kb.add(KeyboardButton("🇷🇺 Русский"))
    return kb

def vacancy_keyboard(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if lang == "uz":
        buttons = [
            "Sotuvchi-maslahatchi",
            "Kassir",
            "Oxrana",
            "Tozalik hodimasi",
            "Helper",
            "Omborchi",
            "Rekruter",
            "Kadrovik",
            "SSM"
        ]
    else:
        buttons = [
            "Продавец-консультант",
            "Кассир",
            "Охранник",
            "Сотрудник по уборке",
            "Хелпер",
            "Кладовщик",
            "Рекрутер",
            "Кадровик",
            "ССМ"
        ]
    for btn in buttons:
        kb.add(KeyboardButton(btn))
    return kb

def store_keyboard(store_list, lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    for store in store_list:
        kb.add(KeyboardButton(store))
    kb.add(KeyboardButton(TEXTS[lang]["restart"]))
    return kb

def location_confirm_keyboard(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton(TEXTS[lang]["yes_location"]))
    kb.add(KeyboardButton(TEXTS[lang]["no_location"]))
    return kb

def phone_keyboard(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton(TEXTS[lang]["share_phone"], request_contact=True))
    return kb

def options_keyboard(options):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    for item in options:
        kb.add(KeyboardButton(item))
    return kb

def consent_keyboard(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton(TEXTS[lang]["consent"]))
    kb.add(KeyboardButton(TEXTS[lang]["restart"]))
    return kb

# =========================
# ВСПОМОГАТЕЛЬНЫЕ
# =========================
def reset_user(user_id):
    user_data[user_id] = {}
    user_step[user_id] = "choose_lang"

def get_lang(user_id):
    return user_lang.get(user_id, "uz")

async def send_vacancy_menu(message: types.Message, user_id: int):
    lang = get_lang(user_id)
    user_step[user_id] = "choose_vacancy"
    await message.answer(
        f"{TEXTS[lang]['welcome']}\n\n{TEXTS[lang]['choose_vacancy']}",
        reply_markup=vacancy_keyboard(lang)
    )

async def send_store_menu(message: types.Message, user_id: int):
    lang = get_lang(user_id)
    vacancy = user_data[user_id]["vacancy"]
    available_stores = vacancy_to_stores.get(vacancy, [])
    user_step[user_id] = "choose_store"
    await message.answer(TEXTS[lang]["choose_store"], reply_markup=store_keyboard(available_stores, lang))

async def send_hr_summary(user_id: int):
    data = user_data.get(user_id, {})
    lang = get_lang(user_id)

    vacancy_internal = data.get("vacancy", "-")
    vacancy_display = vacancy_internal if lang == "uz" else vacancy_map_internal_to_ru.get(vacancy_internal, vacancy_internal)
    store_name = data.get("store", "-")

    summary = (
        f"📥 <b>Yangi nomzod / Новый кандидат</b>\n\n"
        f"<b>Til / Язык:</b> {'O‘zbekcha' if lang == 'uz' else 'Русский'}\n"
        f"<b>Vakansiya / Вакансия:</b> {vacancy_display}\n"
        f"<b>Filial / Филиал:</b> {store_name}\n"
        f"<b>F.I.Sh / ФИО:</b> {data.get('full_name', '-')}\n"
        f"<b>Telefon / Телефон:</b> {data.get('phone', '-')}\n"
        f"<b>Hudud / Район:</b> {data.get('district', '-')}\n"
        f"<b>Oilaviy holati / Семейное положение:</b> {data.get('marital_status', '-')}\n"
        f"<b>Ma'lumoti / Образование:</b> {data.get('education', '-')}\n"
        f"<b>O‘qiydimi / Учится:</b> {data.get('is_studying', '-')}\n"
        f"<b>Ta'lim shakli / Форма обучения:</b> {data.get('study_form', '-')}\n"
        f"<b>Ish tajribasi / Опыт работы:</b> {data.get('work_exp', '-')}\n"
        f"<b>Ishga chiqish sanasi / Готов выйти:</b> {data.get('start_date', '-')}\n"
    )

    photo_file_id = data.get("photo_file_id")
    if photo_file_id:
        await bot.send_photo(
            chat_id=HR_CHAT_ID,
            photo=photo_file_id,
            caption=summary
        )
    else:
        await bot.send_message(chat_id=HR_CHAT_ID, text=summary)

# =========================
# START
# =========================
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    reset_user(user_id)
    await message.answer(TEXTS["uz"]["choose_lang"], reply_markup=lang_keyboard())

# =========================
# ПЕРЕЗАПУСК
# =========================
@dp.message_handler(lambda message: message.text in ["Qayta boshlash 🔄", "Начать заново 🔄"])
async def restart_form(message: types.Message):
    user_id = message.from_user.id
    reset_user(user_id)
    await message.answer(TEXTS["uz"]["choose_lang"], reply_markup=lang_keyboard())

# =========================
# ВЫБОР ЯЗЫКА
# =========================
@dp.message_handler(lambda message: message.text in ["🇺🇿 O‘zbekcha", "🇷🇺 Русский"])
async def choose_language(message: types.Message):
    user_id = message.from_user.id

    if message.text == "🇺🇿 O‘zbekcha":
        user_lang[user_id] = "uz"
    else:
        user_lang[user_id] = "ru"

    if user_id not in user_data:
        user_data[user_id] = {}

    await send_vacancy_menu(message, user_id)

# =========================
# ВЫБОР ВАКАНСИИ
# =========================
@dp.message_handler(lambda message: message.text in list(vacancy_map_ru_to_internal.keys()) + list(vacancy_to_stores.keys()))
async def choose_vacancy(message: types.Message):
    user_id = message.from_user.id
    lang = get_lang(user_id)

    vacancy = message.text
    if vacancy in vacancy_map_ru_to_internal:
        vacancy = vacancy_map_ru_to_internal[vacancy]

    if user_id not in user_data:
        user_data[user_id] = {}

    user_data[user_id]["vacancy"] = vacancy
    await send_store_menu(message, user_id)

# =========================
# ВЫБОР ФИЛИАЛА
# =========================
@dp.message_handler(lambda message: message.text in stores)
async def choose_store(message: types.Message):
    user_id = message.from_user.id
    lang = get_lang(user_id)

    if user_id not in user_data or "vacancy" not in user_data[user_id]:
        await send_vacancy_menu(message, user_id)
        return

    store_name = message.text
    vacancy = user_data[user_id]["vacancy"]
    allowed_stores = vacancy_to_stores.get(vacancy, [])

    if store_name not in allowed_stores:
        await send_store_menu(message, user_id)
        return

    user_data[user_id]["store"] = store_name
    store = stores[store_name]

    await bot.send_location(
        chat_id=message.chat.id,
        latitude=store["lat"],
        longitude=store["lon"]
    )

    address_text = store["address_uz"] if lang == "uz" else store["address_ru"]
    user_step[user_id] = "confirm_store"

    await message.answer(
        f"{TEXTS[lang]['location_sent']}\n\n"
        f"🏬 {'Filial' if lang == 'uz' else 'Филиал'}: {store_name}\n"
        f"📍 {'Manzil' if lang == 'uz' else 'Адрес'}: {address_text}\n\n"
        f"{TEXTS[lang]['location_question']}",
        reply_markup=location_confirm_keyboard(lang)
    )

# =========================
# ПОДТВЕРЖДЕНИЕ ФИЛИАЛА
# =========================
@dp.message_handler(lambda message: message.text in [
    TEXTS["uz"]["yes_location"], TEXTS["uz"]["no_location"],
    TEXTS["ru"]["yes_location"], TEXTS["ru"]["no_location"]
])
async def handle_store_confirmation(message: types.Message):
    user_id = message.from_user.id
    lang = get_lang(user_id)

    if user_id not in user_data or "vacancy" not in user_data[user_id]:
        await send_vacancy_menu(message, user_id)
        return

    if message.text == TEXTS[lang]["yes_location"]:
        user_step[user_id] = "full_name"
        await message.answer(TEXTS[lang]["ask_name"], reply_markup=ReplyKeyboardRemove())
    else:
        await send_store_menu(message, user_id)

# =========================
# ШАГИ АНКЕТЫ
# =========================
@dp.message_handler(content_types=types.ContentType.CONTACT)
async def handle_contact(message: types.Message):
    user_id = message.from_user.id
    lang = get_lang(user_id)

    if user_step.get(user_id) != "phone":
        return

    user_data[user_id]["phone"] = message.contact.phone_number
    user_step[user_id] = "district"
    await message.answer(TEXTS[lang]["ask_district"], reply_markup=ReplyKeyboardRemove())

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    lang = get_lang(user_id)

    if user_step.get(user_id) != "photo":
        return

    user_data[user_id]["photo_file_id"] = message.photo[-1].file_id
    user_step[user_id] = "consent"
    await message.answer(TEXTS[lang]["ask_consent"], reply_markup=consent_keyboard(lang))

@dp.message_handler(lambda message: message.text in [TEXTS["uz"]["consent"], TEXTS["ru"]["consent"]])
async def handle_consent(message: types.Message):
    user_id = message.from_user.id
    lang = get_lang(user_id)

    if user_step.get(user_id) != "consent":
        return

    await send_hr_summary(user_id)
    await message.answer(TEXTS[lang]["done"], reply_markup=ReplyKeyboardRemove())
    user_step[user_id] = "done"

@dp.message_handler()
async def process_form_steps(message: types.Message):
    user_id = message.from_user.id
    lang = get_lang(user_id)
    step = user_step.get(user_id)

    if not step:
        reset_user(user_id)
        await message.answer(TEXTS["uz"]["choose_lang"], reply_markup=lang_keyboard())
        return

    if step == "choose_lang":
        await message.answer(TEXTS["uz"]["choose_lang"], reply_markup=lang_keyboard())
        return

    if step == "choose_vacancy":
        await message.answer(TEXTS[lang]["choose_vacancy"], reply_markup=vacancy_keyboard(lang))
        return

    if step == "choose_store":
        await send_store_menu(message, user_id)
        return

    if step == "full_name":
        user_data[user_id]["full_name"] = message.text
        user_step[user_id] = "phone"
        await message.answer(TEXTS[lang]["ask_phone"], reply_markup=phone_keyboard(lang))
        return

    if step == "phone":
        user_data[user_id]["phone"] = message.text
        user_step[user_id] = "district"
        await message.answer(TEXTS[lang]["ask_district"], reply_markup=ReplyKeyboardRemove())
        return

    if step == "district":
        user_data[user_id]["district"] = message.text
        user_step[user_id] = "marital_status"
        await message.answer(TEXTS[lang]["ask_marital"], reply_markup=options_keyboard(TEXTS[lang]["marital_options"]))
        return

    if step == "marital_status":
        if message.text not in TEXTS[lang]["marital_options"]:
            await message.answer(TEXTS[lang]["ask_marital"], reply_markup=options_keyboard(TEXTS[lang]["marital_options"]))
            return
        user_data[user_id]["marital_status"] = message.text
        user_step[user_id] = "education"
        await message.answer(TEXTS[lang]["ask_education"], reply_markup=options_keyboard(TEXTS[lang]["education_options"]))
        return

    if step == "education":
        if message.text not in TEXTS[lang]["education_options"]:
            await message.answer(TEXTS[lang]["ask_education"], reply_markup=options_keyboard(TEXTS[lang]["education_options"]))
            return
        user_data[user_id]["education"] = message.text
        user_step[user_id] = "is_studying"
        await message.answer(TEXTS[lang]["ask_study"], reply_markup=options_keyboard(TEXTS[lang]["study_options"]))
        return

    if step == "is_studying":
        if message.text not in TEXTS[lang]["study_options"]:
            await message.answer(TEXTS[lang]["ask_study"], reply_markup=options_keyboard(TEXTS[lang]["study_options"]))
            return
        user_data[user_id]["is_studying"] = message.text

        positive_study = "Ha" if lang == "uz" else "Да"
        if message.text == positive_study:
            user_step[user_id] = "study_form"
            await message.answer(TEXTS[lang]["ask_study_form"], reply_markup=options_keyboard(TEXTS[lang]["study_form_options"]))
        else:
            user_data[user_id]["study_form"] = "-"
            user_step[user_id] = "work_exp"
            await message.answer(TEXTS[lang]["ask_work_exp"], reply_markup=ReplyKeyboardRemove())
        return

    if step == "study_form":
        if message.text not in TEXTS[lang]["study_form_options"]:
            await message.answer(TEXTS[lang]["ask_study_form"], reply_markup=options_keyboard(TEXTS[lang]["study_form_options"]))
            return
        user_data[user_id]["study_form"] = message.text
        user_step[user_id] = "work_exp"
        await message.answer(TEXTS[lang]["ask_work_exp"], reply_markup=ReplyKeyboardRemove())
        return

    if step == "work_exp":
        user_data[user_id]["work_exp"] = message.text
        user_step[user_id] = "start_date"
        await message.answer(TEXTS[lang]["ask_start_date"])
        return

    if step == "start_date":
        user_data[user_id]["start_date"] = message.text
        user_step[user_id] = "photo"
        await message.answer(TEXTS[lang]["ask_photo"], reply_markup=ReplyKeyboardRemove())
        return

    if step == "photo":
        await message.answer(TEXTS[lang]["wrong_photo"])
        return

    if step == "consent":
        await message.answer(TEXTS[lang]["ask_consent"], reply_markup=consent_keyboard(lang))
        return

    if step == "done":
        await message.answer(TEXTS[lang]["done"])
        return

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
