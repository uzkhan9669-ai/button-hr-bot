import asyncio
import os
import html
from datetime import datetime

from aiogram import Bot, Dispatcher, F
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

PDF_FONT_PATH = "DejaVuSans.ttf"
PDF_FONT_NAME = "DejaVuSans"

# =========================
# DATA
# =========================
UNITS = ["🏬 Магазины", "🏢 Офис", "📦 Склад"]

VACANCIES = {
    "🏬 Магазины": [
        "Sotuvchi-maslahatchi / Продавец-консультант",
        "Kassir / Кассир",
        "Oxrana / Охрана",
        "Tozalik hodimasi / Уборщица",
        "Helper / Помощник",
    ],
    "🏢 Офис": [
        "HR",
    ],
    "📦 Склад": [
        "Kladovshik / Кладовщик",
    ],
}

BRANCHES = {
    "🏬 Магазины": [
        "Chilonzor Andalus",
        "Chilonzor Integro",
        "Beruniy Korzinka",
        "Risoviy bozor Magnit",
        "Shaxriston Korzinka",
    ],
    "🏢 Офис": [
        "Ofis Andalus",
    ],
    "📦 Склад": [
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

# =========================
# FSM
# =========================
class CandidateForm(StatesGroup):
    choosing_unit = State()
    choosing_vacancy = State()
    choosing_branch = State()

    full_name = State()
    age = State()
    phone = State()
    district = State()
    family_status = State()
    education = State()
    studying_now = State()
    study_place = State()
    has_experience = State()
    last_job = State()
    work_period = State()
    leaving_reason = State()
    applying_position = State()
    preferred_branch = State()
    start_date = State()
    photo = State()
    consent = State()


# =========================
# KEYBOARDS
# =========================
def make_keyboard(items: list[str], with_back: bool = True) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=item)] for item in items]
    if with_back:
        rows.append([KeyboardButton(text="⬅️ Orqaga"), KeyboardButton(text="❌ Bekor qilish")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=item)] for item in UNITS],
        resize_keyboard=True
    )


def consent_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Roziman ✅")],
            [KeyboardButton(text="⬅️ Orqaga"), KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )


def family_keyboard() -> ReplyKeyboardMarkup:
    return make_keyboard(["Uylanmagan", "Uylangan", "Ajrashgan"])


def education_keyboard() -> ReplyKeyboardMarkup:
    return make_keyboard(["O‘rta", "O‘rta maxsus", "Oliy"])


def yes_no_keyboard() -> ReplyKeyboardMarkup:
    return make_keyboard(["Ha", "Yo‘q"])


# =========================
# HELPERS
# =========================
def escape_text(value: str) -> str:
    return html.escape(value if value else "-")


def wrap_text(text: str, width: int = 90) -> list[str]:
    words = str(text).split()
    if not words:
        return [""]
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def ensure_pdf_font():
    if not os.path.exists(PDF_FONT_PATH):
        raise FileNotFoundError(
            f"{PDF_FONT_PATH} topilmadi. Project papkasiga DejaVuSans.ttf faylini joylang."
        )
    try:
        pdfmetrics.getFont(PDF_FONT_NAME)
    except KeyError:
        pdfmetrics.registerFont(TTFont(PDF_FONT_NAME, PDF_FONT_PATH))


def build_candidate_caption(data: dict, user: Message) -> str:
    username = f"@{user.from_user.username}" if user.from_user.username else "—"
    return (
        "📥 <b>Yangi nomzod anketasi</b>\n\n"
        f"🏢 <b>Bo‘lim:</b> {escape_text(data.get('unit'))}\n"
        f"💼 <b>Vakansiya:</b> {escape_text(data.get('vacancy'))}\n"
        f"📍 <b>Filial:</b> {escape_text(data.get('branch'))}\n\n"
        f"👤 <b>F.I.Sh:</b> {escape_text(data.get('full_name'))}\n"
        f"🎂 <b>Yoshi:</b> {escape_text(data.get('age'))}\n"
        f"📞 <b>Telefon:</b> {escape_text(data.get('phone'))}\n"
        f"🏘 <b>Tuman:</b> {escape_text(data.get('district'))}\n"
        f"💍 <b>Oilaviy holati:</b> {escape_text(data.get('family_status'))}\n"
        f"🎓 <b>Ma’lumoti:</b> {escape_text(data.get('education'))}\n"
        f"📚 <b>Hozir o‘qiyaptimi:</b> {escape_text(data.get('studying_now'))}\n"
        f"🏫 <b>O‘qigan / o‘qiyotgan joyi:</b> {escape_text(data.get('study_place'))}\n"
        f"💼 <b>Ish tajribasi:</b> {escape_text(data.get('has_experience'))}\n"
        f"🏢 <b>Oxirgi ish joyi:</b> {escape_text(data.get('last_job'))}\n"
        f"⏳ <b>Ishlagan muddati:</b> {escape_text(data.get('work_period'))}\n"
        f"❓ <b>Ishdan ketish sababi:</b> {escape_text(data.get('leaving_reason'))}\n"
        f"📝 <b>Topshirayotgan lavozimi:</b> {escape_text(data.get('applying_position'))}\n"
        f"📌 <b>Qulay filial:</b> {escape_text(data.get('preferred_branch'))}\n"
        f"🚀 <b>Qachondan ishlay oladi:</b> {escape_text(data.get('start_date'))}\n\n"
        f"👤 <b>Telegram ID:</b> <code>{user.from_user.id}</code>\n"
        f"🔗 <b>Username:</b> {escape_text(username)}"
    )


def create_pdf(data: dict, tg_user_id: int, tg_username: str | None) -> str:
    ensure_pdf_font()

    os.makedirs("generated", exist_ok=True)
    safe_name = "".join(ch for ch in data.get("full_name", "candidate") if ch.isalnum() or ch in (" ", "_", "-")).strip()
    safe_name = safe_name.replace(" ", "_") or "candidate"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = f"generated/{safe_name}_{timestamp}.pdf"

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    y = height - 40

    def draw_line(label: str, value: str):
        nonlocal y, c
        lines = wrap_text(f"{label}: {value}", 95)
        for line in lines:
            if y < 50:
                c.showPage()
                c.setFont(PDF_FONT_NAME, 11)
                y = height - 40
            c.drawString(40, y, line)
            y -= 18

    c.setFont(PDF_FONT_NAME, 15)
    c.drawString(40, y, "BUTTON - Nomzod anketasi")
    y -= 30

    c.setFont(PDF_FONT_NAME, 11)
    fields = [
        ("Bo‘lim", data.get("unit", "-")),
        ("Vakansiya", data.get("vacancy", "-")),
        ("Filial", data.get("branch", "-")),
        ("F.I.Sh", data.get("full_name", "-")),
        ("Yoshi", data.get("age", "-")),
        ("Telefon", data.get("phone", "-")),
        ("Tuman", data.get("district", "-")),
        ("Oilaviy holati", data.get("family_status", "-")),
        ("Ma’lumoti", data.get("education", "-")),
        ("Hozir o‘qiyaptimi", data.get("studying_now", "-")),
        ("O‘qigan / o‘qiyotgan joyi", data.get("study_place", "-")),
        ("Ish tajribasi", data.get("has_experience", "-")),
        ("Oxirgi ish joyi", data.get("last_job", "-")),
        ("Ishlagan muddati", data.get("work_period", "-")),
        ("Ishdan ketish sababi", data.get("leaving_reason", "-")),
        ("Topshirayotgan lavozimi", data.get("applying_position", "-")),
        ("Qulay filial", data.get("preferred_branch", "-")),
        ("Qachondan ishlay oladi", data.get("start_date", "-")),
        ("Telegram ID", str(tg_user_id)),
        ("Telegram username", tg_username or "-"),
        ("Sana", datetime.now().strftime("%d.%m.%Y %H:%M:%S")),
    ]

    for label, value in fields:
        draw_line(label, str(value))

    c.save()
    return pdf_path


async def send_application_to_hr(bot: Bot, data: dict, source_message: Message):
    text_caption = build_candidate_caption(data, source_message)
    username = source_message.from_user.username

    # 1. Foto alohida yuboriladi
    if source_message.photo:
        biggest_photo = source_message.photo[-1]
        await bot.send_photo(
            chat_id=HR_CHAT_ID,
            photo=biggest_photo.file_id,
            caption=text_caption,
            parse_mode=ParseMode.HTML
        )

    # 2. PDF yuboriladi
    pdf_path = create_pdf(
        data=data,
        tg_user_id=source_message.from_user.id,
        tg_username=username,
    )

    try:
        pdf_file = FSInputFile(pdf_path)
        await bot.send_document(
            chat_id=HR_CHAT_ID,
            document=pdf_file,
            caption=f"📄 PDF anketa: {data.get('full_name', '-')}"
        )
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    # 3. Oddiy text message ham yuboriladi
    await bot.send_message(
        chat_id=HR_CHAT_ID,
        text=text_caption,
        parse_mode=ParseMode.HTML
    )


async def cancel_process(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Bekor qilindi. Boshidan boshlash uchun /start bosing.",
        reply_markup=ReplyKeyboardRemove()
    )


# =========================
# BOT SETUP
# =========================
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())


# =========================
# GLOBAL BUTTONS
# =========================
@dp.message(F.text == "❌ Bekor qilish")
async def global_cancel(message: Message, state: FSMContext):
    await cancel_process(message, state)


# =========================
# START
# =========================
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(CandidateForm.choosing_unit)
    await message.answer(
        "Assalomu alaykum!\n"
        "BUTTON kompaniyasining HR-botiga xush kelibsiz.\n\n"
        "Iltimos, bo‘limni tanlang:",
        reply_markup=main_menu_keyboard()
    )


# =========================
# UNIT
# =========================
@dp.message(CandidateForm.choosing_unit)
async def choose_unit(message: Message, state: FSMContext):
    if message.text not in UNITS:
        await message.answer("Iltimos, tugmalardan birini tanlang.")
        return

    await state.update_data(unit=message.text)
    await state.set_state(CandidateForm.choosing_vacancy)

    await message.answer(
        "Vakansiyani tanlang:",
        reply_markup=make_keyboard(VACANCIES[message.text])
    )


# =========================
# VACANCY
# =========================
@dp.message(CandidateForm.choosing_vacancy)
async def choose_vacancy(message: Message, state: FSMContext):
    if message.text == "⬅️ Orqaga":
        await state.set_state(CandidateForm.choosing_unit)
        await message.answer("Bo‘limni tanlang:", reply_markup=main_menu_keyboard())
        return

    data = await state.get_data()
    unit = data.get("unit")
    allowed = VACANCIES.get(unit, [])

    if message.text not in allowed:
        await message.answer("Iltimos, tugmalardan birini tanlang.")
        return

    await state.update_data(vacancy=message.text)
    await state.set_state(CandidateForm.choosing_branch)

    await message.answer(
        "Filialni tanlang:",
        reply_markup=make_keyboard(BRANCHES[unit])
    )


# =========================
# BRANCH
# =========================
@dp.message(CandidateForm.choosing_branch)
async def choose_branch(message: Message, state: FSMContext):
    if message.text == "⬅️ Orqaga":
        data = await state.get_data()
        unit = data.get("unit")
        await state.set_state(CandidateForm.choosing_vacancy)
        await message.answer(
            "Vakansiyani tanlang:",
            reply_markup=make_keyboard(VACANCIES[unit])
        )
        return

    data = await state.get_data()
    unit = data.get("unit")
    allowed = BRANCHES.get(unit, [])

    if message.text not in allowed:
        await message.answer("Iltimos, tugmalardan birini tanlang.")
        return

    await state.update_data(branch=message.text)

    branch_info = LOCATIONS.get(message.text, {})
    address = branch_info.get("address", "Manzil kiritilmagan")
    map_link = branch_info.get("map", "-")

    await message.answer(
        f"📍 <b>{escape_text(message.text)}</b>\n"
        f"📌 Manzil: {escape_text(address)}\n"
        f"🗺 Xarita: {escape_text(map_link)}",
        reply_markup=ReplyKeyboardRemove()
    )

    await state.set_state(CandidateForm.full_name)
    await message.answer("1. Ismingiz va familiyangizni kiriting:")


# =========================
# FORM QUESTIONS
# =========================
@dp.message(CandidateForm.full_name)
async def q_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await state.set_state(CandidateForm.age)
    await message.answer("2. Yoshingiz:")


@dp.message(CandidateForm.age)
async def q_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(CandidateForm.phone)
    await message.answer("3. Telefon raqamingiz:")


@dp.message(CandidateForm.phone)
async def q_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(CandidateForm.district)
    await message.answer("4. Qaysi tumanda yashaysiz?")


@dp.message(CandidateForm.district)
async def q_district(message: Message, state: FSMContext):
    await state.update_data(district=message.text)
    await state.set_state(CandidateForm.family_status)
    await message.answer("5. Oilaviy holatingiz:", reply_markup=family_keyboard())


@dp.message(CandidateForm.family_status)
async def q_family_status(message: Message, state: FSMContext):
    if message.text == "⬅️ Orqaga":
        await state.set_state(CandidateForm.district)
        await message.answer("4. Qaysi tumanda yashaysiz?", reply_markup=ReplyKeyboardRemove())
        return

    if message.text not in ["Uylanmagan", "Uylangan", "Ajrashgan"]:
        await message.answer("Iltimos, tugmalardan birini tanlang.")
        return

    await state.update_data(family_status=message.text)
    await state.set_state(CandidateForm.education)
    await message.answer("6. Ma’lumotingiz:", reply_markup=education_keyboard())


@dp.message(CandidateForm.education)
async def q_education(message: Message, state: FSMContext):
    if message.text == "⬅️ Orqaga":
        await state.set_state(CandidateForm.family_status)
        await message.answer("5. Oilaviy holatingiz:", reply_markup=family_keyboard())
        return

    if message.text not in ["O‘rta", "O‘rta maxsus", "Oliy"]:
        await message.answer("Iltimos, tugmalardan birini tanlang.")
        return

    await state.update_data(education=message.text)
    await state.set_state(CandidateForm.studying_now)
    await message.answer("7. Hozir o‘qiyapsizmi?", reply_markup=yes_no_keyboard())


@dp.message(CandidateForm.studying_now)
async def q_studying_now(message: Message, state: FSMContext):
    if message.text == "⬅️ Orqaga":
        await state.set_state(CandidateForm.education)
        await message.answer("6. Ma’lumotingiz:", reply_markup=education_keyboard())
        return

    if message.text not in ["Ha", "Yo‘q"]:
        await message.answer("Iltimos, tugmalardan birini tanlang.")
        return

    await state.update_data(studying_now=message.text)
    await state.set_state(CandidateForm.study_place)
    await message.answer("8. Qayerda o‘qigansiz yoki o‘qiyapsiz?", reply_markup=ReplyKeyboardRemove())


@dp.message(CandidateForm.study_place)
async def q_study_place(message: Message, state: FSMContext):
    await state.update_data(study_place=message.text)
    await state.set_state(CandidateForm.has_experience)
    await message.answer("9. Ish tajribangiz bormi?", reply_markup=yes_no_keyboard())


@dp.message(CandidateForm.has_experience)
async def q_has_experience(message: Message, state: FSMContext):
    if message.text == "⬅️ Orqaga":
        await state.set_state(CandidateForm.study_place)
        await message.answer("8. Qayerda o‘qigansiz yoki o‘qiyapsiz?", reply_markup=ReplyKeyboardRemove())
        return

    if message.text not in ["Ha", "Yo‘q"]:
        await message.answer("Iltimos, tugmalardan birini tanlang.")
        return

    await state.update_data(has_experience=message.text)
    await state.set_state(CandidateForm.last_job)
    await message.answer("10. Oxirgi ish joyingiz:")


@dp.message(CandidateForm.last_job)
async def q_last_job(message: Message, state: FSMContext):
    await state.update_data(last_job=message.text)
    await state.set_state(CandidateForm.work_period)
    await message.answer("11. Qancha vaqt ishlagansiz?")


@dp.message(CandidateForm.work_period)
async def q_work_period(message: Message, state: FSMContext):
    await state.update_data(work_period=message.text)
    await state.set_state(CandidateForm.leaving_reason)
    await message.answer("12. Nega ishdan ketgansiz?")


@dp.message(CandidateForm.leaving_reason)
async def q_leaving_reason(message: Message, state: FSMContext):
    await state.update_data(leaving_reason=message.text)
    await state.set_state(CandidateForm.applying_position)
    await message.answer("13. Qaysi lavozimga topshiryapsiz?")


@dp.message(CandidateForm.applying_position)
async def q_applying_position(message: Message, state: FSMContext):
    await state.update_data(applying_position=message.text)
    await state.set_state(CandidateForm.preferred_branch)
    await message.answer("14. Qulay ish filiali?")


@dp.message(CandidateForm.preferred_branch)
async def q_preferred_branch(message: Message, state: FSMContext):
    await state.update_data(preferred_branch=message.text)
    await state.set_state(CandidateForm.start_date)
    await message.answer("15. Qachondan ish boshlay olasiz?")


@dp.message(CandidateForm.start_date)
async def q_start_date(message: Message, state: FSMContext):
    await state.update_data(start_date=message.text)
    await state.set_state(CandidateForm.photo)
    await message.answer(
        "📷 Iltimos, o‘zingizni rasmingizni yuboring\n"
        "(selfie yoki oddiy rasm)."
    )


# =========================
# PHOTO
# =========================
@dp.message(CandidateForm.photo, F.photo)
async def q_photo(message: Message, state: FSMContext):
    await state.update_data(photo_file_id=message.photo[-1].file_id)
    await state.set_state(CandidateForm.consent)
    await message.answer(
        "Shaxsiy ma’lumotlaringizni qayta ishlash va BUTTON kompaniyasiga yuborishga rozimisiz?",
        reply_markup=consent_keyboard()
    )


@dp.message(CandidateForm.photo)
async def q_photo_invalid(message: Message, state: FSMContext):
    if message.text == "⬅️ Orqaga":
        await state.set_state(CandidateForm.start_date)
        await message.answer("15. Qachondan ish boshlay olasiz?", reply_markup=ReplyKeyboardRemove())
        return

    await message.answer("Iltimos, foto yuboring.")


# =========================
# CONSENT
# =========================
@dp.message(CandidateForm.consent)
async def q_consent(message: Message, state: FSMContext):
    if message.text == "⬅️ Orqaga":
        await state.set_state(CandidateForm.photo)
        await message.answer(
            "📷 Iltimos, o‘zingizni rasmingizni yuboring\n(selfie yoki oddiy rasm).",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    if message.text != "Roziman ✅":
        await message.answer("Davom etish uchun 'Roziman ✅' tugmasini bosing.")
        return

    data = await state.get_data()

    try:
        await send_application_to_hr(bot, data, message)
        await message.answer(
            "✅ Rahmat! So‘rovnomangiz muvaffaqiyatli yuborildi.\n"
            "Tez orada HR mutaxassisimiz siz bilan bog‘lanadi.",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        await message.answer(
            f"Xatolik yuz berdi: {escape_text(str(e))}",
            reply_markup=ReplyKeyboardRemove()
        )
    finally:
        await state.clear()


# =========================
# FALLBACK
# =========================
@dp.message()
async def fallback_handler(message: Message):
    await message.answer("Botni ishga tushirish uchun /start bosing.")


# =========================
# MAIN
# =========================
async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
