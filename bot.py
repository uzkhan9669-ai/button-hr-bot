import os
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, FSInputFile

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
# DATA
# =========================
BACK_TEXT = "Назад"
CANCEL_TEXT = "Отмена"
RESTART_TEXT = "Заново"
CONSENT_TEXT = "Согласен"

UNITS = ["Магазины", "Офис", "Склад"]

VACANCIES = {
    "Магазины": [
        "Продавец-консультант",
        "Кассир",
        "Охрана",
        "Уборщица",
        "Помощник",
    ],
    "Офис": [
        "HR",
    ],
    "Склад": [
        "Кладовщик",
    ],
}

BRANCHES = {
    "Магазины": [
        "Chilonzor Andalus",
        "Chilonzor Integro",
        "Beruniy Korzinka",
        "Risoviy bozor Magnit",
        "Shaxriston Korzinka",
    ],
    "Офис": [
        "Ofis Andalus",
    ],
    "Склад": [
        "Shayxontohur Makon",
    ],
}

LOCATIONS = {
    "Ofis Andalus": {
        "address": "г. Ташкент, Ofis Andalus",
        "map": "https://maps.app.goo.gl/GDgu8ar46ffh1zb46",
    },
    "Beruniy Korzinka": {
        "address": "г. Ташкент, Beruniy metro, Korzinka",
        "map": "https://maps.app.goo.gl/kJG4gRnn6H5aDm6F8",
    },
    "Chilonzor Andalus": {
        "address": "г. Ташкент, Chilonzor Andalus",
        "map": "https://maps.app.goo.gl/oYSJC9WdxCHJJCi9A",
    },
    "Risoviy bozor Magnit": {
        "address": "г. Ташкент, Risoviy bozor Magnit",
        "map": "https://maps.app.goo.gl/SYLeo8T8hLAQ92s76",
    },
    "Shayxontohur Makon": {
        "address": "г. Ташкент, Shayxontohur Makon",
        "map": "https://maps.app.goo.gl/MCsg4vuu8fiXYm8N7",
    },
    "Chilonzor Integro": {
        "address": "г. Ташкент, Chilonzor Integro",
        "map": "https://maps.app.goo.gl/qkpAoaWKAMcnsNT68",
    },
    "Shaxriston Korzinka": {
        "address": "г. Ташкент, Shaxriston Korzinka",
        "map": "https://maps.app.goo.gl/wtqnQgRQKhhksgQ38",
    },
}

FAMILY_OPTIONS = ["Холост/Не замужем", "Женат/Замужем", "Разведен(а)"]
EDUCATION_OPTIONS = ["Среднее", "Средне-специальное", "Высшее"]
YES_NO_OPTIONS = ["Да", "Нет"]

FORM_STEPS = [
    {"key": "full_name", "question": "Введите имя и фамилию:", "options": None},
    {"key": "age", "question": "Введите возраст:", "options": None},
    {"key": "phone", "question": "Введите номер телефона:", "options": None},
    {"key": "district", "question": "В каком районе проживаете?", "options": None},
    {"key": "family_status", "question": "Выберите семейное положение:", "options": FAMILY_OPTIONS},
    {"key": "education", "question": "Выберите образование:", "options": EDUCATION_OPTIONS},
    {"key": "studying_now", "question": "Сейчас учитесь?", "options": YES_NO_OPTIONS},
    {"key": "study_place", "question": "Где учились или учитесь?", "options": None},
    {"key": "has_experience", "question": "Есть опыт работы?", "options": YES_NO_OPTIONS},
    {"key": "last_job", "question": "Последнее место работы:", "options": None},
    {"key": "work_period", "question": "Сколько там работали?", "options": None},
    {"key": "leaving_reason", "question": "Почему ушли с работы?", "options": None},
    {"key": "applying_position", "question": "На какую должность подаете заявку?", "options": None},
    {"key": "preferred_branch", "question": "Какой филиал удобен для работы?", "options": None},
    {"key": "start_date", "question": "Когда готовы выйти на работу?", "options": None},
]

users = {}
FONT_NAME = "DejaVuSans"

# =========================
# KEYBOARDS
# =========================
def keyboard_from_options(options: list[str], add_controls: bool = True) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=item)] for item in options]
    if add_controls:
        rows.append(
            [
                KeyboardButton(text=BACK_TEXT),
                KeyboardButton(text=CANCEL_TEXT),
                KeyboardButton(text=RESTART_TEXT),
            ]
        )
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def controls_only_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text=BACK_TEXT),
            KeyboardButton(text=CANCEL_TEXT),
            KeyboardButton(text=RESTART_TEXT),
        ]],
        resize_keyboard=True
    )


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return keyboard_from_options(UNITS)


def consent_keyboard() -> ReplyKeyboardMarkup:
    return keyboard_from_options([CONSENT_TEXT])


# =========================
# HELPERS
# =========================
def ensure_user(user_id: int):
    if user_id not in users:
        users[user_id] = {
            "stage": "unit",
            "form_index": 0,
            "data": {},
        }


def reset_user(user_id: int):
    users[user_id] = {
        "stage": "unit",
        "form_index": 0,
        "data": {},
    }


def get_current_form_step(user_id: int):
    idx = users[user_id]["form_index"]
    return FORM_STEPS[idx]


def ensure_pdf_font():
    font_paths = [
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]

    for path in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.getFont(FONT_NAME)
                return
            except KeyError:
                pdfmetrics.registerFont(TTFont(FONT_NAME, path))
                return

    raise FileNotFoundError("DejaVuSans.ttf topilmadi")


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


def create_pdf(data: dict, tg_user_id: int, tg_username: str | None) -> str:
    ensure_pdf_font()
    os.makedirs("generated", exist_ok=True)

    safe_name = "".join(
        ch for ch in data.get("full_name", "candidate")
        if ch.isalnum() or ch in (" ", "_", "-")
    ).strip().replace(" ", "_")

    if not safe_name:
        safe_name = "candidate"

    pdf_path = f"generated/{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    y = height - 40

    c.setFont(FONT_NAME, 15)
    c.drawString(40, y, "BUTTON - Анкета кандидата")
    y -= 30

    c.setFont(FONT_NAME, 11)

    fields = [
        ("Подразделение", data.get("unit", "-")),
        ("Вакансия", data.get("vacancy", "-")),
        ("Филиал", data.get("branch", "-")),
        ("ФИО", data.get("full_name", "-")),
        ("Возраст", data.get("age", "-")),
        ("Телефон", data.get("phone", "-")),
        ("Район", data.get("district", "-")),
        ("Семейное положение", data.get("family_status", "-")),
        ("Образование", data.get("education", "-")),
        ("Сейчас учится", data.get("studying_now", "-")),
        ("Где учился/учится", data.get("study_place", "-")),
        ("Опыт работы", data.get("has_experience", "-")),
        ("Последняя работа", data.get("last_job", "-")),
        ("Срок работы", data.get("work_period", "-")),
        ("Причина ухода", data.get("leaving_reason", "-")),
        ("Желаемая должность", data.get("applying_position", "-")),
        ("Удобный филиал", data.get("preferred_branch", "-")),
        ("Когда готов выйти", data.get("start_date", "-")),
        ("Telegram ID", str(tg_user_id)),
        ("Username", tg_username or "-"),
        ("Дата", datetime.now().strftime("%d.%m.%Y %H:%M:%S")),
    ]

    for label, value in fields:
        text = f"{label}: {value}"
        for line in wrap_text(text):
            if y < 50:
                c.showPage()
                c.setFont(FONT_NAME, 11)
                y = height - 40
            c.drawString(40, y, line)
            y -= 18

    c.save()
    return pdf_path


def build_text(data: dict, user: Message) -> str:
    username = f"@{user.from_user.username}" if user.from_user.username else "-"

    return (
        "<b>Новая анкета кандидата</b>\n\n"
        f"<b>Подразделение:</b> {data.get('unit', '-')}\n"
        f"<b>Вакансия:</b> {data.get('vacancy', '-')}\n"
        f"<b>Филиал:</b> {data.get('branch', '-')}\n\n"
        f"<b>ФИО:</b> {data.get('full_name', '-')}\n"
        f"<b>Возраст:</b> {data.get('age', '-')}\n"
        f"<b>Телефон:</b> {data.get('phone', '-')}\n"
        f"<b>Район:</b> {data.get('district', '-')}\n"
        f"<b>Семейное положение:</b> {data.get('family_status', '-')}\n"
        f"<b>Образование:</b> {data.get('education', '-')}\n"
        f"<b>Сейчас учится:</b> {data.get('studying_now', '-')}\n"
        f"<b>Где учился/учится:</b> {data.get('study_place', '-')}\n"
        f"<b>Опыт работы:</b> {data.get('has_experience', '-')}\n"
        f"<b>Последняя работа:</b> {data.get('last_job', '-')}\n"
        f"<b>Срок работы:</b> {data.get('work_period', '-')}\n"
        f"<b>Причина ухода:</b> {data.get('leaving_reason', '-')}\n"
        f"<b>Желаемая должность:</b> {data.get('applying_position', '-')}\n"
        f"<b>Удобный филиал:</b> {data.get('preferred_branch', '-')}\n"
        f"<b>Когда готов выйти:</b> {data.get('start_date', '-')}\n\n"
        f"<b>Telegram ID:</b> <code>{user.from_user.id}</code>\n"
        f"<b>Username:</b> {username}"
    )


async def send_form_question(message: Message, user_id: int):
    step = get_current_form_step(user_id)
    options = step["options"]

    if options:
        await message.answer(step["question"], reply_markup=keyboard_from_options(options))
    else:
        await message.answer(step["question"], reply_markup=controls_only_keyboard())


async def send_to_hr(data: dict, user_message: Message):
    text = build_text(data, user_message)

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
        tg_username=user_message.from_user.username
    )

    try:
        await bot.send_document(
            chat_id=HR_CHAT_ID,
            document=FSInputFile(pdf_path),
            caption=f"PDF анкета: {data.get('full_name', '-')}"
        )
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    await bot.send_message(
        chat_id=HR_CHAT_ID,
        text=text
    )


async def go_back(message: Message, user_id: int):
    ensure_user(user_id)
    stage = users[user_id]["stage"]

    if stage == "unit":
        await message.answer("Выберите подразделение:", reply_markup=main_menu_keyboard())
        return

    if stage == "vacancy":
        users[user_id]["stage"] = "unit"
        await message.answer("Выберите подразделение:", reply_markup=main_menu_keyboard())
        return

    if stage == "branch":
        users[user_id]["stage"] = "vacancy"
        unit = users[user_id]["data"].get("unit")
        await message.answer("Выберите вакансию:", reply_markup=keyboard_from_options(VACANCIES[unit]))
        return

    if stage == "form":
        idx = users[user_id]["form_index"]
        if idx > 0:
            idx -= 1
            users[user_id]["form_index"] = idx
            key = FORM_STEPS[idx]["key"]
            users[user_id]["data"].pop(key, None)
            await send_form_question(message, user_id)
            return
        else:
            users[user_id]["stage"] = "branch"
            unit = users[user_id]["data"].get("unit")
            await message.answer("Выберите филиал:", reply_markup=keyboard_from_options(BRANCHES[unit]))
            return

    if stage == "photo":
        users[user_id]["stage"] = "form"
        users[user_id]["data"].pop("photo_file_id", None)
        users[user_id]["form_index"] = len(FORM_STEPS) - 1
        await send_form_question(message, user_id)
        return

    if stage == "consent":
        users[user_id]["stage"] = "photo"
        await message.answer("Отправьте фото кандидата:", reply_markup=controls_only_keyboard())
        return


# =========================
# GLOBAL COMMANDS
# =========================
@dp.message(CommandStart())
async def start_handler(message: Message):
    reset_user(message.from_user.id)
    await message.answer(
        "Здравствуйте.\n"
        "Добро пожаловать в HR бот BUTTON.\n\n"
        "Выберите подразделение:",
        reply_markup=main_menu_keyboard()
    )


@dp.message(F.text == CANCEL_TEXT)
async def cancel_handler(message: Message):
    users.pop(message.from_user.id, None)
    await message.answer(
        "Заявка отменена.\nДля нового заполнения нажмите /start",
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message(F.text == RESTART_TEXT)
async def restart_handler(message: Message):
    reset_user(message.from_user.id)
    await message.answer(
        "Заполнение начато заново.\nВыберите подразделение:",
        reply_markup=main_menu_keyboard()
    )


@dp.message(F.text == BACK_TEXT)
async def back_handler(message: Message):
    await go_back(message, message.from_user.id)

# =========================
# PHOTO
# =========================
@dp.message(F.photo)
async def photo_handler(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    if users[user_id]["stage"] != "photo":
        await message.answer("Сейчас фото не требуется.")
        return

    users[user_id]["data"]["photo_file_id"] = message.photo[-1].file_id
    users[user_id]["stage"] = "consent"

    await message.answer(
        "Подтвердите отправку анкеты:",
        reply_markup=consent_keyboard()
    )

# =========================
# TEXT FLOW
# =========================
@dp.message()
async def text_handler(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    stage = users[user_id]["stage"]
    text = (message.text or "").strip()

    if stage == "unit":
        if text not in UNITS:
            await message.answer("Выберите подразделение кнопкой ниже.", reply_markup=main_menu_keyboard())
            return

        users[user_id]["data"]["unit"] = text
        users[user_id]["stage"] = "vacancy"
        await message.answer(
            "Выберите вакансию:",
            reply_markup=keyboard_from_options(VACANCIES[text])
        )
        return

    if stage == "vacancy":
        unit = users[user_id]["data"].get("unit")
        allowed = VACANCIES.get(unit, [])

        if text not in allowed:
            await message.answer("Выберите вакансию кнопкой ниже.", reply_markup=keyboard_from_options(allowed))
            return

        users[user_id]["data"]["vacancy"] = text
        users[user_id]["stage"] = "branch"
        await message.answer(
            "Выберите филиал:",
            reply_markup=keyboard_from_options(BRANCHES[unit])
        )
        return

    if stage == "branch":
        unit = users[user_id]["data"].get("unit")
        allowed = BRANCHES.get(unit, [])

        if text not in allowed:
            await message.answer("Выберите филиал кнопкой ниже.", reply_markup=keyboard_from_options(allowed))
            return

        users[user_id]["data"]["branch"] = text

        branch_info = LOCATIONS.get(text, {})
        address = branch_info.get("address", "-")
        map_link = branch_info.get("map", "-")

        users[user_id]["stage"] = "form"
        users[user_id]["form_index"] = 0

        await message.answer(
            f"<b>Филиал:</b> {text}\n"
            f"<b>Адрес:</b> {address}\n"
            f"<b>Карта:</b> {map_link}",
            reply_markup=ReplyKeyboardRemove()
        )
        await send_form_question(message, user_id)
        return

    if stage == "form":
        step = get_current_form_step(user_id)
        key = step["key"]
        options = step["options"]

        if options and text not in options:
            await message.answer(
                "Выберите вариант кнопкой ниже.",
                reply_markup=keyboard_from_options(options)
            )
            return

        users[user_id]["data"][key] = text
        users[user_id]["form_index"] += 1

        if users[user_id]["form_index"] < len(FORM_STEPS):
            await send_form_question(message, user_id)
        else:
            users[user_id]["stage"] = "photo"
            await message.answer(
                "Отправьте фото кандидата:",
                reply_markup=controls_only_keyboard()
            )
        return

    if stage == "photo":
        await message.answer("Сейчас нужно отправить фото.", reply_markup=controls_only_keyboard())
        return

    if stage == "consent":
        if text != CONSENT_TEXT:
            await message.answer("Для отправки анкеты нажмите кнопку 'Согласен'.", reply_markup=consent_keyboard())
            return

        try:
            await send_to_hr(users[user_id]["data"], message)
            await message.answer(
                "Анкета успешно отправлена.",
                reply_markup=ReplyKeyboardRemove()
            )
        except Exception as e:
            await message.answer(
                f"Ошибка при отправке: {e}",
                reply_markup=ReplyKeyboardRemove()
            )

        users.pop(user_id, None)
        return

# =========================
# MAIN
# =========================
async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
