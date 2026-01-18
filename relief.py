import os
import json
import asyncio
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ======================
# FIREBASE
# ======================
import firebase_admin
from firebase_admin import credentials, storage

# ======================
# GOOGLE SHEET
# ======================
import gspread
from google.oauth2.service_account import Credentials

# ======================
# ENV CONFIG
# ======================
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SHEET_ID = "1bBnCG5ODsqQspRj_-fViRIXJGMo0w7hgbTH6p56gNuM"
FIREBASE_BUCKET = "gs://relief-31bc6.firebasestorage.app"

# ======================
# FIREBASE INIT
# ======================
firebase_creds = credentials.Certificate(
    json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT_JSON"])
)

firebase_admin.initialize_app(firebase_creds, {
    "storageBucket": FIREBASE_BUCKET
})

bucket = storage.bucket()

# ======================
# GOOGLE SHEET INIT
# ======================
sheet_creds = Credentials.from_service_account_info(
    json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]),
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
)

gc = gspread.authorize(sheet_creds)
sheet = gc.open_by_key(SHEET_ID).sheet1

# ======================
# DATA
# ======================
MASA_LIST = [
    "7.45–8.15", "8.15–8.45", "8.45–9.15",
    "9.15–9.45", "9.45–10.15", "10.15–10.45",
    "10.45–11.15", "11.15–11.45", "11.45–12.15",
    "12.15–12.45", "12.45–1.15"
]

# (Guru, kelas, subjek – kekal sama)
# Potong sini untuk ringkas – anggap LIST awak betul

# ======================
# START
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["images"] = []

    keyboard = [[InlineKeyboardButton("📝 Isi Rekod", callback_data="mula")]]
    await update.message.reply_text(
        "🤖 *Relief Check-In Tracker*\n\nTekan untuk mula.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ======================
# CALLBACK
# ======================
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
        await query.edit_message_text("📸 Hantar **2 gambar** kelas relief.")

# ======================
# IMAGE HANDLER (2 GAMBAR)
# ======================
async def gambar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        photo = update.message.photo[-1]
        file = await photo.get_file()

        filename = f"{update.effective_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        await file.download_to_drive(filename)

        blob = bucket.blob(f"relief/{filename}")
        blob.upload_from_filename(filename)
        blob.make_public()

        os.remove(filename)

        context.user_data["images"].append(blob.public_url)

        if len(context.user_data["images"]) < 2:
            await update.message.reply_text("📸 Sila hantar **1 lagi gambar**.")
            return

        # SIMPAN KE SHEET
        sheet.append_row([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            context.user_data.get("masa", ""),
            context.user_data["images"][0],
            context.user_data["images"][1]
        ])

        await update.message.reply_text(
            "✅ Rekod kelas relief berjaya disimpan.\nTerima kasih cikgu 😊"
        )

        context.user_data.clear()

    except Exception as e:
        await update.message.reply_text(
            "⚠️ Rekod diterima tetapi berlaku ralat sistem.\nSila maklumkan pentadbir."
        )
        print("ERROR:", e)

# ======================
# RUN
# ======================
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO, gambar))
    app.run_polling()

if __name__ == "__main__":
    main()
