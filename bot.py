import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import gspread
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    FSInputFile,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from dotenv import load_dotenv
from fpdf import FPDF
from google.oauth2.service_account import Credentials

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
HR_CHAT_ID = os.getenv("HR_CHAT_ID", "").strip()

GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "BUTTON_CANDIDATES").strip()
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON", "").strip()
GOOGLE_CREDS_FILE = os.getenv("GOOGLE_CREDS_FILE", "").strip()

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi.")
if not HR_CHAT_ID:
    raise ValueError("HR_CHAT_ID topilmadi.")

HR_CHAT_ID_INT = int(HR_CHAT_ID)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())

TMP_DIR = Path("/tmp/button_hr_bot")
TMP_DIR.mkdir(parents=True, exist_ok=True)


class Form(StatesGroup):
    full_name = State()
    age = State()
    phone = State()
    position = State()
    branch = State()
    experience = State()
    experience_text = State()
    schedule = State()
    salary = State()
    start_date = State()
    comment = State()
    photo = State()
    external_cv = State()


STEP_ORDER = [
    "full_name",
    "age",
    "phone",
    "position",
    "branch",
    "experience",
    "experience_text",
    "schedule",
    "salary",
    "start_date",
    "comment",
    "photo",
    "external_cv",
]

STEP_TO_STATE = {
    "full_name": Form.full_name,
    "age": Form.age,
    "phone": Form.phone,
    "position": Form.position,
    "branch": Form.branch,
    "experience": Form.experience,
    "experience_text": Form.experience_text,
    "schedule": Form.schedule,
    "salary": Form.salary,
    "start_date": Form.start_date,
    "comment": Form.comment,
    "photo": Form.photo,
    "external_cv": Form.external_cv,
}

POSITIONS = [
    "Sotuvchi-maslahatchi",
    "Kassir",
    "Skladovshik",
    "Qo'riqchi",
]

BRANCHES = [
    "Risoviy bozor - Magnit",
    "Chilonzor - Andalus",
    "Beruniy - Korzinka",
    "Shayxontohur - Makon",
    "Farqi yo'q",
]

EXPERIENCE_OPTIONS = ["Ha", "Yo'q"]

SCHEDULES = [
    "To'liq smena",
    "Faqat kunduzgi",
    "Faqat kechki",
    "Moslashuvchan",
]

ACTION_ROW = ["⬅️ Orqaga", "❌ Bekor qilish", "🔄 Qaytadan boshlash"]
SKIP_ROW = ["⏭ O'tkazib yuborish"]


def kb(rows: list[list[str]]) -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text=item) for item in row] for row in rows]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def start_kb() -> ReplyKeyboardMarkup:
    return kb([["✅ Anketani boshlash"]])


def action_kb() -> ReplyKeyboardMarkup:
    return kb([ACTION_ROW])


def position_kb() -> ReplyKeyboardMarkup:
    return kb([
        ["Sotuvchi-maslahatchi", "Kassir"],
        ["Skladovshik", "Qo'riqchi"],
        ACTION_ROW,
    ])


def branch_kb() -> ReplyKeyboardMarkup:
    return kb([
        ["Risoviy bozor - Magnit"],
        ["Chilonzor - Andalus"],
        ["Beruniy - Korzinka"],
        ["Shayxontohur - Makon"],
        ["Farqi yo'q"],
        ACTION_ROW,
    ])


def yes_no_kb() -> ReplyKeyboardMarkup:
    return kb([
        ["Ha", "Yo'q"],
        ACTION_ROW,
    ])


def schedule_kb() -> ReplyKeyboardMarkup:
    return kb([
        ["To'liq smena"],
        ["Faqat kunduzgi", "Faqat kechki"],
        ["Moslashuvchan"],
        ACTION_ROW,
    ])


def cv_optional_kb() -> ReplyKeyboardMarkup:
    return kb([
        SKIP_ROW,
        ACTION_ROW,
    ])


def hr_panel_kb() -> ReplyKeyboardMarkup:
    return kb([
        ["/stats", "/last"],
        ["/panel"],
    ])


def state_name(full_state: str | None) -> str | None:
    if not full_state:
        return None
    return full_state.split(":")[-1]


def clean_filename(text: str) -> str:
    text = text.strip().replace(" ", "_")
    return re.sub(r"[^A-Za-z0-9_]+", "", text) or "candidate"


def sanitize_pdf_text(value: Any) -> str:
    if value is None:
        return "-"
    text = str(value)
    replacements = {
        "’": "'",
        "‘": "'",
        "ʻ": "'",
        "ʼ": "'",
        "“": '"',
        "”": '"',
        "—": "-",
        "–": "-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[\U00010000-\U0010ffff]", "", text)
    text = "".join(ch for ch in text if ch.isprintable())
    return text.strip() or "-"


def find_font_path() -> str:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return path
    raise FileNotFoundError("Unicode shrift topilmadi.")


def get_creds_file_path() -> str:
    if GOOGLE_CREDS_JSON:
        path = TMP_DIR / "service_account.json"
        path.write_text(GOOGLE_CREDS_JSON, encoding="utf-8")
        return str(path)
    if GOOGLE_CREDS_FILE:
        return GOOGLE_CREDS_FILE
    raise ValueError("Google credentials topilmadi. GOOGLE_CREDS_JSON yoki GOOGLE_CREDS_FILE kerak.")


def get_gspread_client() -> gspread.Client:
    creds_file = get_creds_file_path()
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = Credentials.from_service_account_file(creds_file, scopes=scopes)
    return gspread.authorize(credentials)


def get_sheet():
    client = get_gspread_client()
    spreadsheet = client.open(GOOGLE_SHEET_NAME)
    sheet = spreadsheet.sheet1

    headers = [
        "created_at",
        "full_name",
        "age",
        "phone",
        "position",
        "branch",
        "experience",
        "experience_text",
        "schedule",
        "salary",
        "start_date",
        "comment",
        "telegram_user_id",
        "telegram_username",
        "generated_pdf_sent",
        "external_cv_sent",
    ]

    current_headers = sheet.row_values(1)
    if current_headers != headers:
        if not current_headers:
            sheet.append_row(headers)
    return sheet


def save_candidate_to_sheet(data: dict):
    try:
        sheet = get_sheet()
        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data.get("full_name", ""),
            data.get("age", ""),
            data.get("phone", ""),
            data.get("position", ""),
            data.get("branch", ""),
            data.get("experience", ""),
            data.get("experience_text", ""),
            data.get("schedule", ""),
            data.get("salary", ""),
            data.get("start_date", ""),
            data.get("comment", ""),
            str(data.get("telegram_user_id", "")),
            data.get("telegram_username", ""),
            "Ha" if data.get("generated_pdf_sent") else "Yo'q",
            "Ha" if data.get("external_cv_sent") else "Yo'q",
        ]
        sheet.append_row(row)
    except Exception as e:
        print(f"Google Sheets save error: {e}")


def get_stats_text() -> str:
    try:
        sheet = get_sheet()
        records = sheet.get_all_records()
        total = len(records)

        pos_count: dict[str, int] = {}
        branch_count: dict[str, int] = {}

        for r in records:
            pos = r.get("position", "-") or "-"
            branch = r.get("branch", "-") or "-"
            pos_count[pos] = pos_count.get(pos, 0) + 1
            branch_count[branch] = branch_count.get(branch, 0) + 1

        pos_lines = "\n".join([f"• {k}: {v}" for k, v in pos_count.items()]) or "• Ma'lumot yo'q"
        branch_lines = "\n".join([f"• {k}: {v}" for k, v in branch_count.items()]) or "• Ma'lumot yo'q"

        return (
            "<b>HR Statistikasi</b>\n\n"
            f"<b>Jami nomzodlar:</b> {total}\n\n"
            f"<b>Lavozimlar bo'yicha:</b>\n{pos_lines}\n\n"
            f"<b>Filiallar bo'yicha:</b>\n{branch_lines}"
        )
    except Exception as e:
        return f"Statistikani olishda xatolik: {e}"


def get_last_candidates_text(limit: int = 5) -> str:
    try:
        sheet = get_sheet()
        records = sheet.get_all_records()
        if not records:
            return "Hali nomzodlar yo'q."

        last_items = records[-limit:]
        lines = ["<b>Oxirgi nomzodlar</b>\n"]
        for i, r in enumerate(reversed(last_items), start=1):
            lines.append(
                f"{i}. <b>{r.get('full_name', '-')}</b>\n"
                f"   Lavozim: {r.get('position', '-')}\n"
                f"   Filial: {r.get('branch', '-')}\n"
                f"   Telefon: {r.get('phone', '-')}\n"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Oxirgi nomzodlarni olishda xatolik: {e}"


def create_candidate_pdf(data: dict, photo_path: str | None) -> str:
    candidate_name = sanitize_pdf_text(data.get("full_name", "candidate"))
    safe_name = clean_filename(candidate_name)
    pdf_path = TMP_DIR / f"CV_{safe_name}.pdf"

    font_path = find_font_path()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.add_font("Custom", "", font_path)
    pdf.set_font("Custom", size=16)

    pdf.cell(0, 10, "BUTTON CV", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(2)

    pdf.set_font("Custom", size=11)
    pdf.cell(0, 8, f"Sana: {datetime.now().strftime('%Y-%m-%d %H:%M')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    if photo_path and Path(photo_path).exists():
        try:
            pdf.image(photo_path, x=155, y=18, w=30)
        except Exception:
            pass

    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Custom", size=12)
    pdf.cell(0, 8, "Nomzod ma'lumotlari", new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.ln(2)

    rows = [
        ("Ism familiya", data.get("full_name", "-")),
        ("Yoshi", data.get("age", "-")),
        ("Telefon", data.get("phone", "-")),
        ("Lavozim", data.get("position", "-")),
        ("Filial", data.get("branch", "-")),
        ("Tajriba bormi", data.get("experience", "-")),
        ("Tajriba haqida", data.get("experience_text", "-")),
        ("Qulay grafik", data.get("schedule", "-")),
        ("Kutilayotgan maosh", data.get("salary", "-")),
        ("Ish boshlash vaqti", data.get("start_date", "-")),
        ("Izoh", data.get("comment", "-")),
        ("Telegram ID", str(data.get("telegram_user_id", "-"))),
        ("Telegram username", data.get("telegram_username", "-")),
    ]

    pdf.set_font("Custom", size=11)
    for label, value in rows:
        line = f"{sanitize_pdf_text(label)}: {sanitize_pdf_text(value)}"
        pdf.multi_cell(0, 8, line, border=0)
        pdf.ln(1)

    pdf.output(str(pdf_path))
    return str(pdf_path)


async def download_candidate_photo(message: Message, full_name: str) -> str:
    photo = message.photo[-1]
    tg_file = await bot.get_file(photo.file_id)

    safe_name = clean_filename(full_name)
    photo_path = TMP_DIR / f"{safe_name}_photo.jpg"

    await bot.download_file(tg_file.file_path, destination=photo_path)
    return str(photo_path)


async def send_prompt(message: Message, field: str):
    if field == "full_name":
        await message.answer("👤 Ism va familiyangizni yozing:", reply_markup=action_kb())
    elif field == "age":
        await message.answer("🎂 Yoshingiz nechida?", reply_markup=action_kb())
    elif field == "phone":
        await message.answer("📱 Telefon raqamingizni yozing:\nMasalan: +998901234567", reply_markup=action_kb())
    elif field == "position":
        await message.answer("💼 Qaysi lavozimda ishlamoqchisiz?", reply_markup=position_kb())
    elif field == "branch":
        await message.answer("📍 Qaysi filial yoki hudud sizga qulay?", reply_markup=branch_kb())
    elif field == "experience":
        await message.answer("⭐ Shu lavozim bo'yicha ish tajribangiz bormi?", reply_markup=yes_no_kb())
    elif field == "experience_text":
        await message.answer("🧠 Tajribangiz haqida qisqacha yozing.\nAgar bo'lmasa: yo'q deb yozing.", reply_markup=action_kb())
    elif field == "schedule":
        await message.answer("🕒 Qaysi ish grafigi sizga qulay?", reply_markup=schedule_kb())
    elif field == "salary":
        await message.answer("💰 Kutilayotgan oylik maoshingiz qancha?", reply_markup=action_kb())
    elif field == "start_date":
        await message.answer("🚀 Qachondan ish boshlay olasiz?", reply_markup=action_kb())
    elif field == "comment":
        await message.answer("💬 Qo'shimcha ma'lumot yoki izoh bo'lsa yozing.\nBo'lmasa: yo'q", reply_markup=action_kb())
    elif field == "photo":
        await message.answer("📸 Iltimos, o'zingizning rasmingizni yuboring.\nYuzingiz aniq ko'rinadigan bo'lsin.", reply_markup=action_kb())
    elif field == "external_cv":
        await message.answer(
            "📄 Agar tayyor CV'ingiz bo'lsa, PDF formatda yuboring.\n"
            "Agar yo'q bo'lsa, pastdagi tugmani bosing.",
            reply_markup=cv_optional_kb()
        )


async def go_to_state(message: Message, state: FSMContext, field: str):
    await state.set_state(STEP_TO_STATE[field])
    await send_prompt(message, field)


@dp.message(Command("start"))
async def start_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🤖 <b>Assalomu alaykum!</b>\n\n"
        "BUTTON erkaklar kiyim do'koniga ishga qabul botiga xush kelibsiz.\n\n"
        "📋 Iltimos, quyidagi qisqa anketani to'ldiring.",
        reply_markup=start_kb()
    )


@dp.message(Command("panel"))
async def panel_cmd(message: Message):
    if message.from_user.id != HR_CHAT_ID_INT:
        return
    await message.answer(
        "HR panelga xush kelibsiz.",
        reply_markup=hr_panel_kb()
    )


@dp.message(Command("stats"))
async def stats_cmd(message: Message):
    if message.from_user.id != HR_CHAT_ID_INT:
        return
    await message.answer(get_stats_text())


@dp.message(Command("last"))
async def last_cmd(message: Message):
    if message.from_user.id != HR_CHAT_ID_INT:
        return
    await message.answer(get_last_candidates_text())


@dp.message(F.text == "✅ Anketani boshlash")
async def start_form(message: Message, state: FSMContext):
    await state.clear()
    await go_to_state(message, state, "full_name")


@dp.message(F.text == "🔄 Qaytadan boshlash")
async def restart_form(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🔄 Anketa boshidan boshlandi.", reply_markup=ReplyKeyboardRemove())
    await go_to_state(message, state, "full_name")


@dp.message(F.text == "❌ Bekor qilish")
async def cancel_form(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Anketa bekor qilindi.", reply_markup=start_kb())


@dp.message(F.text == "⬅️ Orqaga")
async def back_form(message: Message, state: FSMContext):
    current_full = await state.get_state()
    current = state_name(current_full)

    if not current:
        await message.answer("Siz hozir anketada emassiz.", reply_markup=start_kb())
        return

    idx = STEP_ORDER.index(current)
    if idx == 0:
        await state.clear()
        await message.answer("Siz boshiga qaytdingiz.", reply_markup=start_kb())
        return

    prev_field = STEP_ORDER[idx - 1]
    await go_to_state(message, state, prev_field)


async def finish_candidate_flow(message: Message, state: FSMContext, external_cv_sent: bool):
    data = await state.get_data()
    data["external_cv_sent"] = external_cv_sent
    data["generated_pdf_sent"] = True

    save_candidate_to_sheet(data)

    await state.clear()
    await message.answer(
        "✅ Rahmat! Sizning anketa, rasm va CV ma'lumotlari qabul qilindi.\n"
        "BUTTON HR jamoasi tez orada siz bilan bog'lanadi.",
        reply_markup=start_kb()
    )


@dp.message(Form.photo, F.photo)
async def get_photo(message: Message, state: FSMContext):
    data = await state.get_data()

    telegram_username = message.from_user.username if message.from_user.username else "yoq"
    telegram_user_id = message.from_user.id

    data["telegram_username"] = telegram_username
    data["telegram_user_id"] = telegram_user_id
    await state.update_data(
        telegram_username=telegram_username,
        telegram_user_id=telegram_user_id
    )

    text = (
        "📥 <b>BUTTON | Yangi nomzod anketasi</b>\n\n"
        f"👤 <b>Ism familiya:</b> {data.get('full_name')}\n"
        f"🎂 <b>Yoshi:</b> {data.get('age')}\n"
        f"📱 <b>Telefon:</b> {data.get('phone')}\n"
        f"💼 <b>Lavozim:</b> {data.get('position')}\n"
        f"📍 <b>Filial:</b> {data.get('branch')}\n"
        f"⭐ <b>Tajriba bormi:</b> {data.get('experience')}\n"
        f"🧠 <b>Tajriba haqida:</b> {data.get('experience_text')}\n"
        f"🕒 <b>Qulay grafik:</b> {data.get('schedule')}\n"
        f"💰 <b>Kutilayotgan maosh:</b> {data.get('salary')}\n"
        f"🚀 <b>Ish boshlash vaqti:</b> {data.get('start_date')}\n"
        f"💬 <b>Izoh:</b> {data.get('comment')}\n\n"
        f"🆔 <b>Telegram ID:</b> <code>{telegram_user_id}</code>\n"
        f"📎 <b>Username:</b> @{telegram_username}"
    )

    await bot.send_message(chat_id=HR_CHAT_ID_INT, text=text)

    await bot.send_photo(
        chat_id=HR_CHAT_ID_INT,
        photo=message.photo[-1].file_id,
        caption=f"📸 Nomzod rasmi: {data.get('full_name')}"
    )

    try:
        photo_path = await download_candidate_photo(message, data.get("full_name", "candidate"))
        pdf_path = create_candidate_pdf(data, photo_path)

        await bot.send_document(
            chat_id=HR_CHAT_ID_INT,
            document=FSInputFile(pdf_path),
            caption=f"📄 Tayyor CV PDF: {data.get('full_name')}"
        )
    except Exception as e:
        await bot.send_message(
            chat_id=HR_CHAT_ID_INT,
            text=f"⚠️ PDF yaratishda xatolik bo'ldi: {e}"
        )

    await go_to_state(message, state, "external_cv")


@dp.message(Form.external_cv, F.document)
async def get_external_cv(message: Message, state: FSMContext):
    doc = message.document
    if not doc.file_name.lower().endswith(".pdf"):
        await message.answer("Iltimos, faqat PDF fayl yuboring.", reply_markup=cv_optional_kb())
        return

    await bot.send_document(
        chat_id=HR_CHAT_ID_INT,
        document=doc.file_id,
        caption="📎 Nomzod yuborgan tayyor CV PDF"
    )
    await finish_candidate_flow(message, state, external_cv_sent=True)


@dp.message(Form.external_cv, F.text == "⏭ O'tkazib yuborish")
async def skip_external_cv(message: Message, state: FSMContext):
    await finish_candidate_flow(message, state, external_cv_sent=False)


@dp.message(Form.photo)
async def photo_required(message: Message):
    await message.answer(
        "📸 Iltimos, rasmni photo ko'rinishida yuboring.",
        reply_markup=action_kb()
    )


@dp.message(Form.external_cv)
async def external_cv_required(message: Message):
    await message.answer(
        "📄 Iltimos, PDF fayl yuboring yoki ⏭ O'tkazib yuborish tugmasini bosing.",
        reply_markup=cv_optional_kb()
    )


@dp.message(
    Form.full_name
    | Form.age
    | Form.phone
    | Form.position
    | Form.branch
    | Form.experience
    | Form.experience_text
    | Form.schedule
    | Form.salary
    | Form.start_date
    | Form.comment
)
async def process_form_steps(message: Message, state: FSMContext):
    current = state_name(await state.get_state())
    if not current:
        await message.answer("Xatolik yuz berdi. /start bosing.")
        return

    text = (message.text or "").strip()

    if current == "full_name":
        if len(text) < 3:
            await message.answer("Iltimos, to'liq ism familiya yozing.")
            return
        await state.update_data(full_name=text)
        await go_to_state(message, state, "age")
        return

    if current == "age":
        if not text.isdigit():
            await message.answer("Iltimos, yoshni raqam bilan kiriting. Masalan: 22")
            return
        await state.update_data(age=text)
        await go_to_state(message, state, "phone")
        return

    if current == "phone":
        await state.update_data(phone=text)
        await go_to_state(message, state, "position")
        return

    if current == "position":
        if text not in POSITIONS:
            await message.answer("Iltimos, tugmalardan birini tanlang.", reply_markup=position_kb())
            return
        await state.update_data(position=text)
        await go_to_state(message, state, "branch")
        return

    if current == "branch":
        if text not in BRANCHES:
            await message.answer("Iltimos, tugmalardan birini tanlang.", reply_markup=branch_kb())
            return
        await state.update_data(branch=text)
        await go_to_state(message, state, "experience")
        return

    if current == "experience":
        if text not in EXPERIENCE_OPTIONS:
            await message.answer("Iltimos, tugmalardan birini tanlang.", reply_markup=yes_no_kb())
            return
        await state.update_data(experience=text)
        await go_to_state(message, state, "experience_text")
        return

    if current == "experience_text":
        await state.update_data(experience_text=text)
        await go_to_state(message, state, "schedule")
        return

    if current == "schedule":
        if text not in SCHEDULES:
            await message.answer("Iltimos, tugmalardan birini tanlang.", reply_markup=schedule_kb())
            return
        await state.update_data(schedule=text)
        await go_to_state(message, state, "salary")
        return

    if current == "salary":
        await state.update_data(salary=text)
        await go_to_state(message, state, "start_date")
        return

    if current == "start_date":
        await state.update_data(start_date=text)
        await go_to_state(message, state, "comment")
        return

    if current == "comment":
        await state.update_data(comment=text)
        await go_to_state(message, state, "photo")
        return


async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
