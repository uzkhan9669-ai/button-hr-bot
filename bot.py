import asyncio
import logging
import os
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

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("8731952281:AAHlcIryCTRTF1ZBG11LFQdGfUv4mr29BgA")
HR_CHAT_ID = os.getenv("5208914641")

# =========================
# TEXTS
# =========================

TEXTS = {
    "uz": {
        "welcome": "Assalomu alaykum! BUTTON kompaniyasiga xush kelibsiz.\nTilni tanlang:",
        "choose_branch": "Filialni tanlang:",
        "choose_vacancy": "Vakansiyani tanlang:",
        "branch_info": "Tanlangan filial: <b>{branch}</b>\n📍 Lokatsiya: {map_url}",
        "start_form": "Anketani to‘ldirishni boshlaymiz.",
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
        "invalid_year": "Iltimos, to‘g‘ri yil kiriting. Masalan: 2000",
        "invalid_phone": "Iltimos, telefon raqamni to‘g‘ri yuboring.",
        "choose_option": "Iltimos, tugmalardan birini tanlang.",
        "send_contact": "📱 Raqamni yuborish",
        "yes": "Ha",
        "no": "Yo‘q",
        "consent_yes": "Roziman ✅",
        "consent_no": "Bekor qilish ❌",
        "restart": "🔄 Qayta boshlash",
        "cancel": "❌ Bekor qilish",
    },
    "ru": {
        "welcome": "Здравствуйте! Добро пожаловать в компанию BUTTON.\nВыберите язык:",
        "choose_branch": "Выберите филиал:",
        "choose_vacancy": "Выберите вакансию:",
        "branch_info": "Выбранный филиал: <b>{branch}</b>\n📍 Локация: {map_url}",
        "start_form": "Начинаем заполнение анкеты.",
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
        "invalid_year": "Пожалуйста, введите корректный год. Например: 2000",
        "invalid_phone": "Пожалуйста, введите корректный номер телефона.",
        "choose_option": "Пожалуйста, выберите один из вариантов.",
        "send_contact": "📱 Отправить номер",
        "yes": "Да",
        "no": "Нет",
        "consent_yes": "Согласен ✅",
        "consent_no": "Отмена ❌",
        "restart": "🔄 Начать заново",
        "cancel": "❌ Отмена",
    },
}

BRANCHES = {
    "chilonzor_andalus": {
        "uz": "Chilonzor — Andalus",
        "ru": "Чиланзар — Andalus",
        "map": "https://maps.app.goo.gl/oYSJC9WdxCHJJCi9A",
        "vacancies": ["seller", "cashier", "security", "cleaner"],
    },
    "chilonzor_integro": {
        "uz": "Chilonzor — Integro",
        "ru": "Чиланзар — Integro",
        "map": "https://maps.app.goo.gl/qkpAoaWKAMcnsNT68",
        "vacancies": ["seller", "cashier", "security", "cleaner"],
    },
    "beruniy_korzinka": {
        "uz": "Beruniy — Korzinka",
        "ru": "Беруний — Korzinka",
        "map": "https://maps.app.goo.gl/kJG4gRnn6H5aDm6F8",
        "vacancies": ["seller", "cashier", "security", "cleaner"],
    },
    "risoviy_magnit": {
        "uz": "Risoviy bozor — Magnit",
        "ru": "Рисовый базар — Magnit",
        "map": "https://maps.app.goo.gl/SYLeo8T8hLAQ92s76",
        "vacancies": ["seller", "cashier", "security", "cleaner"],
    },
    "shaxriston_korzinka": {
        "uz": "Shaxriston — Korzinka",
        "ru": "Шахристон — Korzinka",
        "map": "https://maps.app.goo.gl/wtqnQgRQKhhksgQ38",
        "vacancies": ["seller", "cashier", "security", "cleaner"],
    },
    "shayxontohur_makon": {
        "uz": "Shayxontohur — Makon",
        "ru": "Шайхонтохур — Makon",
        "map": "https://maps.app.goo.gl/MCsg4vuu8fiXYm8N7",
        "vacancies": ["seller", "cashier", "security", "cleaner", "storekeeper"],
    },
    "office_andalus": {
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

def t(lang: str, key: str) -> str:
    return TEXTS[lang][key]

def branch_name(branch_key: str, lang: str) -> str:
    return BRANCHES[branch_key][lang]

def vacancy_name(vacancy_key: str, lang: str) -> str:
    return VACANCIES[vacancy_key][lang]

def normalize_phone(phone: str) -> str:
    return phone.strip().replace(" ", "").replace("-", "")

def valid_phone(phone: str) -> bool:
    phone = normalize_phone(phone)
    return len(phone) >= 9 and (phone.startswith("+") or phone[0].isdigit())

def lang_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="O‘zbekcha", callback_data="lang_uz")],
            [InlineKeyboardButton(text="Русский", callback_data="lang_ru")],
        ]
    )

def branch_kb(lang: str):
    buttons = []
    for key, item in BRANCHES.items():
        buttons.append([InlineKeyboardButton(text=item[lang], callback_data=f"branch:{key}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def vacancy_kb(lang: str, branch_key: str):
    buttons = []
    for vacancy in BRANCHES[branch_key]["vacancies"]:
        buttons.append([InlineKeyboardButton(text=VACANCIES[vacancy][lang], callback_data=f"vacancy:{vacancy}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def marital_kb(lang: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=MARITAL["single"][lang], callback_data="marital:single")],
        [InlineKeyboardButton(text=MARITAL["married"][lang], callback_data="marital:married")],
        [InlineKeyboardButton(text=MARITAL["divorced"][lang], callback_data="marital:divorced")],
    ])

def education_kb(lang: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=EDUCATION["secondary"][lang], callback_data="education:secondary")],
        [InlineKeyboardButton(text=EDUCATION["special"][lang], callback_data="education:special")],
        [InlineKeyboardButton(text=EDUCATION["higher"][lang], callback_data="education:higher")],
        [InlineKeyboardButton(text=EDUCATION["unfinished_higher"][lang], callback_data="education:unfinished_higher")],
    ])

def yes_no_kb(lang: str, prefix: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t(lang, "yes"), callback_data=f"{prefix}:yes"),
            InlineKeyboardButton(text=t(lang, "no"), callback_data=f"{prefix}:no"),
        ]
    ])

def study_type_kb(lang: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=STUDY_TYPE["day"][lang], callback_data="study_type:day")],
        [InlineKeyboardButton(text=STUDY_TYPE["evening"][lang], callback_data="study_type:evening")],
        [InlineKeyboardButton(text=STUDY_TYPE["external"][lang], callback_data="study_type:external")],
    ])

def consent_kb(lang: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "consent_yes"), callback_data="consent:yes")],
        [InlineKeyboardButton(text=t(lang, "consent_no"), callback_data="consent:no")],
    ])

def contact_kb(lang: str):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(lang, "send_contact"), request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def restart_kb(lang: str):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "restart"))],
            [KeyboardButton(text=t(lang, "cancel"))],
        ],
        resize_keyboard=True
    )

def build_result_text(data: Dict[str, Any]) -> str:
    lang = data["lang"]
    studying = t(lang, "yes") if data.get("is_studying") == "yes" else t(lang, "no")
    experience = t(lang, "yes") if data.get("experience") == "yes" else t(lang, "no")

    marital_text = MARITAL.get(data.get("marital"), {}).get(lang, "-")
    education_text = EDUCATION.get(data.get("education"), {}).get(lang, "-")
    study_type_text = STUDY_TYPE.get(data.get("study_type"), {}).get(lang, "-") if data.get("study_type") != "-" else "-"

    return (
        f"<b>📥 Yangi anketa / Новая анкета</b>\n\n"
        f"<b>Til / Язык:</b> {lang}\n"
        f"<b>Filial / Филиал:</b> {branch_name(data['branch'], lang)}\n"
        f"<b>Vakansiya / Вакансия:</b> {vacancy_name(data['vacancy'], lang)}\n"
        f"<b>Lokatsiya:</b> {BRANCHES[data['branch']]['map']}\n\n"
        f"<b>F.I.Sh:</b> {data.get('full_name', '-')}\n"
        f"<b>Tug‘ilgan yil:</b> {data.get('birth_year', '-')}\n"
        f"<b>Telefon:</b> {data.get('phone', '-')}\n"
        f"<b>Manzil:</b> {data.get('address', '-')}\n"
        f"<b>Oilaviy holati:</b> {marital_text}\n"
        f"<b>Ma'lumoti:</b> {education_text}\n"
        f"<b>O‘qiydimi:</b> {studying}\n"
        f"<b>O‘qish turi:</b> {study_type_text}\n"
        f"<b>Tajriba:</b> {experience}\n"
        f"<b>Oxirgi ish joyi:</b> {data.get('last_job', '-')}\n"
        f"<b>Oxirgi lavozimi:</b> {data.get('last_position', '-')}\n"
        f"<b>Ish boshlash vaqti:</b> {data.get('start_date', '-')}\n"
    )


dp = Dispatcher(storage=MemoryStorage())


# =========================
# COMMANDS
# =========================

@dp.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(CandidateForm.language)
    await message.answer(
        "Assalomu alaykum / Здравствуйте!\nBUTTON kompaniyasiga xush kelibsiz.",
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer("Выберите язык / Tilni tanlang:", reply_markup=lang_kb())

@dp.message(Command("cancel"))
async def cancel_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Jarayon bekor qilindi / Процесс отменён.", reply_markup=ReplyKeyboardRemove())


# =========================
# RESTART / CANCEL TEXT
# =========================

@dp.message(F.text.in_(["🔄 Qayta boshlash", "🔄 Начать заново"]))
async def restart_handler(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(CandidateForm.language)
    await message.answer("Выберите язык / Tilni tanlang:", reply_markup=ReplyKeyboardRemove())
    await message.answer("Til / Язык:", reply_markup=lang_kb())

@dp.message(F.text.in_(["❌ Bekor qilish", "❌ Отмена"]))
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Jarayon bekor qilindi / Процесс отменён.", reply_markup=ReplyKeyboardRemove())


# =========================
# LANGUAGE
# =========================

@dp.callback_query(F.data.startswith("lang_"))
async def select_language(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    await state.update_data(lang=lang)
    await state.set_state(CandidateForm.branch)
    await callback.message.edit_text(t(lang, "choose_branch"), reply_markup=branch_kb(lang))
    await callback.answer()


# =========================
# BRANCH
# =========================

@dp.callback_query(F.data.startswith("branch:"))
async def select_branch(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    branch_key = callback.data.split(":")[1]

    await state.update_data(branch=branch_key)
    await state.set_state(CandidateForm.vacancy)
    await callback.message.edit_text(t(lang, "choose_vacancy"), reply_markup=vacancy_kb(lang, branch_key))
    await callback.answer()


# =========================
# VACANCY
# =========================

@dp.callback_query(F.data.startswith("vacancy:"))
async def select_vacancy(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    vacancy_key = callback.data.split(":")[1]
    branch_key = data["branch"]

    await state.update_data(vacancy=vacancy_key)

    await callback.message.edit_text(
        t(lang, "branch_info").format(
            branch=branch_name(branch_key, lang),
            map_url=BRANCHES[branch_key]["map"]
        )
    )
    await callback.message.answer(t(lang, "start_form"))
    await callback.message.answer(t(lang, "full_name"))
    await state.set_state(CandidateForm.full_name)
    await callback.answer()


# =========================
# FORM
# =========================

@dp.message(CandidateForm.full_name)
async def form_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=(message.text or "").strip())
    data = await state.get_data()
    await state.set_state(CandidateForm.birth_year)
    await message.answer(t(data["lang"], "birth_year"))

@dp.message(CandidateForm.birth_year)
async def form_birth_year(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    text = (message.text or "").strip()

    if not text.isdigit() or len(text) != 4 or int(text) < 1950 or int(text) > 2010:
        await message.answer(t(lang, "invalid_year"))
        return

    await state.update_data(birth_year=text)
    await state.set_state(CandidateForm.phone)
    await message.answer(t(lang, "phone"), reply_markup=contact_kb(lang))

@dp.message(CandidateForm.phone, F.contact)
async def form_phone_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone

    await state.update_data(phone=phone)
    data = await state.get_data()
    await state.set_state(CandidateForm.address)
    await message.answer(t(data["lang"], "address"), reply_markup=ReplyKeyboardRemove())

@dp.message(CandidateForm.phone)
async def form_phone_text(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    phone = normalize_phone(message.text or "")

    if not valid_phone(phone):
        await message.answer(t(lang, "invalid_phone"))
        return

    if not phone.startswith("+") and phone[0].isdigit():
        phone = "+" + phone

    await state.update_data(phone=phone)
    await state.set_state(CandidateForm.address)
    await message.answer(t(lang, "address"), reply_markup=ReplyKeyboardRemove())

@dp.message(CandidateForm.address)
async def form_address(message: Message, state: FSMContext):
    await state.update_data(address=(message.text or "").strip())
    data = await state.get_data()
    await state.set_state(CandidateForm.marital)
    await message.answer(t(data["lang"], "marital"), reply_markup=marital_kb(data["lang"]))

@dp.callback_query(CandidateForm.marital, F.data.startswith("marital:"))
async def form_marital(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split(":")[1]
    await state.update_data(marital=key)
    data = await state.get_data()
    await state.set_state(CandidateForm.education)
    await callback.message.edit_text(t(data["lang"], "education"), reply_markup=education_kb(data["lang"]))
    await callback.answer()

@dp.callback_query(CandidateForm.education, F.data.startswith("education:"))
async def form_education(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split(":")[1]
    await state.update_data(education=key)
    data = await state.get_data()
    await state.set_state(CandidateForm.is_studying)
    await callback.message.edit_text(t(data["lang"], "is_studying"), reply_markup=yes_no_kb(data["lang"], "studying"))
    await callback.answer()

@dp.callback_query(CandidateForm.is_studying, F.data.startswith("studying:"))
async def form_is_studying(callback: CallbackQuery, state: FSMContext):
    answer = callback.data.split(":")[1]
    await state.update_data(is_studying=answer)
    data = await state.get_data()
    lang = data["lang"]

    if answer == "yes":
        await state.set_state(CandidateForm.study_type)
        await callback.message.edit_text(t(lang, "study_type"), reply_markup=study_type_kb(lang))
    else:
        await state.update_data(study_type="-")
        await state.set_state(CandidateForm.experience)
        await callback.message.edit_text(t(lang, "experience"), reply_markup=yes_no_kb(lang, "experience"))
    await callback.answer()

@dp.callback_query(CandidateForm.study_type, F.data.startswith("study_type:"))
async def form_study_type(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split(":")[1]
    await state.update_data(study_type=key)
    data = await state.get_data()
    lang = data["lang"]

    await state.set_state(CandidateForm.experience)
    await callback.message.edit_text(t(lang, "experience"), reply_markup=yes_no_kb(lang, "experience"))
    await callback.answer()

@dp.callback_query(CandidateForm.experience, F.data.startswith("experience:"))
async def form_experience(callback: CallbackQuery, state: FSMContext):
    answer = callback.data.split(":")[1]
    await state.update_data(experience=answer)
    data = await state.get_data()
    lang = data["lang"]

    if answer == "yes":
        await state.set_state(CandidateForm.last_job)
        await callback.message.edit_text(t(lang, "last_job"))
    else:
        await state.update_data(last_job="-", last_position="-")
        await state.set_state(CandidateForm.start_date)
        await callback.message.edit_text(t(lang, "start_date"))
    await callback.answer()

@dp.message(CandidateForm.last_job)
async def form_last_job(message: Message, state: FSMContext):
    await state.update_data(last_job=(message.text or "").strip())
    data = await state.get_data()
    await state.set_state(CandidateForm.last_position)
    await message.answer(t(data["lang"], "last_position"))

@dp.message(CandidateForm.last_position)
async def form_last_position(message: Message, state: FSMContext):
    await state.update_data(last_position=(message.text or "").strip())
    data = await state.get_data()
    await state.set_state(CandidateForm.start_date)
    await message.answer(t(data["lang"], "start_date"))

@dp.message(CandidateForm.start_date)
async def form_start_date(message: Message, state: FSMContext):
    await state.update_data(start_date=(message.text or "").strip())
    data = await state.get_data()
    await state.set_state(CandidateForm.consent)
    await message.answer(t(data["lang"], "consent"), reply_markup=consent_kb(data["lang"]))


# =========================
# CONSENT
# =========================

@dp.callback_query(CandidateForm.consent, F.data == "consent:yes")
async def consent_yes(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    lang = data["lang"]

    try:
        chat_id = int(HR_CHAT_ID)
        await bot.send_message(chat_id=chat_id, text=build_result_text(data))
    except Exception as e:
        logging.exception("HR ga yuborishda xatolik: %s", e)
        await callback.message.answer(f"Xatolik yuz berdi: {e}")
        await callback.answer()
        return

    await callback.message.edit_text(t(lang, "thanks"))
    await callback.message.answer(t(lang, "thanks"), reply_markup=restart_kb(lang))
    await state.clear()
    await callback.answer()

@dp.callback_query(CandidateForm.consent, F.data == "consent:no")
async def consent_no(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.clear()
    await callback.message.edit_text(t(lang, "cancelled"))
    await callback.message.answer(t(lang, "cancelled"), reply_markup=restart_kb(lang))
    await callback.answer()


# =========================
# FALLBACKS
# =========================

@dp.callback_query()
async def fallback_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await callback.answer(t(lang, "choose_option"))

@dp.message()
async def fallback_message(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if not current_state:
        await message.answer("Botni ishga tushirish uchun /start bosing.")
        return

    data = await state.get_data()
    lang = data.get("lang", "uz")
    await message.answer(t(lang, "choose_option"))


# =========================
# MAIN
# =========================

async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN topilmadi. Railway Variables ga qo‘ying.")
    if not HR_CHAT_ID:
        raise ValueError("HR_CHAT_ID topilmadi. Railway Variables ga qo‘ying.")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
