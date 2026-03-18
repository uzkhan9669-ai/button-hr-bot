import os
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile
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

# =========================
# BOT
# =========================
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# =========================
# TEMP STORAGE
# =========================
users = {}

QUESTIONS = [
    ("unit", "1. Bo‘limni yozing:\n(Magazin / Ofis / Sklad)"),
    ("vacancy", "2. Vakansiyani yozing:"),
    ("branch", "3. Filialni yozing:"),
    ("full_name", "4. Ismingiz va familiyangiz:"),
    ("age", "5. Yoshingiz:"),
    ("phone", "6. Telefon raqamingiz:"),
    ("district", "7. Qaysi tumanda yashaysiz?"),
    ("family_status", "8. Oilaviy holatingiz:"),
    ("education", "9. Ma’lumotingiz:"),
    ("studying_now", "10. Hozir o‘qiyapsizmi?"),
    ("study_place", "11. Qayerda o‘qigansiz yoki o‘qiyapsiz?"),
    ("has_experience", "12. Ish tajribangiz bormi?"),
    ("last_job", "13. Oxirgi ish joyingiz:"),
    ("work_period", "14. Qancha vaqt ishlagansiz?"),
    ("leaving_reason", "15. Nega ishdan ketgansiz?"),
    ("applying_position", "16. Qaysi lavozimga topshiryapsiz?"),
    ("preferred_branch", "17. Qulay ish filiali:"),
    ("start_date", "18. Qachondan ish boshlay olasiz?"),
]

FONT_NAME = "DejaVuSans"


# =========================
# HELPERS
# =========================
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
    c.drawString(40, y, "BUTTON - Nomzod anketasi")
    y -= 30

    c.setFont(FONT_NAME, 11)

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
    username = f"@{user.from_user.username}" if user.from_user.username else "—"

    return (
        "📥 <b>Yangi nomzod anketasi</b>\n\n"
        f"🏢 <b>Bo‘lim:</b> {data.get('unit', '-')}\n"
        f"💼 <b>Vakansiya:</b> {data.get('vacancy', '-')}\n"
        f"📍 <b>Filial:</b> {data.get('branch', '-')}\n\n"
        f"👤 <b>F.I.Sh:</b> {data.get('full_name', '-')}\n"
        f"🎂 <b>Yoshi:</b> {data.get('age', '-')}\n"
        f"📞 <b>Telefon:</b> {data.get('phone', '-')}\n"
        f"🏘 <b>Tuman:</b> {data.get('district', '-')}\n"
        f"💍 <b>Oilaviy holati:</b> {data.get('family_status', '-')}\n"
        f"🎓 <b>Ma’lumoti:</b> {data.get('education', '-')}\n"
        f"📚 <b>Hozir o‘qiyaptimi:</b> {data.get('studying_now', '-')}\n"
        f"🏫 <b>O‘qigan / o‘qiyotgan joyi:</b> {data.get('study_place', '-')}\n"
        f"💼 <b>Ish tajribasi:</b> {data.get('has_experience', '-')}\n"
        f"🏢 <b>Oxirgi ish joyi:</b> {data.get('last_job', '-')}\n"
        f"⏳ <b>Ishlagan muddati:</b> {data.get('work_period', '-')}\n"
        f"❓ <b>Ishdan ketish sababi:</b> {data.get('leaving_reason', '-')}\n"
        f"📝 <b>Topshirayotgan lavozimi:</b> {data.get('applying_position', '-')}\n"
        f"📌 <b>Qulay filial:</b> {data.get('preferred_branch', '-')}\n"
        f"🚀 <b>Qachondan ishlay oladi:</b> {data.get('start_date', '-')}\n\n"
        f"🆔 <b>Telegram ID:</b> <code>{user.from_user.id}</code>\n"
        f"🔗 <b>Username:</b> {username}"
    )


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
            caption=f"📄 PDF anketa: {data.get('full_name', '-')}"
        )
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    await bot.send_message(
        chat_id=HR_CHAT_ID,
        text=text
    )


# =========================
# START
# =========================
@dp.message(CommandStart())
async def start_handler(message: Message):
    users[message.from_user.id] = {
        "step_index": 0,
        "started": True,
    }

    await message.answer(
        "Assalomu alaykum!\n"
        "BUTTON HR botiga xush kelibsiz.\n\n"
        "Bekor qilish uchun: /cancel\n\n"
        f"{QUESTIONS[0][1]}"
    )


@dp.message(F.text == "/cancel")
async def cancel_handler(message: Message):
    users.pop(message.from_user.id, None)
    await message.answer("Bekor qilindi. Qaytadan boshlash uchun /start bosing.")


# =========================
# PHOTO
# =========================
@dp.message(F.photo)
async def photo_handler(message: Message):
    user_id = message.from_user.id

    if user_id not in users:
        await message.answer("Avval /start bosing.")
        return

    user_data = users[user_id]

    if user_data.get("awaiting_photo") is not True:
        await message.answer("Hozir foto yuborish vaqti emas.")
        return

    user_data["photo_file_id"] = message.photo[-1].file_id
    user_data["awaiting_photo"] = False
    user_data["awaiting_consent"] = True

    await message.answer(
        "Shaxsiy ma’lumotlaringizni qayta ishlash va BUTTON kompaniyasiga yuborishga rozimisiz?\n\n"
        "Yozing: Roziman"
    )


# =========================
# TEXT FLOW
# =========================
@dp.message()
async def text_handler(message: Message):
    user_id = message.from_user.id

    if user_id not in users:
        await message.answer("Botni ishga tushirish uchun /start bosing.")
        return

    user_data = users[user_id]

    if user_data.get("awaiting_photo"):
        await message.answer("Iltimos, foto yuboring.")
        return

    if user_data.get("awaiting_consent"):
        if (message.text or "").strip().lower() != "roziman":
            await message.answer("Davom etish uchun 'Roziman' deb yozing.")
            return

        try:
            await send_to_hr(user_data, message)
            await message.answer(
                "✅ Rahmat! So‘rovnomangiz muvaffaqiyatli yuborildi.\n"
                "Tez orada HR mutaxassisimiz siz bilan bog‘lanadi."
            )
        except Exception as e:
            await message.answer(f"Xatolik yuz berdi: {e}")

        users.pop(user_id, None)
        return

    step_index = user_data.get("step_index", 0)

    if step_index >= len(QUESTIONS):
        user_data["awaiting_photo"] = True
        await message.answer("📷 Iltimos, o‘zingizni rasmingizni yuboring.")
        return

    field_name, question_text = QUESTIONS[step_index]
    user_data[field_name] = message.text
    user_data["step_index"] = step_index + 1

    if user_data["step_index"] < len(QUESTIONS):
        next_question = QUESTIONS[user_data["step_index"]][1]
        await message.answer(next_question)
    else:
        user_data["awaiting_photo"] = True
        await message.answer("📷 Iltimos, o‘zingizni rasmingizni yuboring.")


# =========================
# MAIN
# =========================
async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
