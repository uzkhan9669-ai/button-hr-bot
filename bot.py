import asyncio
import os
import re
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, StateFilter
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

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
HR_CHAT_ID = os.getenv("HR_CHAT_ID", "").strip()

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi. Railway Variables ni tekshiring.")
if not HR_CHAT_ID:
    raise ValueError("HR_CHAT_ID topilmadi. Railway Variables ni tekshiring.")

HR_CHAT_ID = int(HR_CHAT_ID)

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

STATE_MAP = {
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


def make_kb(rows: list[list[str]]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=x) for x in row] for row in rows],
        resize_keyboard=True,
    )


def start_kb() -> ReplyKeyboardMarkup:
    return make_kb([["✅ Anketani boshlash"]])


def action_kb() -> ReplyKeyboardMarkup:
    return make_kb([ACTION_ROW])


def position_kb() -> ReplyKeyboardMarkup:
    return make_kb([
        ["Sotuvchi-maslahatchi", "Kassir"],
        ["Skladovshik", "Qo'riqchi"],
        ACTION_ROW,
    ])


def branch_kb() -> ReplyKeyboardMarkup:
    return make_kb([
        ["Risoviy bozor - Magnit"],
        ["Chilonzor - Andalus"],
        ["Beruniy - Korzinka"],
        ["Shayxontohur - Makon"],
        ["Farqi yo'q"],
        ACTION_ROW,
    ])


def yes_no_kb() -> ReplyKeyboardMarkup:
    return make_kb([
        ["Ha", "Yo'q"],
        ACTION_ROW,
    ])


def schedule_kb() -> ReplyKeyboardMarkup:
    return make_kb([
        ["To'liq smena"],
        ["Faqat kunduzgi", "Faqat kechki"],
        ["Moslashuvchan"],
        ACTION_ROW,
    ])


def external_cv_kb() -> ReplyKeyboardMarkup:
    return make_kb([
        ["⏭ O'tkazib yuborish"],
        ACTION_ROW,
    ])


def get_state_name(full_state: str | None) -> str | None:
    if not full_state:
        return None
    return full_state.split(":")[-1]


def clean_filename(text: str) -> str:
    text = text.strip().replace(" ", "_")
    return re.sub(r"[^A-Za-z0-9_]+", "", text) or "candidate"


def sanitize_pdf_text(value: str) -> str:
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


def create_candidate_pdf(data: dict, photo_path: str | None) -> str:
    candidate_name = sanitize_pdf_text(data.get("full_name", "candidate"))
    safe_name = clean_filename(candidate_name)
    pdf_path = TMP_DIR / f"CV_{safe_name}.pdf"

    font_path = find_font_path()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.add_font("Custom", "", font_path)
    pdf.set_font("Custom", size=15)

    pdf.cell(0, 10, "BUTTON CV", align="C")
    pdf.ln(12)

    if photo_path and Path(photo_path).exists():
        try:
            pdf.image(photo_path, x=155, y=18, w=30)
        except Exception:
            pass

    pdf.set_font("Custom", size=11)

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

    for label, value in rows:
        pdf.multi_cell(0, 8, f"{sanitize_pdf_text(label)}: {sanitize_pdf_text(value)}")
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


async def ask_step(message: Message, field: str):
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
            "📄 Agar tayyor CV'ingiz bo'lsa, PDF formatda yuboring.\nAgar yo'q bo'lsa, pastdagi tugmani bosing.",
            reply_markup=external_cv_kb()
        )


async def goto_step(message: Message, state: FSMContext, field: str):
    await state.set_state(STATE_MAP[field])
    await ask_step(message, field)


async def finish_flow(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "✅ Rahmat! Sizning anketa, rasm va CV ma'lumotlari qabul qilindi.\n"
        "BUTTON HR jamoasi tez orada siz bilan bog'lanadi.",
        reply_markup=start_kb()
    )


@dp.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🤖 <b>Assalomu alaykum!</b>\n\n"
        "BUTTON erkaklar kiyim do'koniga ishga qabul botiga xush kelibsiz.\n\n"
        "📋 Iltimos, quyidagi qisqa anketani to'ldiring.",
        reply_markup=start_kb()
    )


@dp.message(F.text == "✅ Anketani boshlash")
async def start_form(message: Message, state: FSMContext):
    await state.clear()
    await goto_step(message, state, "full_name")


@dp.message(F.text == "🔄 Qaytadan boshlash")
async def restart_form(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🔄 Anketa boshidan boshlandi.", reply_markup=ReplyKeyboardRemove())
    await goto_step(message, state, "full_name")


@dp.message(F.text == "❌ Bekor qilish")
async def cancel_form(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Anketa bekor qilindi.", reply_markup=start_kb())


@dp.message(F.text == "⬅️ Orqaga")
async def back_form(message: Message, state: FSMContext):
    current = get_state_name(await state.get_state())

    if not current:
        await message.answer("Siz hozir anketada emassiz.", reply_markup=start_kb())
        return

    index = STEP_ORDER.index(current)
    if index == 0:
        await state.clear()
        await message.answer("Siz boshiga qaytdingiz.", reply_markup=start_kb())
        return

    prev_field = STEP_ORDER[index - 1]
    await goto_step(message, state, prev_field)


@dp.message(StateFilter(Form.full_name))
async def process_full_name(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if len(text) < 3:
        await message.answer("Iltimos, to'liq ism familiya yozing.")
        return
    await state.update_data(full_name=text)
    await goto_step(message, state, "age")


@dp.message(StateFilter(Form.age))
async def process_age(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer("Iltimos, yoshni raqam bilan kiriting. Masalan: 22")
        return
    await state.update_data(age=text)
    await goto_step(message, state, "phone")


@dp.message(StateFilter(Form.phone))
async def process_phone(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    await state.update_data(phone=text)
    await goto_step(message, state, "position")


@dp.message(StateFilter(Form.position))
async def process_position(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text not in POSITIONS:
        await message.answer("Iltimos, tugmalardan birini tanlang.", reply_markup=position_kb())
        return
    await state.update_data(position=text)
    await goto_step(message, state, "branch")


@dp.message(StateFilter(Form.branch))
async def process_branch(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text not in BRANCHES:
        await message.answer("Iltimos, tugmalardan birini tanlang.", reply_markup=branch_kb())
        return
    await state.update_data(branch=text)
    await goto_step(message, state, "experience")


@dp.message(StateFilter(Form.experience))
async def process_experience(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text not in EXPERIENCE_OPTIONS:
        await message.answer("Iltimos, tugmalardan birini tanlang.", reply_markup=yes_no_kb())
        return
    await state.update_data(experience=text)
    await goto_step(message, state, "experience_text")


@dp.message(StateFilter(Form.experience_text))
async def process_experience_text(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    await state.update_data(experience_text=text)
    await goto_step(message, state, "schedule")


@dp.message(StateFilter(Form.schedule))
async def process_schedule(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text not in SCHEDULES:
        await message.answer("Iltimos, tugmalardan birini tanlang.", reply_markup=schedule_kb())
        return
    await state.update_data(schedule=text)
    await goto_step(message, state, "salary")


@dp.message(StateFilter(Form.salary))
async def process_salary(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    await state.update_data(salary=text)
    await goto_step(message, state, "start_date")


@dp.message(StateFilter(Form.start_date))
async def process_start_date(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    await state.update_data(start_date=text)
    await goto_step(message, state, "comment")


@dp.message(StateFilter(Form.comment))
async def process_comment(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    await state.update_data(comment=text)
    await goto_step(message, state, "photo")


@dp.message(StateFilter(Form.photo), F.photo)
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()

    telegram_username = message.from_user.username or "yoq"
    telegram_user_id = message.from_user.id

    await state.update_data(
        telegram_username=telegram_username,
        telegram_user_id=telegram_user_id
    )

    data["telegram_username"] = telegram_username
    data["telegram_user_id"] = telegram_user_id

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

    await bot.send_message(chat_id=HR_CHAT_ID, text=text)

    await bot.send_photo(
        chat_id=HR_CHAT_ID,
        photo=message.photo[-1].file_id,
        caption=f"📸 Nomzod rasmi: {data.get('full_name')}"
    )

    try:
        photo_path = await download_candidate_photo(message, data.get("full_name", "candidate"))
        pdf_path = create_candidate_pdf(data, photo_path)

        await bot.send_document(
            chat_id=HR_CHAT_ID,
            document=FSInputFile(pdf_path),
            caption=f"📄 Tayyor CV PDF: {data.get('full_name')}"
        )
    except Exception as e:
        await bot.send_message(
            chat_id=HR_CHAT_ID,
            text=f"⚠️ PDF yaratishda xatolik bo'ldi: {e}"
        )

    await goto_step(message, state, "external_cv")


@dp.message(StateFilter(Form.photo))
async def photo_required(message: Message):
    await message.answer(
        "📸 Iltimos, rasmni photo ko'rinishida yuboring.",
        reply_markup=action_kb()
    )


@dp.message(StateFilter(Form.external_cv), F.document)
async def process_external_cv(message: Message, state: FSMContext):
    doc = message.document
    if not doc.file_name.lower().endswith(".pdf"):
        await message.answer(
            "Iltimos, faqat PDF fayl yuboring.",
            reply_markup=external_cv_kb()
        )
        return

    await bot.send_document(
        chat_id=HR_CHAT_ID,
        document=doc.file_id,
        caption="📎 Nomzod yuborgan tayyor CV PDF"
    )
    await finish_flow(message, state)


@dp.message(StateFilter(Form.external_cv), F.text == "⏭ O'tkazib yuborish")
async def skip_external_cv(message: Message, state: FSMContext):
    await finish_flow(message, state)


@dp.message(StateFilter(Form.external_cv))
async def external_cv_required(message: Message):
    await message.answer(
        "📄 Iltimos, PDF fayl yuboring yoki ⏭ O'tkazib yuborish tugmasini bosing.",
        reply_markup=external_cv_kb()
    )


async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
