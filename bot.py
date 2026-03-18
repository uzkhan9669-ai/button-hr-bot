import os
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    FSInputFile,
)

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# =========================
# SETTINGS
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
HR_CHAT_ID = os.getenv("HR_CHAT_ID")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi")
if not HR_CHAT_ID:
    raise ValueError("HR_CHAT_ID topilmadi")

HR_CHAT_ID = int(HR_CHAT_ID)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# =========================
# TEXT CONSTANTS
# =========================
BACK_TEXT_RU = "⬅️ Назад"
CANCEL_TEXT_RU = "❌ Отмена"
RESTART_TEXT_RU = "🔄 Заново"
CONSENT_TEXT_RU = "✅ Согласен"
LANG_RU = "🇷🇺 Русский язык"

BACK_TEXT_UZ = "⬅️ Orqaga"
CANCEL_TEXT_UZ = "❌ Bekor qilish"
RESTART_TEXT_UZ = "🔄 Qaytadan"
CONSENT_TEXT_UZ = "✅ Roziman"
LANG_UZ = "🇺🇿 O‘zbek tili"

FONT_REGULAR = "DejaVuSans"
FONT_BOLD = "DejaVuSansBold"

users = {}

# =========================
# DATA
# =========================
TEXTS = {
    "ru": {
        "start": "👋 Здравствуйте!\nДобро пожаловать в HR бот BUTTON.\n\nПожалуйста, выберите язык:",
        "choose_unit": "🏢 Выберите подразделение:",
        "choose_vacancy": "💼 Выберите вакансию:",
        "choose_branch": "📍 Выберите филиал:",
        "invalid_unit": "Пожалуйста, выберите подразделение кнопкой ниже.",
        "invalid_vacancy": "Пожалуйста, выберите вакансию кнопкой ниже.",
        "invalid_branch": "Пожалуйста, выберите филиал кнопкой ниже.",
        "invalid_option": "Пожалуйста, выберите вариант кнопкой ниже.",
        "branch_info": "<b>📍 Филиал:</b> {branch}\n<b>🏠 Адрес:</b> {address}\n<b>🗺 Карта:</b> {map_link}",
        "photo_request": "📸 Отправьте фото кандидата:",
        "photo_not_needed": "Сейчас фото не требуется.",
        "photo_required": "Сейчас нужно отправить фото.",
        "consent_request": "📨 Подтвердите отправку анкеты:",
        "consent_invalid": "Для отправки анкеты нажмите кнопку 'Согласен'.",
        "success": "✅ Анкета успешно отправлена.",
        "cancelled": "❌ Заявка отменена.\nДля нового заполнения нажмите /start",
        "restarted": "🔄 Заполнение начато заново.\nВыберите язык:",
        "fallback_start": "Для начала нажмите /start",
        "pdf_title": "BUTTON - Анкета кандидата",
        "pdf_caption": "📄 PDF анкета: {name}",
        "hr_title": "📥 <b>Новая анкета кандидата</b>",
        "fields": {
            "unit": "🏢 Подразделение",
            "vacancy": "💼 Вакансия",
            "branch": "📍 Филиал",
            "full_name": "👤 ФИО",
            "age": "🎂 Возраст",
            "phone": "📞 Телефон",
            "district": "🏘 Район",
            "family_status": "💍 Семейное положение",
            "education": "🎓 Образование",
            "studying_now": "📚 Сейчас учится",
            "study_place": "🏫 Где учился/учится",
            "has_experience": "🧰 Опыт работы",
            "last_job": "🏢 Последняя работа",
            "work_period": "⏳ Срок работы",
            "leaving_reason": "❓ Причина ухода",
            "applying_position": "📝 Желаемая должность",
            "preferred_branch": "📌 Удобный филиал",
            "start_date": "🚀 Когда готов выйти",
            "telegram_id": "🆔 Telegram ID",
            "username": "🔗 Username",
            "date": "📅 Дата",
        },
        "form_steps": [
            {"key": "full_name", "question": "👤 Введите имя и фамилию:", "options": None},
            {"key": "age", "question": "🎂 Введите возраст:", "options": None},
            {"key": "phone", "question": "📞 Введите номер телефона:", "options": None},
            {"key": "district", "question": "🏘 В каком районе проживаете?", "options": None},
            {"key": "family_status", "question": "💍 Выберите семейное положение:", "options": ["Холост/Не замужем", "Женат/Замужем", "Разведен(а)"]},
            {"key": "education", "question": "🎓 Выберите образование:", "options": ["Среднее", "Средне-специальное", "Высшее"]},
            {"key": "studying_now", "question": "📚 Сейчас учитесь?", "options": ["Да", "Нет"]},
            {"key": "study_place", "question": "🏫 Где учились или учитесь?", "options": None},
            {"key": "has_experience", "question": "🧰 Есть опыт работы?", "options": ["Да", "Нет"]},
            {"key": "last_job", "question": "🏢 Последнее место работы:", "options": None},
            {"key": "work_period", "question": "⏳ Сколько там работали?", "options": None},
            {"key": "leaving_reason", "question": "❓ Почему ушли с работы?", "options": None},
            {"key": "applying_position", "question": "📝 На какую должность подаете заявку?", "options": None},
            {"key": "preferred_branch", "question": "📌 Какой филиал удобен для работы?", "options": None},
            {"key": "start_date", "question": "🚀 Когда готовы выйти на работу?", "options": None},
        ],
    },
    "uz": {
        "start": "👋 Assalomu alaykum!\nBUTTON HR botiga xush kelibsiz.\n\nIltimos, tilni tanlang:",
        "choose_unit": "🏢 Bo‘limni tanlang:",
        "choose_vacancy": "💼 Vakansiyani tanlang:",
        "choose_branch": "📍 Filialni tanlang:",
        "invalid_unit": "Iltimos, bo‘limni pastdagi tugma orqali tanlang.",
        "invalid_vacancy": "Iltimos, vakansiyani pastdagi tugma orqali tanlang.",
        "invalid_branch": "Iltimos, filialni pastdagi tugma orqali tanlang.",
        "invalid_option": "Iltimos, variantni pastdagi tugma orqali tanlang.",
        "branch_info": "<b>📍 Filial:</b> {branch}\n<b>🏠 Manzil:</b> {address}\n<b>🗺 Xarita:</b> {map_link}",
        "photo_request": "📸 Nomzod rasmini yuboring:",
        "photo_not_needed": "Hozir foto kerak emas.",
        "photo_required": "Hozir foto yuborish kerak.",
        "consent_request": "📨 Anketani yuborishni tasdiqlang:",
        "consent_invalid": "Yuborish uchun 'Roziman' tugmasini bosing.",
        "success": "✅ Anketa muvaffaqiyatli yuborildi.",
        "cancelled": "❌ Ariza bekor qilindi.\nQayta boshlash uchun /start bosing",
        "restarted": "🔄 To‘ldirish qaytadan boshlandi.\nTilni tanlang:",
        "fallback_start": "Boshlash uchun /start bosing",
        "pdf_title": "BUTTON - Nomzod anketasi",
        "pdf_caption": "📄 PDF anketa: {name}",
        "hr_title": "📥 <b>Yangi nomzod anketasi</b>",
        "fields": {
            "unit": "🏢 Bo‘lim",
            "vacancy": "💼 Vakansiya",
            "branch": "📍 Filial",
            "full_name": "👤 F.I.Sh",
            "age": "🎂 Yoshi",
            "phone": "📞 Telefon",
            "district": "🏘 Tuman",
            "family_status": "💍 Oilaviy holati",
            "education": "🎓 Ma’lumoti",
            "studying_now": "📚 Hozir o‘qiyaptimi",
            "study_place": "🏫 Qayerda o‘qigan/o‘qiyapti",
            "has_experience": "🧰 Ish tajribasi",
            "last_job": "🏢 Oxirgi ish joyi",
            "work_period": "⏳ Ishlagan muddati",
            "leaving_reason": "❓ Ishdan ketish sababi",
            "applying_position": "📝 Topshirayotgan lavozimi",
            "preferred_branch": "📌 Qulay filial",
            "start_date": "🚀 Qachondan ishlay oladi",
            "telegram_id": "🆔 Telegram ID",
            "username": "🔗 Username",
            "date": "📅 Sana",
        },
        "form_steps": [
            {"key": "full_name", "question": "👤 Ism va familiyangizni kiriting:", "options": None},
            {"key": "age", "question": "🎂 Yoshingizni kiriting:", "options": None},
            {"key": "phone", "question": "📞 Telefon raqamingizni kiriting:", "options": None},
            {"key": "district", "question": "🏘 Qaysi tumanda yashaysiz?", "options": None},
            {"key": "family_status", "question": "💍 Oilaviy holatingizni tanlang:", "options": ["Bo‘ydoq/Turmush qurmagan", "Uylangan/Turmush qurgan", "Ajrashgan"]},
            {"key": "education", "question": "🎓 Ma’lumotingizni tanlang:", "options": ["O‘rta", "O‘rta maxsus", "Oliy"]},
            {"key": "studying_now", "question": "📚 Hozir o‘qiyapsizmi?", "options": ["Ha", "Yo‘q"]},
            {"key": "study_place", "question": "🏫 Qayerda o‘qigansiz yoki o‘qiyapsiz?", "options": None},
            {"key": "has_experience", "question": "🧰 Ish tajribangiz bormi?", "options": ["Ha", "Yo‘q"]},
            {"key": "last_job", "question": "🏢 Oxirgi ish joyingiz:", "options": None},
            {"key": "work_period", "question": "⏳ Qancha vaqt ishlagansiz?", "options": None},
            {"key": "leaving_reason", "question": "❓ Nega ishdan ketgansiz?", "options": None},
            {"key": "applying_position", "question": "📝 Qaysi lavozimga topshiryapsiz?", "options": None},
            {"key": "preferred_branch", "question": "📌 Qaysi filial qulay?", "options": None},
            {"key": "start_date", "question": "🚀 Qachondan ish boshlay olasiz?", "options": None},
        ],
    },
}

UNITS = {
    "ru": ["🏬 Магазины", "🏢 Офис", "📦 Склад"],
    "uz": ["🏬 Do‘konlar", "🏢 Ofis", "📦 Sklad"],
}

VACANCIES = {
    "ru": {
        "🏬 Магазины": ["🛍 Продавец-консультант", "💳 Кассир", "🛡 Охрана", "🧹 Уборщица", "🤝 Помощник"],
        "🏢 Офис": ["👨‍💼 HR"],
        "📦 Склад": ["📦 Кладовщик"],
    },
    "uz": {
        "🏬 Do‘konlar": ["🛍 Sotuvchi-maslahatchi", "💳 Kassir", "🛡 Qo‘riqlash", "🧹 Tozalik hodimasi", "🤝 Yordamchi"],
        "🏢 Ofis": ["👨‍💼 HR"],
        "📦 Sklad": ["📦 Kladovshik"],
    },
}

BRANCHES = {
    "ru": {
        "🏬 Магазины": ["Chilonzor Andalus", "Chilonzor Integro", "Beruniy Korzinka", "Risoviy bozor Magnit", "Shaxriston Korzinka"],
        "🏢 Офис": ["Ofis Andalus"],
        "📦 Склад": ["Shayxontohur Makon"],
    },
    "uz": {
        "🏬 Do‘konlar": ["Chilonzor Andalus", "Chilonzor Integro", "Beruniy Korzinka", "Risoviy bozor Magnit", "Shaxriston Korzinka"],
        "🏢 Ofis": ["Ofis Andalus"],
        "📦 Sklad": ["Shayxontohur Makon"],
    },
}

LOCATIONS = {
    "Ofis Andalus": {
        "address_ru": "г. Ташкент, Ofis Andalus",
        "address_uz": "Toshkent shahri, Ofis Andalus",
        "map": "https://maps.app.goo.gl/GDgu8ar46ffh1zb46",
    },
    "Beruniy Korzinka": {
        "address_ru": "г. Ташкент, Beruniy metro, Korzinka",
        "address_uz": "Toshkent shahri, Beruniy metro, Korzinka",
        "map": "https://maps.app.goo.gl/kJG4gRnn6H5aDm6F8",
    },
    "Chilonzor Andalus": {
        "address_ru": "г. Ташкент, Chilonzor Andalus",
        "address_uz": "Toshkent shahri, Chilonzor Andalus",
        "map": "https://maps.app.goo.gl/oYSJC9WdxCHJJCi9A",
    },
    "Risoviy bozor Magnit": {
        "address_ru": "г. Ташкент, Risoviy bozor Magnit",
        "address_uz": "Toshkent shahri, Risoviy bozor Magnit",
        "map": "https://maps.app.goo.gl/SYLeo8T8hLAQ92s76",
    },
    "Shayxontohur Makon": {
        "address_ru": "г. Ташкент, Shayxontohur Makon",
        "address_uz": "Toshkent shahri, Shayxontohur Makon",
        "map": "https://maps.app.goo.gl/MCsg4vuu8fiXYm8N7",
    },
    "Chilonzor Integro": {
        "address_ru": "г. Ташкент, Chilonzor Integro",
        "address_uz": "Toshkent shahri, Chilonzor Integro",
        "map": "https://maps.app.goo.gl/qkpAoaWKAMcnsNT68",
    },
    "Shaxriston Korzinka": {
        "address_ru": "г. Ташкент, Shaxriston Korzinka",
        "address_uz": "Toshkent shahri, Shaxriston Korzinka",
        "map": "https://maps.app.goo.gl/wtqnQgRQKhhksgQ38",
    },
}

# =========================
# KEYBOARDS
# =========================
def get_control_texts(lang: str):
    if lang == "uz":
        return BACK_TEXT_UZ, CANCEL_TEXT_UZ, RESTART_TEXT_UZ, CONSENT_TEXT_UZ
    return BACK_TEXT_RU, CANCEL_TEXT_RU, RESTART_TEXT_RU, CONSENT_TEXT_RU


def keyboard_from_options(options: list[str], lang: str, add_controls: bool = True) -> ReplyKeyboardMarkup:
    back_text, cancel_text, restart_text, _ = get_control_texts(lang)
    rows = [[KeyboardButton(text=item)] for item in options]
    if add_controls:
        rows.append(
            [
                KeyboardButton(text=back_text),
                KeyboardButton(text=cancel_text),
                KeyboardButton(text=restart_text),
            ]
        )
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def controls_only_keyboard(lang: str) -> ReplyKeyboardMarkup:
    back_text, cancel_text, restart_text, _ = get_control_texts(lang)
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text=back_text),
            KeyboardButton(text=cancel_text),
            KeyboardButton(text=restart_text),
        ]],
        resize_keyboard=True
    )


def language_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LANG_UZ), KeyboardButton(text=LANG_RU)]
        ],
        resize_keyboard=True
    )


def main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return keyboard_from_options(UNITS[lang], lang)


def consent_keyboard(lang: str) -> ReplyKeyboardMarkup:
    _, _, _, consent_text = get_control_texts(lang)
    return keyboard_from_options([consent_text], lang)


# =========================
# HELPERS
# =========================
def ensure_user(user_id: int):
    if user_id not in users:
        users[user_id] = {
            "stage": "language",
            "form_index": 0,
            "lang": None,
            "data": {},
        }


def reset_user(user_id: int):
    users[user_id] = {
        "stage": "language",
        "form_index": 0,
        "lang": None,
        "data": {},
    }


def get_lang(user_id: int) -> str:
    lang = users[user_id].get("lang")
    return lang if lang in ("ru", "uz") else "ru"


def get_current_form_step(user_id: int):
    lang = get_lang(user_id)
    idx = users[user_id]["form_index"]
    return TEXTS[lang]["form_steps"][idx]


def register_font_if_needed(font_name: str, paths: list[str]):
    try:
        pdfmetrics.getFont(font_name)
        return
    except KeyError:
        pass

    for path in paths:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont(font_name, path))
            return

    raise FileNotFoundError(f"{font_name} topilmadi")


def ensure_pdf_fonts():
    register_font_if_needed(
        FONT_REGULAR,
        [
            "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        ],
    )
    register_font_if_needed(
        FONT_BOLD,
        [
            "DejaVuSansBold.ttf",
            "DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        ],
    )


def wrap_text(text: str, max_len: int = 90) -> list[str]:
    words = str(text).split()
    if not words:
        return [""]

    lines = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_len:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def create_pdf(data: dict, tg_user_id: int, tg_username: str | None, lang: str) -> str:
    ensure_pdf_fonts()
    os.makedirs("generated", exist_ok=True)

    safe_name = "".join(
        ch for ch in data.get("full_name", "candidate")
        if ch.isalnum() or ch in (" ", "_", "-")
    ).strip().replace(" ", "_")

    if not safe_name:
        safe_name = "candidate"

    pdf_path = f"generated/{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    t = TEXTS[lang]
    labels = t["fields"]

    c = canvas.Canvas(pdf_path, pagesize=A4)
    _, height = A4
    y = height - 40

    c.setFont(FONT_BOLD, 16)
    c.drawString(40, y, t["pdf_title"])
    y -= 30

    fields = [
        (labels["unit"], data.get("unit", "-")),
        (labels["vacancy"], data.get("vacancy", "-")),
        (labels["branch"], data.get("branch", "-")),
        (labels["full_name"], data.get("full_name", "-")),
        (labels["age"], data.get("age", "-")),
        (labels["phone"], data.get("phone", "-")),
        (labels["district"], data.get("district", "-")),
        (labels["family_status"], data.get("family_status", "-")),
        (labels["education"], data.get("education", "-")),
        (labels["studying_now"], data.get("studying_now", "-")),
        (labels["study_place"], data.get("study_place", "-")),
        (labels["has_experience"], data.get("has_experience", "-")),
        (labels["last_job"], data.get("last_job", "-")),
        (labels["work_period"], data.get("work_period", "-")),
        (labels["leaving_reason"], data.get("leaving_reason", "-")),
        (labels["applying_position"], data.get("applying_position", "-")),
        (labels["preferred_branch"], data.get("preferred_branch", "-")),
        (labels["start_date"], data.get("start_date", "-")),
        (labels["telegram_id"], str(tg_user_id)),
        (labels["username"], tg_username or "-"),
        (labels["date"], datetime.now().strftime("%d.%m.%Y %H:%M:%S")),
    ]

    for label, value in fields:
        line_text = f"{label}: {value}"
        wrapped = wrap_text(line_text)
        for i, line in enumerate(wrapped):
            if y < 50:
                c.showPage()
                y = height - 40
            c.setFont(FONT_BOLD if i == 0 else FONT_REGULAR, 11)
            c.drawString(40, y, line)
            y -= 18

    c.save()
    return pdf_path


def build_text(data: dict, user: Message, lang: str) -> str:
    username = f"@{user.from_user.username}" if user.from_user.username else "-"
    labels = TEXTS[lang]["fields"]

    return (
        f"{TEXTS[lang]['hr_title']}\n\n"
        f"<b>{labels['unit']}:</b> {data.get('unit', '-')}\n"
        f"<b>{labels['vacancy']}:</b> {data.get('vacancy', '-')}\n"
        f"<b>{labels['branch']}:</b> {data.get('branch', '-')}\n\n"
        f"<b>{labels['full_name']}:</b> {data.get('full_name', '-')}\n"
        f"<b>{labels['age']}:</b> {data.get('age', '-')}\n"
        f"<b>{labels['phone']}:</b> {data.get('phone', '-')}\n"
        f"<b>{labels['district']}:</b> {data.get('district', '-')}\n"
        f"<b>{labels['family_status']}:</b> {data.get('family_status', '-')}\n"
        f"<b>{labels['education']}:</b> {data.get('education', '-')}\n"
        f"<b>{labels['studying_now']}:</b> {data.get('studying_now', '-')}\n"
        f"<b>{labels['study_place']}:</b> {data.get('study_place', '-')}\n"
        f"<b>{labels['has_experience']}:</b> {data.get('has_experience', '-')}\n"
        f"<b>{labels['last_job']}:</b> {data.get('last_job', '-')}\n"
        f"<b>{labels['work_period']}:</b> {data.get('work_period', '-')}\n"
        f"<b>{labels['leaving_reason']}:</b> {data.get('leaving_reason', '-')}\n"
        f"<b>{labels['applying_position']}:</b> {data.get('applying_position', '-')}\n"
        f"<b>{labels['preferred_branch']}:</b> {data.get('preferred_branch', '-')}\n"
        f"<b>{labels['start_date']}:</b> {data.get('start_date', '-')}\n\n"
        f"<b>{labels['telegram_id']}:</b> <code>{user.from_user.id}</code>\n"
        f"<b>{labels['username']}:</b> {username}"
    )


async def send_form_question(message: Message, user_id: int):
    lang = get_lang(user_id)
    step = get_current_form_step(user_id)
    options = step["options"]

    if options:
        await message.answer(step["question"], reply_markup=keyboard_from_options(options, lang))
    else:
        await message.answer(step["question"], reply_markup=controls_only_keyboard(lang))


async def send_to_hr(data: dict, user_message: Message, lang: str):
    text = build_text(data, user_message, lang)

    photo_file_id = data.get("photo_file_id")
    if photo_file_id:
        await bot.send_photo(
            chat_id=HR_CHAT_ID,
            photo=photo_file_id,
            caption=text
        )

    pdf_path = create_pdf(
        data=data,
        tg_user_id=user_message.from_user.id,
        tg_username=user_message.from_user.username,
        lang=lang,
    )

    try:
        await bot.send_document(
            chat_id=HR_CHAT_ID,
            document=FSInputFile(pdf_path),
            caption=TEXTS[lang]["pdf_caption"].format(name=data.get("full_name", "-"))
        )
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    await bot.send_message(chat_id=HR_CHAT_ID, text=text)


async def go_back(message: Message, user_id: int):
    ensure_user(user_id)
    lang = get_lang(user_id)
    t = TEXTS[lang]
    stage = users[user_id]["stage"]

    if stage == "language":
        await message.answer(t["start"], reply_markup=language_keyboard())
        return

    if stage == "unit":
        users[user_id]["stage"] = "language"
        await message.answer(t["start"], reply_markup=language_keyboard())
        return

    if stage == "vacancy":
        users[user_id]["stage"] = "unit"
        await message.answer(t["choose_unit"], reply_markup=main_menu_keyboard(lang))
        return

    if stage == "branch":
        users[user_id]["stage"] = "vacancy"
        unit = users[user_id]["data"].get("unit")
        await message.answer(t["choose_vacancy"], reply_markup=keyboard_from_options(VACANCIES[lang][unit], lang))
        return

    if stage == "form":
        idx = users[user_id]["form_index"]
        if idx > 0:
            idx -= 1
            users[user_id]["form_index"] = idx
            key = TEXTS[lang]["form_steps"][idx]["key"]
            users[user_id]["data"].pop(key, None)
            await send_form_question(message, user_id)
            return
        users[user_id]["stage"] = "branch"
        unit = users[user_id]["data"].get("unit")
        await message.answer(t["choose_branch"], reply_markup=keyboard_from_options(BRANCHES[lang][unit], lang))
        return

    if stage == "photo":
        users[user_id]["stage"] = "form"
        users[user_id]["data"].pop("photo_file_id", None)
        users[user_id]["form_index"] = len(TEXTS[lang]["form_steps"]) - 1
        await send_form_question(message, user_id)
        return

    if stage == "consent":
        users[user_id]["stage"] = "photo"
        await message.answer(t["photo_request"], reply_markup=controls_only_keyboard(lang))
        return


# =========================
# COMMANDS
# =========================
@dp.message(CommandStart())
async def start_handler(message: Message):
    reset_user(message.from_user.id)
    await message.answer(TEXTS["ru"]["start"], reply_markup=language_keyboard())


@dp.message()
async def text_handler(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    text = (message.text or "").strip()
    stage = users[user_id]["stage"]
    lang = get_lang(user_id)

    if text in [CANCEL_TEXT_RU, CANCEL_TEXT_UZ]:
        users.pop(user_id, None)
        await message.answer(TEXTS[lang]["cancelled"], reply_markup=ReplyKeyboardRemove())
        return

    if text in [RESTART_TEXT_RU, RESTART_TEXT_UZ]:
        reset_user(user_id)
        await message.answer(TEXTS["ru"]["start"], reply_markup=language_keyboard())
        return

    if text in [BACK_TEXT_RU, BACK_TEXT_UZ]:
        await go_back(message, user_id)
        return

    if stage == "language":
        if text == LANG_UZ:
            users[user_id]["lang"] = "uz"
            users[user_id]["stage"] = "unit"
            await message.answer(TEXTS["uz"]["choose_unit"], reply_markup=main_menu_keyboard("uz"))
            return
        if text == LANG_RU:
            users[user_id]["lang"] = "ru"
            users[user_id]["stage"] = "unit"
            await message.answer(TEXTS["ru"]["choose_unit"], reply_markup=main_menu_keyboard("ru"))
            return

        await message.answer(TEXTS["ru"]["start"], reply_markup=language_keyboard())
        return

    lang = get_lang(user_id)
    t = TEXTS[lang]

    if stage == "unit":
        if text not in UNITS[lang]:
            await message.answer(t["invalid_unit"], reply_markup=main_menu_keyboard(lang))
            return

        users[user_id]["data"]["unit"] = text
        users[user_id]["stage"] = "vacancy"
        await message.answer(t["choose_vacancy"], reply_markup=keyboard_from_options(VACANCIES[lang][text], lang))
        return

    if stage == "vacancy":
        unit = users[user_id]["data"].get("unit")
        allowed = VACANCIES[lang].get(unit, [])

        if text not in allowed:
            await message.answer(t["invalid_vacancy"], reply_markup=keyboard_from_options(allowed, lang))
            return

        users[user_id]["data"]["vacancy"] = text
        users[user_id]["stage"] = "branch"
        await message.answer(t["choose_branch"], reply_markup=keyboard_from_options(BRANCHES[lang][unit], lang))
        return

    if stage == "branch":
        unit = users[user_id]["data"].get("unit")
        allowed = BRANCHES[lang].get(unit, [])

        if text not in allowed:
            await message.answer(t["invalid_branch"], reply_markup=keyboard_from_options(allowed, lang))
            return

        users[user_id]["data"]["branch"] = text

        branch_info = LOCATIONS.get(text, {})
        address = branch_info.get("address_uz" if lang == "uz" else "address_ru", "-")
        map_link = branch_info.get("map", "-")

        users[user_id]["stage"] = "form"
        users[user_id]["form_index"] = 0

        await message.answer(
            t["branch_info"].format(branch=text, address=address, map_link=map_link),
            reply_markup=ReplyKeyboardRemove()
        )
        await send_form_question(message, user_id)
        return

    if stage == "form":
        step = get_current_form_step(user_id)
        key = step["key"]
        options = step["options"]

        if options and text not in options:
            await message.answer(t["invalid_option"], reply_markup=keyboard_from_options(options, lang))
            return

        users[user_id]["data"][key] = text
        users[user_id]["form_index"] += 1

        if users[user_id]["form_index"] < len(TEXTS[lang]["form_steps"]):
            await send_form_question(message, user_id)
        else:
            users[user_id]["stage"] = "photo"
            await message.answer(t["photo_request"], reply_markup=controls_only_keyboard(lang))
        return

    if stage == "photo":
        await message.answer(t["photo_required"], reply_markup=controls_only_keyboard(lang))
        return

    if stage == "consent":
        _, _, _, consent_text = get_control_texts(lang)
        if text != consent_text:
            await message.answer(t["consent_invalid"], reply_markup=consent_keyboard(lang))
            return

        try:
            await send_to_hr(users[user_id]["data"], message, lang)
            await message.answer(t["success"], reply_markup=ReplyKeyboardRemove())
        except Exception as e:
            await message.answer(f"❌ Ошибка при отправке: {e}", reply_markup=ReplyKeyboardRemove())

        users.pop(user_id, None)
        return

    await message.answer(t["fallback_start"])


@dp.message(Form.photo, F.photo)
async def get_photo(message: Message, state: FSMContext):

    data = await state.get_data()

    photo = message.photo[-1]

    await bot.send_photo(
        chat_id=int(HR_CHAT_ID),
        photo=photo.file_id,
        caption=f"📸 Nomzod rasmi: {data.get('full_name')}"
    )

    await message.answer(
        "✅ Anketani yuborishga rozimisiz?",
        reply_markup=consent_keyboard()
    )

    await state.set_state(Form.consent)

    await message.answer(t["consent_request"], reply_markup=consent_keyboard(lang))


@dp.message(F.document)
async def document_photo_handler(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    if users[user_id]["stage"] != "photo":
        return

    users[user_id]["data"]["photo_file_id"] = message.document.file_id
    users[user_id]["stage"] = "consent"

    await message.answer(
        "Анкету отправить?",
        reply_markup=consent_keyboard()
    )

    if text in [RESTART_TEXT_RU, RESTART_TEXT_UZ]:
        reset_user(user_id)
        await message.answer(TEXTS["ru"]["start"], reply_markup=language_keyboard())
        return

    if text in [BACK_TEXT_RU, BACK_TEXT_UZ]:
        await go_back(message, user_id)
        return

    if stage == "language":
        if text == LANG_UZ:
            users[user_id]["lang"] = "uz"
            users[user_id]["stage"] = "unit"
            await message.answer(TEXTS["uz"]["choose_unit"], reply_markup=main_menu_keyboard("uz"))
            return
        if text == LANG_RU:
            users[user_id]["lang"] = "ru"
            users[user_id]["stage"] = "unit"
            await message.answer(TEXTS["ru"]["choose_unit"], reply_markup=main_menu_keyboard("ru"))
            return

        await message.answer(TEXTS["ru"]["start"], reply_markup=language_keyboard())
        return

    lang = get_lang(user_id)
    t = TEXTS[lang]

    if stage == "unit":
        if text not in UNITS[lang]:
            await message.answer(t["invalid_unit"], reply_markup=main_menu_keyboard(lang))
            return

        users[user_id]["data"]["unit"] = text
        users[user_id]["stage"] = "vacancy"
        await message.answer(t["choose_vacancy"], reply_markup=keyboard_from_options(VACANCIES[lang][text], lang))
        return

    if stage == "vacancy":
        unit = users[user_id]["data"].get("unit")
        allowed = VACANCIES[lang].get(unit, [])

        if text not in allowed:
            await message.answer(t["invalid_vacancy"], reply_markup=keyboard_from_options(allowed, lang))
            return

        users[user_id]["data"]["vacancy"] = text
        users[user_id]["stage"] = "branch"
        await message.answer(t["choose_branch"], reply_markup=keyboard_from_options(BRANCHES[lang][unit], lang))
        return

    if stage == "branch":
        unit = users[user_id]["data"].get("unit")
        allowed = BRANCHES[lang].get(unit, [])

        if text not in allowed:
            await message.answer(t["invalid_branch"], reply_markup=keyboard_from_options(allowed, lang))
            return

        users[user_id]["data"]["branch"] = text

        branch_info = LOCATIONS.get(text, {})
        address = branch_info.get("address_uz" if lang == "uz" else "address_ru", "-")
        map_link = branch_info.get("map", "-")

        users[user_id]["stage"] = "form"
        users[user_id]["form_index"] = 0

        await message.answer(
            t["branch_info"].format(branch=text, address=address, map_link=map_link),
            reply_markup=ReplyKeyboardRemove()
        )
        await send_form_question(message, user_id)
        return

    if stage == "form":
        step = get_current_form_step(user_id)
        key = step["key"]
        options = step["options"]

        if options and text not in options:
            await message.answer(t["invalid_option"], reply_markup=keyboard_from_options(options, lang))
            return

        users[user_id]["data"][key] = text
        users[user_id]["form_index"] += 1

        if users[user_id]["form_index"] < len(TEXTS[lang]["form_steps"]):
            await send_form_question(message, user_id)
        else:
            users[user_id]["stage"] = "photo"
            await message.answer(t["photo_request"], reply_markup=controls_only_keyboard(lang))
        return

    if stage == "photo":
        await message.answer(t["photo_required"], reply_markup=controls_only_keyboard(lang))
        return

    if stage == "consent":
        _, _, _, consent_text = get_control_texts(lang)
        if text != consent_text:
            await message.answer(t["consent_invalid"], reply_markup=consent_keyboard(lang))
            return

        try:
            await send_to_hr(users[user_id]["data"], message, lang)
            await message.answer(t["success"], reply_markup=ReplyKeyboardRemove())
        except Exception as e:
            await message.answer(f"❌ Ошибка при отправке: {e}", reply_markup=ReplyKeyboardRemove())

        users.pop(user_id, None)
        return

    await message.answer(t["fallback_start"])


# =========================
# MAIN
# =========================
async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
