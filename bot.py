import asyncio
import logging
from typing import Dict, Any

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
from aiogram.filters import CommandStart, Command

# =========================
# CONFIG
# =========================
BOT_TOKEN = "8731952281:AAHlcIryCTRTF1ZBG11LFQdGfUv4mr29BgA"
HR_CHAT_ID = -546403983  # <-- сюда вставь ID группы/канала/лички HR

logging.basicConfig(level=logging.INFO)

# =========================
# DATA
# =========================

LANG_TEXT = {
    "uz": {
        "welcome": "Assalomu alaykum! BUTTON kompaniyasiga xush kelibsiz.\nTilni tanlang:",
        "choose_branch": "Filialni tanlang:",
        "choose_vacancy": "Vakansiyani tanlang:",
        "branch_info": "Tanlangan filial: <b>{branch}</b>\n\n📍 Lokatsiya: {map_url}",
        "start_form": "Endi qisqa anketani to‘ldiramiz.",
        "full_name": "Ism va familiyangizni kiriting:",
        "birth_year": "Tug‘ilgan yilingizni kiriting:",
        "phone": "Telefon raqamingizni yuboring yoki yozing:",
        "address": "Yashash manzilingizni kiriting:",
        "marital": "Oilaviy holatingizni tanlang:",
        "education": "Ma'lumotingizni tanlang:",
        "is_studying": "Hozir o‘qiyapsizmi?",
        "study_type": "O‘qish turini tanlang:",
        "experience": "Ish tajribangiz bormi?",
        "last_job": "Oxirgi ish joyingizni yozing:",
        "last_position": "Oxirgi lavozimingizni yozing:",
        "start_date": "Qachondan ish boshlay olasiz?",
        "consent": "Ma'lumotlaringiz BUTTON kompaniyasida ko‘rib chiqilishiga rozimisiz?",
        "thanks": "Rahmat! Anketangiz qabul qilindi ✅\nTez orada siz bilan bog‘lanamiz.",
        "cancelled": "Jarayon bekor qilindi.",
        "invalid_year": "Iltimos, tug‘ilgan yilni to‘g‘ri kiriting. Masalan: 1999",
        "invalid_phone": "Iltimos, telefon raqamni to‘g‘ri yuboring.",
        "choose_option": "Iltimos, tugmalardan birini tanlang.",
        "send_contact": "📱 Raqamni yuborish",
        "consent_yes": "Roziman ✅",
        "consent_no": "Bekor qilish ❌",
        "yes": "Ha",
        "no": "Yo‘q",
        "btn_restart": "🔄 Qayta boshlash",
        "btn_cancel": "❌ Bekor qilish",
        "submitted_title": "📥 Yangi anketa",
    },
    "ru": {
        "welcome": "Здравствуйте! Добро пожаловать в компанию BUTTON.\nВыберите язык:",
        "choose_branch": "Выберите филиал:",
        "choose_vacancy": "Выберите вакансию:",
        "branch_info": "Выбранный филиал: <b>{branch}</b>\n\n📍 Локация: {map_url}",
        "start_form": "Теперь заполним короткую анкету.",
        "full_name": "Введите имя и фамилию:",
        "birth_year": "Введите год рождения:",
        "phone": "Отправьте номер телефона или введите его:",
        "address": "Введите адрес проживания:",
        "marital": "Выберите семейное положение:",
        "education": "Выберите образование:",
        "is_studying": "Вы сейчас учитесь?",
        "study_type": "Выберите форму обучения:",
        "experience": "Есть ли у вас опыт работы?",
        "last_job": "Напишите последнее место работы:",
        "last_position": "Напишите последнюю должность:",
        "start_date": "Когда можете выйти на работу?",
        "consent": "Вы согласны на обработку ваших данных компанией BUTTON?",
        "thanks": "Спасибо! Ваша анкета принята ✅\nС вами скоро свяжутся.",
        "cancelled": "Процесс отменён.",
        "invalid_year": "Пожалуйста, введите корректный год рождения. Например: 1999",
        "invalid_phone": "Пожалуйста, отправьте корректный номер телефона.",
        "choose_option": "Пожалуйста, выберите один из вариантов кнопкой.",
        "send_contact": "📱 Отправить номер",
        "consent_yes": "Согласен ✅",
        "consent_no": "Отмена ❌",
        "yes": "Да",
        "no": "Нет",
        "btn_restart": "🔄 Начать заново",
        "btn_cancel": "❌ Отмена",
        "submitted_title": "📥 Новая анкета",
    },
}

BRANCHES = {
    "chilonzor_andalus": {
        "name_uz": "Chilonzor — Andalus",
        "name_ru": "Чиланзар — Andalus",
        "map_url": "https://maps.app.goo.gl/oYSJC9WdxCHJJCi9A",
        "vacancies": ["seller", "cashier", "security", "cleaner"],
    },
    "chilonzor_integro": {
        "name_uz": "Chilonzor — Integro",
        "name_ru": "Чиланзар — Integro",
        "map_url": "https://maps.app.goo.gl/qkpAoaWKAMcnsNT68",
        "vacancies": ["seller", "cashier", "security", "cleaner"],
    },
    "beruniy_korzinka": {
        "name_uz": "Beruniy — Korzinka",
        "name_ru": "Беруний — Korzinka",
        "map_url": "https://maps.app.goo.gl/kJG4gRnn6H5aDm6F8",
        "vacancies": ["seller", "cashier", "security", "cleaner"],
    },
    "risoviy_magnit": {
        "name_uz": "Risoviy bozor — Magnit",
        "name_ru": "Рисовый базар — Magnit",
        "map_url": "https://maps.app.goo.gl/SYLeo8T8hLAQ92s76",
        "vacancies": ["seller", "cashier", "security", "cleaner"],
    },
    "shaxriston_korzinka": {
        "name_uz": "Shaxriston — Korzinka",
        "name_ru": "Шахристон — Korzinka",
        "map_url": "https://maps.app.goo.gl/wtqnQgRQKhhksgQ38",
        "vacancies": ["seller", "cashier", "security", "cleaner"],
    },
    "shayxontohur_makon": {
        "name_uz": "Shayxontohur — Makon",
        "name_ru": "Шайхонтохур — Makon",
        "map_url": "https://maps.app.goo.gl/MCsg4vuu8fiXYm8N7",
        "vacancies": ["seller", "cashier", "security", "cleaner", "storekeeper"],
    },
    "office_andalus": {
        "name_uz": "Ofis — Andalus",
        "name_ru": "Офис — Andalus",
        "map_url": "https://maps.app.goo.gl/GDgu8ar46ffh1zb46",
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

MARITAL = {
    "single": {"uz": "Bo‘ydoq / Turmush qurmagan", "ru": "Холост / Не замужем"},
    "married": {"uz": "Uylangan / Turmushga chiqqan", "ru": "Женат / Замужем"},
    "divorced": {"uz": "Ajrashgan", "ru": "Разведён(а)"},
}

EDUCATION = {
    "secondary": {"uz": "O‘rta", "ru": "Среднее"},
    "special": {"uz": "O‘rta maxsus", "ru": "Среднее специальное"},
    "higher": {"uz": "Oliy", "ru": "Высшее"},
    "unfinished_higher": {"uz": "Tugallanmagan oliy", "ru": "Неоконченное высшее"},
}

STUDY_TYPE = {
    "day": {"uz": "Kunduzgi", "ru": "Очное"},
    "evening": {"uz": "Kechki", "ru": "Вечернее"},
    "external": {"uz": "Sirtqi", "ru": "Заочное"},
}

# =========================
# FSM
# =========================

class CandidateForm(StatesGroup):
    language = State()
    branch = State()
    vacancy = State()
    full_name = State()
    birth_year = State()
    phone = State()
    address = State()
    marital = State()
    education = State()
    is_studying = State()
    study_type = State()
    experience = State()
    last_job = State()
    last_position = State()
    start_date = State()
    consent = State()

# =========================
# HELPERS
# =========================

def get_lang_text(lang: str, key: str) -> str:
    return LANG_TEXT[lang][key]

def branch_title(branch_key: str, lang: str) -> str:
    return BRANCHES[branch_key]["name_uz"] if lang == "uz" else BRANCHES[branch_key]["name_ru"]

def vacancy_title(vacancy_key: str, lang: str) -> str:
    return VACANCIES[vacancy_key][lang]

def inline_lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="O‘zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="Русский", callback_data="lang_ru")],
    ])

def branches_keyboard(lang: str) -> InlineKeyboardMarkup:
    buttons = []
    for key, item in BRANCHES.items():
        title = item["name_uz"] if lang == "uz" else item["name_ru"]
        buttons.append([InlineKeyboardButton(text=title, callback_data=f"branch_{key}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def vacancies_keyboard(lang: str, branch_key: str) -> InlineKeyboardMarkup:
    buttons = []
    for vacancy_key in BRANCHES[branch_key]["vacancies"]:
        buttons.append([
            InlineKeyboardButton(
                text=vacancy_title(vacancy_key, lang),
                callback_data=f"vacancy_{vacancy_key}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def marital_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=MARITAL["single"][lang], callback_data="marital_single")],
        [InlineKeyboardButton(text=MARITAL["married"][lang], callback_data="marital_married")],
        [InlineKeyboardButton(text=MARITAL["divorced"][lang], callback_data="marital_divorced")],
    ])

def education_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=EDUCATION["secondary"][lang], callback_data="edu_secondary")],
        [InlineKeyboardButton(text=EDUCATION["special"][lang], callback_data="edu_special")],
        [InlineKeyboardButton(text=EDUCATION["higher"][lang], callback_data="edu_higher")],
        [InlineKeyboardButton(text=EDUCATION["unfinished_higher"][lang], callback_data="edu_unfinished_higher")],
    ])

def yes_no_keyboard(lang: str, prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_lang_text(lang, "yes"), callback_data=f"{prefix}_yes"),
            InlineKeyboardButton(text=get_lang_text(lang, "no"), callback_data=f"{prefix}_no"),
        ]
    ])

def study_type_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=STUDY_TYPE["day"][lang], callback_data="study_day")],
        [InlineKeyboardButton(text=STUDY_TYPE["evening"][lang], callback_data="study_evening")],
        [InlineKeyboardButton(text=STUDY_TYPE["external"][lang], callback_data="study_external")],
    ])

def consent_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_lang_text(lang, "consent_yes"), callback_data="consent_yes")],
        [InlineKeyboardButton(text=get_lang_text(lang, "consent_no"), callback_data="consent_no")],
    ])

def contact_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_lang_text(lang, "send_contact"), request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def restart_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_lang_text(lang, "btn_restart"))],
            [KeyboardButton(text=get_lang_text(lang, "btn_cancel"))],
        ],
        resize_keyboard=True
    )

def normalize_phone(phone: str) -> str:
    return phone.strip().replace(" ", "").replace("-", "")

def valid_phone(phone: str) -> bool:
    phone = normalize_phone(phone)
    return phone.startswith("+") and len(phone) >= 9

def format_value(value: str) -> str:
    return value if value else "-"

async def start_form_flow(callback: CallbackQuery, state: FSMContext, lang: str, branch_key: str, vacancy_key: str):
    branch_name = branch_title(branch_key, lang)
    map_url = BRANCHES[branch_key]["map_url"]

    await callback.message.edit_text(
        get_lang_text(lang, "branch_info").format(branch=branch_name, map_url=map_url),
        parse_mode=ParseMode.HTML
    )
    await callback.message.answer(get_lang_text(lang, "start_form"))
    await callback.message.answer(get_lang_text(lang, "full_name"))
    await state.set_state(CandidateForm.full_name)

def get_readable_data(data: Dict[str, Any]) -> str:
    lang = data["lang"]

    marital_text = MARITAL.get(data.get("marital", ""), {}).get(lang, data.get("marital", "-"))
    education_text = EDUCATION.get(data.get("education", ""), {}).get(lang, data.get("education", "-"))
    study_type_text = STUDY_TYPE.get(data.get("study_type", ""), {}).get(lang, data.get("study_type", "-"))

    yes_text = get_lang_text(lang, "yes")
    no_text = get_lang_text(lang, "no")

    experience_text = yes_text if data.get("experience") == "yes" else no_text
    studying_text = yes_text if data.get("is_studying") == "yes" else no_text

    branch_name = branch_title(data["branch"], lang)
    vacancy_name = vacancy_title(data["vacancy"], lang)
    map_url = BRANCHES[data["branch"]]["map_url"]

    return (
        f"<b>{get_lang_text(lang, 'submitted_title')}</b>\n\n"
        f"<b>Til / Язык:</b> {lang}\n"
        f"<b>Filial / Филиал:</b> {branch_name}\n"
        f"<b>Vakansiya / Вакансия:</b> {vacancy_name}\n"
        f"<b>Lokatsiya:</b> {map_url}\n\n"
        f"<b>1. F.I.Sh / ФИО:</b> {format_value(data.get('full_name'))}\n"
        f"<b>2. Tug‘ilgan yil / Год рождения:</b> {format_value(data.get('birth_year'))}\n"
        f"<b>3. Telefon / Телефон:</b> {format_value(data.get('phone'))}\n"
        f"<b>4. Manzil / Адрес:</b> {format_value(data.get('address'))}\n"
        f"<b>5. Oilaviy holati / Семейное положение:</b> {format_value(marital_text)}\n"
        f"<b>6. Ma'lumoti / Образование:</b> {format_value(education_text)}\n"
        f"<b>7. O‘qiydimi / Учится:</b> {studying_text}\n"
        f"<b>8. O‘qish turi / Форма обучения:</b> {format_value(study_type_text)}\n"
        f"<b>9. Tajriba / Опыт работы:</b> {experience_text}\n"
        f"<b>10. Oxirgi ish joyi / Последнее место работы:</b> {format_value(data.get('last_job'))}\n"
        f"<b>11. Oxirgi lavozimi / Последняя должность:</b> {format_value(data.get('last_position'))}\n"
        f"<b>12. Qachondan chiqadi / Когда может выйти:</b> {format_value(data.get('start_date'))}\n"
    )

# =========================
# HANDLERS
# =========================

dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(CandidateForm.language)
    await message.answer(
        "Assalomu alaykum / Здравствуйте!\nBUTTON kompaniyasiga xush kelibsiz.\nВыберите язык / Tilni tanlang:",
        reply_markup=inline_lang_keyboard()
    )

@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Jarayon bekor qilindi / Процесс отменён.", reply_markup=ReplyKeyboardRemove())

@dp.message(F.text.in_(["🔄 Qayta boshlash", "🔄 Начать заново"]))
async def restart_handler(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(CandidateForm.language)
    await message.answer(
        "Assalomu alaykum / Здравствуйте!\nBUTTON kompaniyasiga xush kelibsiz.\nВыберите язык / Tilni tanlang:",
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer(
        "Выберите язык / Tilni tanlang:",
        reply_markup=inline_lang_keyboard()
    )

@dp.message(F.text.in_(["❌ Bekor qilish", "❌ Отмена"]))
async def cancel_text_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Jarayon bekor qilindi / Процесс отменён.", reply_markup=ReplyKeyboardRemove())

@dp.callback_query(F.data.startswith("lang_"))
async def choose_language(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    await state.update_data(lang=lang)
    await state.set_state(CandidateForm.branch)

    await callback.message.edit_text(
        get_lang_text(lang, "choose_branch"),
        reply_markup=branches_keyboard(lang)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("branch_"))
async def choose_branch(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    branch_key = callback.data.replace("branch_", "")

    await state.update_data(branch=branch_key)
    await state.set_state(CandidateForm.vacancy)

    await callback.message.edit_text(
        get_lang_text(lang, "choose_vacancy"),
        reply_markup=vacancies_keyboard(lang, branch_key)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("vacancy_"))
async def choose_vacancy(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    branch_key = data["branch"]
    vacancy_key = callback.data.replace("vacancy_", "")

    await state.update_data(vacancy=vacancy_key)
    await start_form_flow(callback, state, lang, branch_key, vacancy_key)
    await callback.answer()

@dp.message(CandidateForm.full_name)
async def form_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    data = await state.get_data()
    lang = data["lang"]

    await state.set_state(CandidateForm.birth_year)
    await message.answer(get_lang_text(lang, "birth_year"))

@dp.message(CandidateForm.birth_year)
async def form_birth_year(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    text = message.text.strip()

    if not text.isdigit() or len(text) != 4 or int(text) < 1950 or int(text) > 2010:
        await message.answer(get_lang_text(lang, "invalid_year"))
        return

    await state.update_data(birth_year=text)
    await state.set_state(CandidateForm.phone)
    await message.answer(
        get_lang_text(lang, "phone"),
        reply_markup=contact_keyboard(lang)
    )

@dp.message(CandidateForm.phone, F.contact)
async def form_phone_contact(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]

    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone

    await state.update_data(phone=phone)
    await state.set_state(CandidateForm.address)
    await message.answer(
        get_lang_text(lang, "address"),
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(CandidateForm.phone)
async def form_phone_text(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]

    phone = normalize_phone(message.text)
    if not valid_phone(phone):
        await message.answer(get_lang_text(lang, "invalid_phone"))
        return

    await state.update_data(phone=phone)
    await state.set_state(CandidateForm.address)
    await message.answer(
        get_lang_text(lang, "address"),
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(CandidateForm.address)
async def form_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    data = await state.get_data()
    lang = data["lang"]

    await state.set_state(CandidateForm.marital)
    await message.answer(
        get_lang_text(lang, "marital"),
        reply_markup=marital_keyboard(lang)
    )

@dp.callback_query(CandidateForm.marital, F.data.startswith("marital_"))
async def form_marital(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]

    marital_key = callback.data.replace("marital_", "")
    await state.update_data(marital=marital_key)
    await state.set_state(CandidateForm.education)

    await callback.message.edit_text(
        get_lang_text(lang, "education"),
        reply_markup=education_keyboard(lang)
    )
    await callback.answer()

@dp.callback_query(CandidateForm.education, F.data.startswith("edu_"))
async def form_education(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]

    edu_key = callback.data.replace("edu_", "")
    await state.update_data(education=edu_key)
    await state.set_state(CandidateForm.is_studying)

    await callback.message.edit_text(
        get_lang_text(lang, "is_studying"),
        reply_markup=yes_no_keyboard(lang, "studying")
    )
    await callback.answer()

@dp.callback_query(CandidateForm.is_studying, F.data.startswith("studying_"))
async def form_is_studying(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]

    answer = callback.data.replace("studying_", "")
    await state.update_data(is_studying=answer)

    if answer == "yes":
        await state.set_state(CandidateForm.study_type)
        await callback.message.edit_text(
            get_lang_text(lang, "study_type"),
            reply_markup=study_type_keyboard(lang)
        )
    else:
        await state.update_data(study_type="-")
        await state.set_state(CandidateForm.experience)
        await callback.message.edit_text(
            get_lang_text(lang, "experience"),
            reply_markup=yes_no_keyboard(lang, "exp")
        )
    await callback.answer()

@dp.callback_query(CandidateForm.study_type, F.data.startswith("study_"))
async def form_study_type(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]

    study_key = callback.data.replace("study_", "")
    await state.update_data(study_type=study_key)
    await state.set_state(CandidateForm.experience)

    await callback.message.edit_text(
        get_lang_text(lang, "experience"),
        reply_markup=yes_no_keyboard(lang, "exp")
    )
    await callback.answer()

@dp.callback_query(CandidateForm.experience, F.data.startswith("exp_"))
async def form_experience(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]

    answer = callback.data.replace("exp_", "")
    await state.update_data(experience=answer)

    if answer == "yes":
        await state.set_state(CandidateForm.last_job)
        await callback.message.edit_text(get_lang_text(lang, "last_job"))
    else:
        await state.update_data(last_job="-", last_position="-")
        await state.set_state(CandidateForm.start_date)
        await callback.message.edit_text(get_lang_text(lang, "start_date"))
    await callback.answer()

@dp.message(CandidateForm.last_job)
async def form_last_job(message: Message, state: FSMContext):
    await state.update_data(last_job=message.text.strip())
    data = await state.get_data()
    lang = data["lang"]

    await state.set_state(CandidateForm.last_position)
    await message.answer(get_lang_text(lang, "last_position"))

@dp.message(CandidateForm.last_position)
async def form_last_position(message: Message, state: FSMContext):
    await state.update_data(last_position=message.text.strip())
    data = await state.get_data()
    lang = data["lang"]

    await state.set_state(CandidateForm.start_date)
    await message.answer(get_lang_text(lang, "start_date"))

@dp.message(CandidateForm.start_date)
async def form_start_date(message: Message, state: FSMContext):
    await state.update_data(start_date=message.text.strip())
    data = await state.get_data()
    lang = data["lang"]

    await state.set_state(CandidateForm.consent)
    await message.answer(
        get_lang_text(lang, "consent"),
        reply_markup=consent_keyboard(lang)
    )

@dp.callback_query(CandidateForm.consent, F.data == "consent_yes")
async def consent_yes(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    lang = data["lang"]

    text = get_readable_data(data)

    try:
        await bot.send_message(
            chat_id=HR_CHAT_ID,
            text=text,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logging.exception("HR chatga yuborishda xatolik: %s", e)
        await callback.message.answer("Xatolik yuz berdi. HR_CHAT_ID yoki bot huquqlarini tekshiring.")
        await callback.answer()
        return

    await callback.message.edit_text(get_lang_text(lang, "thanks"))
    await callback.message.answer(
        get_lang_text(lang, "thanks"),
        reply_markup=restart_keyboard(lang)
    )
    await state.clear()
    await callback.answer()

@dp.callback_query(CandidateForm.consent, F.data == "consent_no")
async def consent_no(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    await state.clear()
    await callback.message.edit_text(get_lang_text(lang, "cancelled"))
    await callback.message.answer(
        get_lang_text(lang, "cancelled"),
        reply_markup=restart_keyboard(lang)
    )
    await callback.answer()

# =========================
# FALLBACKS
# =========================

@dp.callback_query()
async def unknown_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await callback.answer(get_lang_text(lang, "choose_option"), show_alert=False)

@dp.message()
async def fallback_message(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Botni ishga tushirish uchun /start bosing.")
        return

    data = await state.get_data()
    lang = data.get("lang", "uz")
    await message.answer(get_lang_text(lang, "choose_option"))

# =========================
# MAIN
# =========================

async def main():
    if BOT_TOKEN == "PASTE_YOUR_BOT_TOKEN_HERE":
        raise ValueError("BOT_TOKEN ni kiriting.")
    if HR_CHAT_ID == -1001234567890:
        raise ValueError("HR_CHAT_ID ni kiriting.")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
