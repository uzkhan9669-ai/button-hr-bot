import asyncio
import os
import re
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from dotenv import load_dotenv
from fpdf import FPDF

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
HR_CHAT_ID = os.getenv("HR_CHAT_ID")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi. .env faylni tekshiring.")

if not HR_CHAT_ID:
    raise ValueError("HR_CHAT_ID topilmadi. .env faylni tekshiring.")

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


def start_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Anketani boshlash")]
        ],
        resize_keyboard=True
    )


def position_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👔 Sotuvchi-maslahatchi")],
            [KeyboardButton(text="💰 Kassir")],
            [KeyboardButton(text="📦 Skladovshik")],
            [KeyboardButton(text="🛡 Qo'riqchi")]
        ],
        resize_keyboard=True
    )


def branch_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏬 Risoviy bozor - Magnit")],
            [KeyboardButton(text="🏬 Chilonzor - Andalus")],
            [KeyboardButton(text="🏬 Beruniy - Korzinka")],
            [KeyboardButton(text="🏬 Shayxontohur - Makon")],
            [KeyboardButton(text="🔄 Farqi yo'q")]
        ],
        resize_keyboard=True
    )


def yes_no_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Ha"), KeyboardButton(text="❌ Yo'q")]
        ],
        resize_keyboard=True
    )


def schedule_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🕘 To'liq smena")],
            [KeyboardButton(text="🌅 Faqat kunduzgi"), KeyboardButton(text="🌙 Faqat kechki")],
            [KeyboardButton(text="🔄 Moslashuvchan")]
        ],
        resize_keyboard=True
    )


def clean_filename(text: str) -> str:
    text = text.strip().replace(" ", "_")
    return re.sub(r"[^A-Za-z0-9_]+", "", text) or "candidate"


def create_candidate_pdf(data: dict, photo_path: str) -> str:
    candidate_name = data.get("full_name", "candidate")
    safe_name = clean_filename(candidate_name)
    pdf_path = TMP_DIR / f"CV_{safe_name}.pdf"

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "BUTTON CV", ln=True, align="C")
    pdf.ln(4)

    if photo_path and Path(photo_path).exists():
        try:
            pdf.image(photo_path, x=150, y=20, w=35)
        except Exception:
            pass

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Nomzod haqida ma'lumot", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", size=11)

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
        pdf.set_font("Helvetica", "B", 11)
        pdf.multi_cell(55, 8, f"{label}: ", border=0)
        y_before = pdf.get_y()
        pdf.set_xy(65, y_before - 8)
        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(0, 8, str(value), border=0)
        pdf.ln(1)

    pdf.output(str(pdf_path))
    return str(pdf_path)


async def download_candidate_photo(message: Message, full_name: str) -> str:
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)

    safe_name = clean_filename(full_name)
    photo_path = TMP_DIR / f"{safe_name}_photo.jpg"

    await bot.download_file(file.file_path, destination=photo_path)
    return str(photo_path)


@dp.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🤖 <b>Assalomu alaykum!</b>\n\n"
        "BUTTON erkaklar kiyim do'koniga ishga qabul botiga xush kelibsiz.\n\n"
        "📋 Iltimos, quyidagi qisqa anketani to'ldiring.",
        reply_markup=start_keyboard()
    )


@dp.message(F.text == "✅ Anketani boshlash")
async def start_form(message: Message, state: FSMContext):
    await state.set_state(Form.full_name)
    await message.answer(
        "👤 Ism va familiyangizni yozing:",
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message(Form.full_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    await state.set_state(Form.age)
    await message.answer("🎂 Yoshingiz nechida?")


@dp.message(Form.age)
async def get_age(message: Message, state: FSMContext):
    age = message.text.strip()
    if not age.isdigit():
        await message.answer("⚠️ Iltimos, yoshni raqam bilan kiriting. Masalan: 22")
        return

    await state.update_data(age=age)
    await state.set_state(Form.phone)
    await message.answer("📱 Telefon raqamingizni yozing:\nMasalan: +998901234567")


@dp.message(Form.phone)
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    await state.set_state(Form.position)
    await message.answer(
        "💼 Qaysi lavozimda ishlamoqchisiz?",
        reply_markup=position_keyboard()
    )


@dp.message(Form.position)
async def get_position(message: Message, state: FSMContext):
    await state.update_data(position=message.text.strip())
    await state.set_state(Form.branch)
    await message.answer(
        "📍 Qaysi filial yoki hudud sizga qulay?",
        reply_markup=branch_keyboard()
    )


@dp.message(Form.branch)
async def get_branch(message: Message, state: FSMContext):
    await state.update_data(branch=message.text.strip())
    await state.set_state(Form.experience)
    await message.answer(
        "⭐ Shu lavozim bo'yicha ish tajribangiz bormi?",
        reply_markup=yes_no_keyboard()
    )


@dp.message(Form.experience)
async def get_experience(message: Message, state: FSMContext):
    await state.update_data(experience=message.text.strip())
    await state.set_state(Form.experience_text)
    await message.answer(
        "🧠 Tajribangiz haqida qisqacha yozing.\n"
        "Agar bo'lmasa: yo'q deb yozing.",
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message(Form.experience_text)
async def get_experience_text(message: Message, state: FSMContext):
    await state.update_data(experience_text=message.text.strip())
    await state.set_state(Form.schedule)
    await message.answer(
        "🕒 Qaysi ish grafigi sizga qulay?",
        reply_markup=schedule_keyboard()
    )


@dp.message(Form.schedule)
async def get_schedule(message: Message, state: FSMContext):
    await state.update_data(schedule=message.text.strip())
    await state.set_state(Form.salary)
    await message.answer(
        "💰 Kutilayotgan oylik maoshingiz qancha?",
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message(Form.salary)
async def get_salary(message: Message, state: FSMContext):
    await state.update_data(salary=message.text.strip())
    await state.set_state(Form.start_date)
    await message.answer("🚀 Qachondan ish boshlay olasiz?")


@dp.message(Form.start_date)
async def get_start_date(message: Message, state: FSMContext):
    await state.update_data(start_date=message.text.strip())
    await state.set_state(Form.comment)
    await message.answer("💬 Qo'shimcha ma'lumot yoki izoh bo'lsa yozing.\nBo'lmasa: yo'q")


@dp.message(Form.comment)
async def get_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text.strip())
    await state.set_state(Form.photo)
    await message.answer(
        "📸 Iltimos, o'zingizning rasmingizni yuboring\n"
        "(yuzingiz aniq ko'rinadigan bo'lsin)"
    )


@dp.message(Form.photo, F.photo)
async def get_photo(message: Message, state: FSMContext):
    data = await state.get_data()

    telegram_username = message.from_user.username if message.from_user.username else "yoq"
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

    await bot.send_message(chat_id=int(HR_CHAT_ID), text=text)

    photo = message.photo[-1]
    await bot.send_photo(
        chat_id=int(HR_CHAT_ID),
        photo=photo.file_id,
        caption=f"📸 Nomzod rasmi: {data.get('full_name')}"
    )

    try:
        photo_path = await download_candidate_photo(message, data.get("full_name", "candidate"))
        pdf_path = create_candidate_pdf(data, photo_path)

        with open(pdf_path, "rb") as pdf_file:
            await bot.send_document(
                chat_id=int(HR_CHAT_ID),
                document=pdf_file,
                caption=f"📄 Tayyor CV PDF: {data.get('full_name')}"
            )
    except Exception as e:
        await bot.send_message(
            chat_id=int(HR_CHAT_ID),
            text=f"⚠️ PDF yaratishda xatolik bo'ldi: {e}"
        )

    await message.answer(
        "✅ Rahmat! Sizning anketa, rasm va CV PDF qabul qilindi.\n"
        "BUTTON HR jamoasi tez orada siz bilan bog'lanadi.",
        reply_markup=ReplyKeyboardRemove()
    )

    await state.clear()


@dp.message(Form.photo)
async def photo_required(message: Message):
    await message.answer("📸 Iltimos, rasmni photo ko'rinishida yuboring.")


async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
