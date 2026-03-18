import os
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

BOT_TOKEN = os.getenv("BOT_TOKEN")
HR_CHAT_ID = os.getenv("HR_CHAT_ID")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi")
if not HR_CHAT_ID:
    raise ValueError("HR_CHAT_ID topilmadi")

HR_CHAT_ID = int(HR_CHAT_ID)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

users = {}

FONT_NAME = "DejaVuSans"
FONT_PATHS = [
    "DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
]


def register_font():
    for path in FONT_PATHS:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(FONT_NAME, path))
                return
            except Exception:
                pass
    raise FileNotFoundError("DejaVuSans.ttf topilmadi")


def wrap_text(text: str, max_len: int = 85) -> list[str]:
    words = str(text).split()
    lines = []
    current = ""

    for word in words:
        test = f"{current} {word}".strip()
        if len(test) <= max_len:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines if lines else [""]


def create_pdf(data: dict, user_id: int, username: str | None) -> str:
    register_font()

    os.makedirs("generated", exist_ok=True)

    safe_name = "".join(c for c in data.get("name", "candidate") if c.isalnum() or c in (" ", "_", "-")).strip()
    safe_name = safe_name.replace(" ", "_") or "candidate"

    file_path = f"generated/{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    y = height - 40

    c.setFont(FONT_NAME, 15)
    c.drawString(40, y, "BUTTON - Nomzod anketasi")
    y -= 30

    c.setFont(FONT_NAME, 11)

    fields = [
        ("Ism", data.get("name", "-")),
        ("Yosh", data.get("age", "-")),
        ("Telefon", data.get("phone", "-")),
        ("Filial", data.get("branch", "-")),
        ("Oxirgi ish joyi", data.get("job", "-")),
        ("Telegram ID", str(user_id)),
        ("Username", username or "-"),
        ("Sana", datetime.now().strftime("%d.%m.%Y %H:%M")),
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
    return file_path


@dp.message(CommandStart())
async def start(message: types.Message):
    users[message.from_user.id] = {"step": "name"}
    await message.answer(
        "Assalomu alaykum.\n"
        "BUTTON HR botiga xush kelibsiz.\n\n"
        "1. Ismingizni yozing:"
    )


@dp.message(F.photo)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id

    if user_id not in users:
        await message.answer("Avval /start bosing.")
        return

    if users[user_id].get("step") != "photo":
        await message.answer("Hozir foto yuborish vaqti emas.")
        return

    users[user_id]["photo"] = message.photo[-1].file_id
    data = users[user_id]

    text = (
        "📥 Yangi nomzod\n\n"
        f"👤 Ism: {data.get('name', '-')}\n"
        f"🎂 Yosh: {data.get('age', '-')}\n"
        f"📞 Telefon: {data.get('phone', '-')}\n"
        f"📍 Filial: {data.get('branch', '-')}\n"
        f"💼 Oxirgi ish joyi: {data.get('job', '-')}"
    )

    await bot.send_photo(
        HR_CHAT_ID,
        photo=data["photo"],
        caption=text
    )

    pdf_path = create_pdf(
        data=data,
        user_id=message.from_user.id,
        username=message.from_user.username
    )

    try:
        await bot.send_document(
            HR_CHAT_ID,
            FSInputFile(pdf_path),
            caption=f"📄 PDF anketa: {data.get('name', '-')}"
        )
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    await bot.send_message(HR_CHAT_ID, text)
    await message.answer("✅ Rahmat! Arizangiz yuborildi.")
    del users[user_id]


@dp.message()
async def form_handler(message: types.Message):
    user_id = message.from_user.id

    if user_id not in users:
        await message.answer("Botni boshlash uchun /start bosing.")
        return

    step = users[user_id]["step"]

    if step == "name":
        users[user_id]["name"] = message.text
        users[user_id]["step"] = "age"
        await message.answer("2. Yoshingiz:")
        return

    if step == "age":
        users[user_id]["age"] = message.text
        users[user_id]["step"] = "phone"
        await message.answer("3. Telefon raqamingiz:")
        return

    if step == "phone":
        users[user_id]["phone"] = message.text
        users[user_id]["step"] = "branch"
        await message.answer("4. Qaysi filialda ishlamoqchisiz?")
        return

    if step == "branch":
        users[user_id]["branch"] = message.text
        users[user_id]["step"] = "job"
        await message.answer("5. Oxirgi ish joyingiz?")
        return

    if step == "job":
        users[user_id]["job"] = message.text
        users[user_id]["step"] = "photo"
        await message.answer("6. Rasmingizni yuboring.")
        return

    if step == "photo":
        await message.answer("Iltimos, foto yuboring.")
        return


async def main():
    print("Bot ishga tushdi")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
