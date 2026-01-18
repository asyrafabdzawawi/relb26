from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

import os
import json
import asyncio
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ======================
# ENV CONFIG
# ======================

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SHEET_ID = "1bBnCG5ODsqQspRj_-fViRIXJGMo0w7hgbTH6p56gNuM"
DRIVE_FOLDER_ID = "1aXDdttdB9WFxzVZdAkP63OgepB2dHKvu"

service_account_info = json.loads(
    os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
)

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]

# ======================
# GOOGLE AUTH
# ======================

creds = Credentials.from_service_account_info(
    service_account_info,
    scopes=SCOPES
)

drive_service = build("drive", "v3", credentials=creds)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SHEET_ID).sheet1

# ======================
# KEYBOARD
# ======================

def bottom_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📝 Isi Rekod")]],
        resize_keyboard=True
    )

# ======================
# DATA
# ======================

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
    "Muhammad Asyraf Bin Abdullah Zawawi"
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
    "Bahasa Melayu",
    "Bahasa Inggeris",
    "Sains",
    "Matematik",
    "Sejarah",
    "Pendidikan Islam",
    "Pendidikan Jasmani",
    "Pendidikan Seni Visual"
]

# ======================
# START / MULA
# ======================

async def mula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["album_buffer"] = {}
    context.user_data["album_timer"] = {}

    keyboard = [[InlineKeyboardButton("📝 Isi Rekod", callback_data="mula")]]
    await update.message.reply_text(
        "🤖 *Relief Check-In Tracker*\n\nTekan butang untuk mula.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

    await update.message.reply_text(
        "Jika ada masalah, hubungi Cikgu Asyraf.",
        reply_markup=bottom_keyboard()
    )

# ======================
# CALLBACK BUTTON
# ======================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("|")
    key = data[0]
    value = data[1] if len(data) > 1 else None

    if key == "mula":
        keyboard = [[InlineKeyboardButton(m, callback_data=f"masa|{m}")] for m in MASA_LIST]
        await query.edit_message_text("⏰ Pilih masa:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif key == "masa":
        context.user_data["masa"] = value
        keyboard = [[InlineKeyboardButton(g, callback_data=f"guru|{g}")] for g in GURU_LIST]
        await query.edit_message_text("👨‍🏫 Pilih guru:", reply_markup=InlineKeyboardMarkup(keyboard))

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
        await query.edit_message_text("📸 Sila hantar **2 gambar** kelas.")

# ======================
# IMAGE PROCESS
# ======================

async def process_album_background(messages, context, user):
    links = []

    for i, msg in enumerate(messages[:2]):
        photo = msg.photo[-1]
        file = await photo.get_file()
        filename = f"{user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.jpg"

        await file.download_to_drive(filename)

        media = MediaFileUpload(filename, mimetype="image/jpeg")
        uploaded = drive_service.files().create(
            body={"name": filename, "parents": [DRIVE_FOLDER_ID]},
            media_body=media,
            fields="id"
        ).execute()

        links.append(f"https://drive.google.com/file/d/{uploaded['id']}/view")
        os.remove(filename)

    sheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        context.user_data.get("masa", ""),
        context.user_data.get("guru", ""),
        context.user_data.get("kelas", ""),
        context.user_data.get("subjek", ""),
        links[0],
        links[1] if len(links) > 1 else ""
    ])

async def gambar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message
    group_id = msg.media_group_id

    if group_id:
        context.user_data["album_buffer"].setdefault(group_id, []).append(msg)

        if group_id not in context.user_data["album_timer"]:
            context.user_data["album_timer"][group_id] = asyncio.get_event_loop().call_later(
                1.5,
                lambda: asyncio.create_task(
                    process_album_background(
                        context.user_data["album_buffer"].pop(group_id),
                        context,
                        user
                    )
                )
            )
    else:
        await process_album_background([msg], context, user)

    await user.send_message("✅ Rekod berjaya dihantar.")

# ======================
# TEXT BUTTON
# ======================

async def text_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "📝 Isi Rekod":
        await mula(update, context)

# ======================
# MAIN
# ======================

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", mula))
    app.add_handler(CommandHandler("mula", mula))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_button))
    app.add_handler(MessageHandler(filters.PHOTO, gambar))

    print("🤖 Bot Relief berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
