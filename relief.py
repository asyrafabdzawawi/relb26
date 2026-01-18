import os
import json
import asyncio
from datetime import datetime

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

import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ======================
# CONFIG
# ======================
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

SHEET_ID = "1bBnCG5ODsqQspRj_-fViRIXJGMo0w7hgbTH6p56gNuM"
DRIVE_FOLDER_ID = "1bBnCG5ODsqQspRj_-fViRIXJGMo0w7hgbTH6p56gNuM"

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

# ======================
# GOOGLE SERVICE ACCOUNT (ENV JSON)
# ======================
service_account_info = json.loads(
    os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
)

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
# DATA LIST
# ======================
MASA_LIST = [
    "7.45–8.15", "8.15–8.45", "8.45–9.15",
    "9.15–9.45", "9.45–10.15", "10.15–10.45",
    "10.45–11.15", "11.15–11.45", "11.45–12.15",
    "12.15–12.45", "12.45–1.15"
]

GURU_DIGANTI_LIST = [
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

GURU_PENGGANTI_LIST = GURU_DIGANTI_LIST.copy()

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
    "Bahasa Arab",
    "Sains",
    "Sejarah",
    "Matematik",
    "Reka Bentuk dan Teknologi (RBT)",
    "Pendidikan Jasmani Dan Kesihatan",
    "Pendidikan Seni Visual",
    "Pendidikan Muzik",
    "Pendidikan Moral",
    "Pendidikan Islam"
]

# ======================
# /start & /mula
# ======================
async def mula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["album_buffer"] = {}
    context.user_data["album_timer"] = {}

    keyboard = [[InlineKeyboardButton("📝 Isi Rekod", callback_data="mula_rekod")]]
    await update.message.reply_text(
        "🤖 *Relief Check-In Tracker*\n\n"
        "Sila tekan butang di bawah untuk mula mengisi rekod.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

    await update.message.reply_text(
        "Jika ada sebarang masalah, hubungi Cikgu Asyraf.",
        reply_markup=bottom_keyboard()
    )

# ======================
# Button callback
# ======================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("|")
    key = data[0]
    value = data[1] if len(data) > 1 else None

    if key == "mula_rekod":
        keyboard = [[InlineKeyboardButton(m, callback_data=f"masa|{m}")] for m in MASA_LIST]
        await query.edit_message_text(
            "📅 Sila pilih masa kelas relief:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif key == "masa":
        context.user_data["masa"] = value
        keyboard = [[InlineKeyboardButton(f"🟢 {g}", callback_data=f"guru_pengganti|{g}")] for g in GURU_PENGGANTI_LIST]
        await query.edit_message_text(
            "👨‍🏫 Sila pilih guru pengganti:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif key == "guru_pengganti":
        context.user_data["guru_pengganti"] = value
        keyboard = [[InlineKeyboardButton(f"🔴 {g}", callback_data=f"guru|{g}")] for g in GURU_DIGANTI_LIST]
        await query.edit_message_text(
            "👨‍🏫 Sila pilih guru diganti:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif key == "guru":
        context.user_data["guru_diganti"] = value
        keyboard = [[InlineKeyboardButton(k, callback_data=f"kelas|{k}")] for k in KELAS_LIST]
        await query.edit_message_text(
            "🏫 Sila pilih kelas:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif key == "kelas":
        context.user_data["kelas"] = value
        keyboard = [[InlineKeyboardButton(s, callback_data=f"subjek|{s}")] for s in SUBJEK_LIST]
        await query.edit_message_text(
            "📚 Sila pilih subjek:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif key == "subjek":
        context.user_data["subjek"] = value
        await query.edit_message_text(
            "📸 Sila hantar **2 gambar** kelas relief.",
            parse_mode="Markdown"
        )

# ======================
# Google upload + Sheet append
# ======================
async def process_album_background(messages, context, user):
    gambar_links = []

    for i, msg in enumerate(messages[:2]):
        photo = msg.photo[-1]
        file = await photo.get_file()
        filename = f"{user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.jpg"

        await file.download_to_drive(filename)

        media = MediaFileUpload(filename, mimetype="image/jpeg", resumable=False)
        metadata = {"name": filename, "parents": [DRIVE_FOLDER_ID]}

        uploaded = drive_service.files().create(
            body=metadata,
            media_body=media,
            fields="id",
            supportsAllDrives=True
        ).execute()

        gambar_links.append(f"https://drive.google.com/file/d/{uploaded['id']}/view")

        try:
            media._fd.close()
            os.remove(filename)
        except Exception:
            pass

    sheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        datetime.now().strftime("%d/%m/%Y"),
        context.user_data.get("masa", ""),
        context.user_data.get("guru_pengganti", ""),
        context.user_data.get("guru_diganti", ""),
        context.user_data.get("kelas", ""),
        context.user_data.get("subjek", ""),
        gambar_links[0] if len(gambar_links) > 0 else "",
        gambar_links[1] if len(gambar_links) > 1 else "",
    ])

# ======================
# Album handler (SAFE)
# ======================
async def process_album(group_id, context, user, single_msg=None):
    if single_msg:
        messages = [single_msg]
    else:
        messages = context.user_data["album_buffer"].pop(group_id, [])
        context.user_data["album_timer"].pop(group_id, None)

    # Mesej awal (confirm keluar)
    await user.send_message(
        "✅ Rekod kelas relief berjaya diterima.\n"
        "📤 Sedang memuat naik ke sistem..."
    )

    # Upload Google dengan try/except
    try:
        await process_album_background(messages, context, user)
    except Exception as e:
        print("❌ Google upload error:", e)
        await user.send_message(
            "⚠️ Rekod diterima tetapi gagal upload ke Google.\n"
            "Sila maklumkan pentadbir."
        )

# ======================
# Terima gambar
# ======================
async def gambar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message
    group_id = getattr(msg, "media_group_id", None)

    if group_id:
        if group_id not in context.user_data["album_buffer"]:
            context.user_data["album_buffer"][group_id] = []
            context.user_data["album_timer"][group_id] = asyncio.get_event_loop().call_later(
                1.5,
                lambda: asyncio.create_task(process_album(group_id, context, user))
            )
        context.user_data["album_buffer"][group_id].append(msg)
    else:
        await process_album(None, context, user, single_msg=msg)

# ======================
# Text button
# ======================
async def text_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "📝 Isi Rekod":
        await mula(update, context)

# ======================
# RUN
# ======================
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", mula))
    app.add_handler(CommandHandler("mula", mula))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_button))
    app.add_handler(MessageHandler(filters.PHOTO, gambar))
    print("🤖 Bot Relief sedang berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
