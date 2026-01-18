import os
import json
import asyncio
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# =========================
# FIREBASE
# =========================
import firebase_admin
from firebase_admin import credentials, storage

# =========================
# GOOGLE SHEET
# =========================
import gspread
from google.oauth2.service_account import Credentials

# ==================================================
# ENV VARIABLES
# ==================================================
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SHEET_ID = "1bBnCG5ODsqQspRj_-fViRIXJGMo0w7hgbTH6p56gNuM"
FIREBASE_BUCKET = "relief-31bc6.firebasestorage.app"

# ==================================================
# FIREBASE INIT
# ==================================================
firebase_creds = credentials.Certificate(
    json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT_JSON"])
)

firebase_admin.initialize_app(firebase_creds, {
    "storageBucket": FIREBASE_BUCKET
})

bucket = storage.bucket()

# ==================================================
# GOOGLE SHEET INIT
# ==================================================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

sheet_creds = Credentials.from_service_account_info(
    json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]),
    scopes=SCOPES
)

gc = gspread.authorize(sheet_creds)
sheet = gc.open_by_key(SHEET_ID).sheet1

# ==================================================
# DATA
# ==================================================
MASA_LIST = [
    "7.45–8.15", "8.15–8.45", "8.45–9.15",
    "9.15–9.45", "9.45–10.15", "10.15–10.45",
    "10.45–11.15", "11.15–11.45", "11.45–12.15",
    "12.15–12.45", "12.45–1.15"
]

GURU_LIST = [
    "Mohd Faizal Bin Ahmad",
    "Shahairi Bin Suratman",
    "Mohd Khairul Nizam Bin Hazari",
    "Wan Nurhaslinda Binti Wan Mazuki",
    "Abdul Ghani Bin Abdul Karim",
    "Abu Bakar Bin Sahari",
    "Azizul Rahim Bin Ismail",
    "Azlinawati Binti Yaakob",
    "Azura Binti Mohamad",
    "Basirah Binti Bacharudin",
    "Chithrra A/P Damodharan",
    "Endhumathy A/P Veeraiah",
    "Fadzilah Binti Jahaya",
    "Faridah Binti Muda",
    "Masita Binti Ismail",
    "Mazura Binti Abdul Aziz",
    "Mohd Asri Bin Isma'ail",
    "Mohd Huzaini Bin Husin",
    "Mohd Noor Safwan Bin Md Noor",
    "Muhammad Asyraf Bin Abdullah Zawawi",
    "Muhammad Yusuf Bin Zainol Abidin",
    "Noor Aizah Binti Ilias",
    "Noor Azlin Binti Teh",
    "Noor Azlinda Binti Abdullah",
    "Noor Jareena Binti Mohamud Kassim",
    "Normasita Bt Elias",
    "Norul Fazlin Binti Zainal Karib",
    "Nur Imanina Binti Shaari",
    "Nurul Asyiqin Binti Osman",
    "Nurulzahilah Binti Ibrahim",
    "Puoneswari A/P Sundarajoo",
    "Roslan Bin Mohd Yusoff",
    "Rusmaliza Binti Abdul Rahman",
    "Siti Rohayu Binti Zakaria",
    "Siti Munirah Binti Munadzir",
    "Suria Binti Ismail",
    "Umamageswari A/P Muniandy",
    "Uzma Farzana Binti Ridzuan",
    "Wan Nur Aqielah Binti Wan Shahar",
    "Za'aimah Binti Shakir",
    "Zarina Binti Mohamad",
    "Zuraini Binti Hassan"
]

KELAS_LIST = [
    "1 Amber", "1 Amethyst", "1 Aquamarine",
    "2 Amber", "2 Amethyst", "2 Aquamarine",
    "3 Amber", "3 Amethyst", "3 Aquamarine",
    "4 Amber", "4 Amethyst", "4 Aquamarine",
    "5 Amber", "5 Amethyst", "5 Aquamarine",
    "6 Amber", "6 Amethyst", "6 Aquamarine",
]

SUBJEK_LIST = [
    "Bahasa Melayu", "Bahasa Inggeris", "Bahasa Arab",
    "Sains", "Sejarah", "Matematik",
    "RBT", "PJPK", "PSV", "Muzik",
    "Moral", "Pendidikan Islam"
]

# ==================================================
# /start
# ==================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    keyboard = [[InlineKeyboardButton("📝 Isi Rekod", callback_data="mula")]]
    await update.message.reply_text(
        "🤖 *Relief Check-In Tracker*\n\nTekan butang di bawah untuk mula.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ==================================================
# CALLBACK FLOW
# ==================================================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    key, *rest = query.data.split("|")
    value = rest[0] if rest else None

    if key == "mula":
        keyboard = [[InlineKeyboardButton(m, callback_data=f"masa|{m}")] for m in MASA_LIST]
        await query.edit_message_text("📅 Pilih masa:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif key == "masa":
        context.user_data["masa"] = value
        keyboard = [[InlineKeyboardButton(g, callback_data=f"guru|{g}")] for g in GURU_LIST]
        await query.edit_message_text("👨‍🏫 Pilih guru pengganti:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif key == "guru":
        context.user_data["guru"] = value
        keyboard = [[InlineKeyboardButton(k, callback_data=f"kelas|{k}")] for k in KELAS_LIST]
        await query.edit_message_text("🏫 Pilih kelas:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif key == "kelas":
        context.user_data["kelas"] = value
        keyboard = [[InlineKeyboardButton(s, callback_data=f"subjek|{s}")] for s in SUBJEK_LIST]
        await query.edit_message_text("📚 Pilih subjek:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif key == "subjek":
        context.user_data["subjek"] = value
        await query.edit_message_text("📸 Sila hantar **2 gambar** kelas relief.", parse_mode="Markdown")

# ==================================================
# IMAGE HANDLER
# ==================================================
async def gambar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        photo = update.message.photo[-1]
        file = await photo.get_file()

        filename = f"{user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        await file.download_to_drive(filename)

        blob = bucket.blob(f"relief/{filename}")
        blob.upload_from_filename(filename)
        blob.make_public()

        image_url = blob.public_url
        os.remove(filename)

        sheet.append_row([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            context.user_data.get("masa", ""),
            context.user_data.get("guru", ""),
            context.user_data.get("kelas", ""),
            context.user_data.get("subjek", ""),
            image_url
        ])

        await update.message.reply_text(
            "✅ Rekod kelas relief berjaya dihantar.\nTerima kasih cikgu 😊"
        )

    except Exception as e:
        print("ERROR:", e)
        await update.message.reply_text(
            "⚠️ Rekod diterima tetapi berlaku ralat sistem.\n"
            "Sila maklumkan pentadbir."
        )

# ==================================================
# RUN BOT
# ==================================================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO, gambar))

    print("🤖 Bot Relief (Firebase) sedang berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
