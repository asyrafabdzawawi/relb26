import os
import json
from datetime import datetime, date, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

import firebase_admin
from firebase_admin import credentials, storage

import gspread
from google.oauth2.service_account import Credentials


# ==================================================
# CONFIG
# ==================================================
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SHEET_ID = "1bBnCG5ODsqQspRj_-fViRIXJGMo0w7hgbTH6p56gNuM"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1bBnCG5ODsqQspRj_-fViRIXJGMo0w7hgbTH6p56gNuM/edit"
FIREBASE_BUCKET = "relief-31bc6.firebasestorage.app"

ADMIN_IDS = [522707506]


# ==================================================
# FIREBASE INIT
# ==================================================
firebase_creds = credentials.Certificate(
    json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT_JSON"])
)
firebase_admin.initialize_app(firebase_creds, {"storageBucket": FIREBASE_BUCKET})
bucket = storage.bucket()


# ==================================================
# GOOGLE SHEET INIT
# ==================================================
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
sheet_creds = Credentials.from_service_account_info(
    json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]), scopes=SCOPES
)
gc = gspread.authorize(sheet_creds)
sheet = gc.open_by_key(SHEET_ID).sheet1


# ==================================================
# DATA
# ==================================================
MASA_LIST = ["7.45–8.15", "8.15–8.45", "8.45–9.15", "9.15–9.45", "9.45–10.15",
             "10.15–10.45", "10.45–11.15", "11.15–11.45", "11.45–12.15", "12.15–12.45", "12.45–1.15"]

GURU_LIST = [
    "Mohd Faizal Bin Ahmad","Shahairi Bin Suratman","Mohd Khairul Nizam Bin Hazari",
    "Wan Nurhaslinda Binti Wan Mazuki","Abdul Ghani Bin Abdul Karim","Abu Bakar Bin Sahari",
    "Azizul Rahim Bin Ismail","Azlinawati Binti Yaakob","Azura Binti Mohamad","Basirah Binti Bacharudin",
    "Chithrra A/P Damodharan","Endhumathy A/P Veeraiah","Fadzilah Binti Jahaya","Faridah Binti Muda",
    "Masita Binti Ismail","Mazura Binti Abdul Aziz","Mohd Asri Bin Isma'ail","Mohd Huzaini Bin Husin",
    "Mohd Noor Safwan Bin Md Noor","Muhammad Asyraf Bin Abdullah Zawawi","Muhammad Yusuf Bin Zainol Abidin",
    "Noor Aizah Binti Ilias","Noor Azlin Binti Teh","Noor Azlinda Binti Abdullah",
    "Noor Jareena Binti Mohamud Kassim","Normasita Bt Elias","Norul Fazlin Binti Zainal Karib",
    "Nur Imanina Binti Shaari","Nurul Asyiqin Binti Osman","Nurulzahilah Binti Ibrahim",
    "Puoneswari A/P Sundarajoo","Roslan Bin Mohd Yusoff","Rusmaliza Binti Abdul Rahman",
    "Siti Rohayu Binti Zakaria","Siti Munirah Binti Munadzir","Suria Binti Ismail",
    "Umamageswari A/P Muniandy","Uzma Farzana Binti Ridzuan","Wan Nur Aqielah Binti Wan Shahar",
    "Za'aimah Binti Shakir","Zarina Binti Mohamad","Zuraini Binti Hassan"
]

KELAS_LIST = ["1 Amber","1 Amethyst","1 Aquamarine","2 Amber","2 Amethyst","2 Aquamarine",
              "3 Amber","3 Amethyst","3 Aquamarine","4 Amber","4 Amethyst","4 Aquamarine",
              "5 Amber","5 Amethyst","5 Aquamarine","6 Amber","6 Amethyst","6 Aquamarine"]

SUBJEK_LIST = ["Bahasa Melayu","Bahasa Inggeris","Bahasa Arab","Sains","Sejarah","Matematik",
               "RBT","PJPK","PSV","Muzik","Moral","Pendidikan Islam"]


# ==================================================
# 🔥 ULTRA HELPER — GRID KEYBOARD
# ==================================================
def build_grid_keyboard(items, callback_prefix, cols=2, emoji=""):
    keyboard, row = [], []

    for item in items:
        label = f"{emoji} {item}" if emoji else item
        row.append(InlineKeyboardButton(label, callback_data=f"{callback_prefix}|{item}"))

        if len(row) == cols:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


# ==================================================
# UTIL DELETE MESSAGE
# ==================================================
async def delete_last_message(context, chat_id):
    try:
        last_id = context.user_data.get("last_message_id")
        if last_id:
            await context.bot.delete_message(chat_id, last_id)
    except:
        pass


async def send_menu(update_or_query, context, text, keyboard, parse="Markdown"):
    chat_id = update_or_query.effective_chat.id

    await delete_last_message(context, chat_id)

    msg = await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=keyboard,
        parse_mode=parse
    )

    context.user_data["last_message_id"] = msg.message_id


# ==================================================
# START
# ==================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    reply_keyboard = [
        [KeyboardButton("🟢 Hari Ini"), KeyboardButton("📅 Tarikh Lain")],
        [KeyboardButton("📊 Semak Rekod Hari Ini"), KeyboardButton("📊 Lihat Rekod Penuh (Admin)")]
    ]

    await update.message.reply_text(
        "🤖 *Relief Check-In Tracker*\n\nPilih tindakan:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),
        parse_mode="Markdown"
    )


# ==================================================
# HARI INI
# ==================================================
async def hari_ini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["tarikh"] = datetime.now().strftime("%Y-%m-%d")

    keyboard = build_grid_keyboard(MASA_LIST, "masa", cols=2)

    await send_menu(
        update,
        context,
        "📅 Tarikh: *Hari Ini*\n\n⏰ Pilih masa:",
        keyboard
    )


# ==================================================
# TARIKH LAIN
# ==================================================
async def tarikh_lain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = date.today()
    context.user_data["calendar_year"] = today.year
    context.user_data["calendar_month"] = today.month

    await show_calendar(update, context)


# ==================================================
# CALENDAR
# ==================================================
async def show_calendar(update, context):

    year = context.user_data["calendar_year"]
    month = context.user_data["calendar_month"]
    today = date.today()

    first_day = date(year, month, 1)
    start_weekday = first_day.weekday()
    days_in_month = (date(year + (month // 12), ((month % 12) + 1), 1) - timedelta(days=1)).day

    keyboard = []

    keyboard.append([
        InlineKeyboardButton("⬅️", callback_data=f"cal_nav|{year}|{month-1}"),
        InlineKeyboardButton(f"{first_day.strftime('%B')} {year}", callback_data="noop"),
        InlineKeyboardButton("➡️", callback_data=f"cal_nav|{year}|{month+1}")
    ])

    weekdays = ["Mo","Tu","We","Th","Fr","Sa","Su"]
    keyboard.append([InlineKeyboardButton(d, callback_data="noop") for d in weekdays])

    row = []
    for _ in range(start_weekday):
        row.append(InlineKeyboardButton(" ", callback_data="noop"))

    for day in range(1, days_in_month + 1):
        tarikh_ini = date(year, month, day)
        label = f"🟢{day}" if tarikh_ini == today else str(day)

        row.append(InlineKeyboardButton(label, callback_data=f"cal_day|{year}|{month}|{day}"))

        if len(row) == 7:
            keyboard.append(row)
            row = []

    if row:
        while len(row) < 7:
            row.append(InlineKeyboardButton(" ", callback_data="noop"))
        keyboard.append(row)

    await send_menu(update, context, "🗓 Pilih tarikh rekod:", InlineKeyboardMarkup(keyboard), parse=None)


# ==================================================
# CALLBACK FLOW
# ==================================================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    key, *rest = data.split("|")
    value = rest[0] if rest else None

    if key == "masa":
        context.user_data["masa"] = value
        keyboard = build_grid_keyboard(GURU_LIST, "guru_pengganti", cols=3, emoji="🟢")
        await send_menu(query, context, "👨‍🏫 Pilih guru pengganti:", keyboard)

    elif key == "guru_pengganti":
        context.user_data["guru_pengganti"] = value
        keyboard = build_grid_keyboard(GURU_LIST, "guru_diganti", cols=3, emoji="🔴")
        await send_menu(query, context, "👤 Pilih guru diganti:", keyboard)

    elif key == "guru_diganti":
        context.user_data["guru_diganti"] = value
        keyboard = build_grid_keyboard(KELAS_LIST, "kelas", cols=3)
        await send_menu(query, context, "🏫 Pilih kelas:", keyboard)

    elif key == "kelas":
        context.user_data["kelas"] = value
        keyboard = build_grid_keyboard(SUBJEK_LIST, "subjek", cols=2)
        await send_menu(query, context, "📚 Pilih subjek:", keyboard)

    elif key == "subjek":

        context.user_data["subjek"] = value
        context.user_data["images"] = []

        text = (
            f"📅 *Tarikh:* {context.user_data.get('tarikh','')}\n"
            f"⏰ *Masa:* {context.user_data.get('masa','')}\n"
            f"👨‍🏫 *Guru Pengganti:* {context.user_data.get('guru_pengganti','')}\n"
            f"👤 *Guru Diganti:* {context.user_data.get('guru_diganti','')}\n"
            f"🏫 *Kelas:* {context.user_data.get('kelas','')}\n"
            f"📚 *Subjek:* {context.user_data.get('subjek','')}\n\n"
            "📸 Sila hantar **2 gambar** kelas relief."
        )

        await send_menu(query, context, text, None)


# ==================================================
# IMAGE HANDLER
# ==================================================
async def gambar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    photo = update.message.photo[-1]
    file = await photo.get_file()

    filename = f"{update.effective_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    await file.download_to_drive(filename)

    blob = bucket.blob(f"relief/{filename}")
    blob.upload_from_filename(filename, content_type="image/jpeg")

    url = blob.generate_signed_url(version="v4", expiration=604800, method="GET")

    context.user_data.setdefault("images", []).append(url)

    if len(context.user_data["images"]) < 2:
        return

    img1, img2 = context.user_data["images"]

    last_row = len(sheet.get_all_values()) + 1

    sheet.update(
        f"A{last_row}:I{last_row}",
        [[
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            context.user_data.get("tarikh"),
            context.user_data.get("masa"),
            context.user_data.get("guru_pengganti"),
            context.user_data.get("guru_diganti"),
            context.user_data.get("kelas"),
            context.user_data.get("subjek"),
            img1,
            img2
        ]]
    )

    context.user_data.clear()

    await update.message.reply_text("✅ Rekod relief berjaya dihantar. Terima kasih cikgu 😊")

    os.remove(filename)


# ==================================================
# RUN
# ==================================================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^🟢 Hari Ini$"), hari_ini))
    app.add_handler(MessageHandler(filters.Regex("^📅 Tarikh Lain$"), tarikh_lain))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO, gambar))

    print("🤖 Bot Relief ULTRA sedang berjalan...")
    app.run_polling()


if __name__ == "__main__":
    main()
