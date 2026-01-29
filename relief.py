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
# UTIL TARIKH
# ==================================================
def format_tarikh_bm(tarikh_iso):
    try:
        return datetime.strptime(tarikh_iso,"%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        return tarikh_iso

def get_hari_bm(tarikh_iso):
    try:
        hari_map = {"Monday":"Isnin","Tuesday":"Selasa","Wednesday":"Rabu",
                    "Thursday":"Khamis","Friday":"Jumaat","Saturday":"Sabtu","Sunday":"Ahad"}
        return hari_map[datetime.strptime(tarikh_iso,"%Y-%m-%d").strftime("%A")]
    except:
        return ""

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
# SEMAK REKOD
# ==================================================
async def semak_rekod(update: Update, context: ContextTypes.DEFAULT_TYPE):

    today_iso = datetime.now().strftime("%Y-%m-%d")
    today_display = datetime.now().strftime("%d/%m/%Y")

    rows = sheet.get_all_values()
    data_rows = rows[1:] if len(rows) > 1 else []

    rekod = [r for r in data_rows if len(r) > 1 and r[1] == today_iso]

    if not rekod:
        await update.message.reply_text(
            f"📊 *Rekod Relief Hari Ini*\n📅 {today_display}\n\nTiada rekod direkodkan.",
            parse_mode="Markdown"
        )
        return

    mesej = f"📊 *REKOD RELIEF HARI INI*\n📅 {today_display}\n\n"

    for i, r in enumerate(rekod, start=1):
        mesej += (
            f"{i}️⃣ {r[2]}\n"
            f"👨‍🏫 Pengganti: {r[3]}\n"
            f"👤 Diganti: {r[4]}\n"
            f"🏫 {r[5]}\n"
            f"📚 {r[6]}\n\n"
        )

    await update.message.reply_text(mesej, parse_mode="Markdown")

# ==================================================
# ADMIN LOCK
# ==================================================
async def lihat_penuh(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text(
            "⛔ *Akses Terhad*\n\nHanya pentadbir boleh melihat rekod penuh.",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text("📊 *Rekod Relief Penuh:*", parse_mode="Markdown")
    await update.message.reply_text(SHEET_URL)

# ==================================================
# (SEMUA BAWAH INI KEKAL — TAK DIUSIK)
# ==================================================
# 👉 hari_ini
# 👉 tarikh_lain
# 👉 calendar
# 👉 callback flow
# 👉 image handler
# 👉 main()

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Text("🟢 Hari Ini"), hari_ini))
    app.add_handler(MessageHandler(filters.Text("📅 Tarikh Lain"), tarikh_lain))
    app.add_handler(MessageHandler(filters.Text("📊 Semak Rekod Hari Ini"), semak_rekod))
    app.add_handler(MessageHandler(filters.Text("📊 Lihat Rekod Penuh (Admin)"), lihat_penuh))

    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO, gambar))

    print("🤖 Bot Relief PRODUCTION sedang berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
