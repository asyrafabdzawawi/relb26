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
    "Mohd Faizal Bin Ahmad", "Shahairi Bin Suratman", "Mohd Khairul Nizam Bin Hazari",
    "Wan Nurhaslinda Binti Wan Mazuki", "Abdul Ghani Bin Abdul Karim", "Abu Bakar Bin Sahari",
    "Azizul Rahim Bin Ismail", "Azlinawati Binti Yaakob", "Azura Binti Mohamad", "Basirah Binti Bacharudin",
    "Chithrra A/P Damodharan", "Endhumathy A/P Veeraiah", "Fadzilah Binti Jahaya", "Faridah Binti Muda",
    "Masita Binti Ismail", "Mazura Binti Abdul Aziz", "Mohd Asri Bin Isma'ail", "Mohd Huzaini Bin Husin",
    "Mohd Noor Safwan Bin Md Noor", "Muhammad Asyraf Bin Abdullah Zawawi", "Muhammad Yusuf Bin Zainol Abidin",
    "Noor Aizah Binti Ilias", "Noor Azlin Binti Teh", "Noor Azlinda Binti Abdullah",
    "Noor Jareena Binti Mohamud Kassim", "Normasita Bt Elias", "Norul Fazlin Binti Zainal Karib",
    "Nur Imanina Binti Shaari", "Nurul Asyiqin Binti Osman", "Nurulzahilah Binti Ibrahim",
    "Puoneswari A/P Sundarajoo", "Roslan Bin Mohd Yusoff", "Rusmaliza Binti Abdul Rahman",
    "Siti Rohayu Binti Zakaria", "Siti Munirah Binti Munadzir", "Suria Binti Ismail",
    "Umamageswari A/P Muniandy", "Uzma Farzana Binti Ridzuan", "Wan Nur Aqielah Binti Wan Shahar",
    "Za'aimah Binti Shakir", "Zarina Binti Mohamad", "Zuraini Binti Hassan"
]

KELAS_LIST = ["1 Amber", "1 Amethyst", "1 Aquamarine", "2 Amber", "2 Amethyst", "2 Aquamarine",
              "3 Amber", "3 Amethyst", "3 Aquamarine", "4 Amber", "4 Amethyst", "4 Aquamarine",
              "5 Amber", "5 Amethyst", "5 Aquamarine", "6 Amber", "6 Amethyst", "6 Aquamarine"]

SUBJEK_LIST = ["Bahasa Melayu", "Bahasa Inggeris", "Bahasa Arab", "Sains", "Sejarah", "Matematik",
               "RBT", "PJPK", "PSV", "Muzik", "Moral", "Pendidikan Islam"]


# ==================================================
# GRID KEYBOARD (SAHAJA PERUBAHAN)
# ==================================================
def grid_keyboard(items, callback_prefix, cols=2, emoji=None):
    keyboard = []
    row = []

    for item in items:
        text = f"{emoji} {item}" if emoji else item
        row.append(InlineKeyboardButton(text, callback_data=f"{callback_prefix}|{item}"))

        if len(row) == cols:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


# ==================================================
# UTIL TARIKH
# ==================================================
def format_tarikh_bm(tarikh_iso):
    try:
        dt = datetime.strptime(tarikh_iso, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except:
        return tarikh_iso


def get_hari_bm(tarikh_iso):
    try:
        dt = datetime.strptime(tarikh_iso, "%Y-%m-%d")
        hari_map = {
            "Monday": "Isnin",
            "Tuesday": "Selasa",
            "Wednesday": "Rabu",
            "Thursday": "Khamis",
            "Friday": "Jumaat",
            "Saturday": "Sabtu",
            "Sunday": "Ahad"
        }
        return hari_map.get(dt.strftime("%A"), dt.strftime("%A"))
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
# SEMAK REKOD HARI INI
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
# HARI INI
# ==================================================
async def hari_ini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.delete()
    except:
        pass

    context.user_data["tarikh"] = datetime.now().strftime("%Y-%m-%d")

    keyboard = grid_keyboard(MASA_LIST, "masa", cols=2)

    msg = await update.effective_chat.send_message(
        "📅 Tarikh: *Hari Ini*\n\n⏰ Pilih masa:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

    context.user_data["last_message_id"] = msg.message_id


# ==================================================
# TARIKH LAIN
# ==================================================
async def tarikh_lain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.delete()
    except:
        pass

    today = date.today()
    context.user_data["calendar_year"] = today.year
    context.user_data["calendar_month"] = today.month

    await show_calendar(update, context)


# ==================================================
# SHOW CALENDAR
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

    msg = await update.effective_chat.send_message(
        "🗓 Pilih tarikh rekod:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    context.user_data["last_message_id"] = msg.message_id


# ==================================================
# CALLBACK FLOW
# ==================================================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("cal_day|"):
        _, year, month, day = data.split("|")

        tarikh_obj = date(int(year), int(month), int(day))
        if tarikh_obj > date.today():
            await query.answer("❌ Tarikh tidak boleh melebihi hari ini", show_alert=True)
            return

        tarikh_iso = tarikh_obj.strftime("%Y-%m-%d")
        context.user_data["tarikh"] = tarikh_iso

        keyboard = grid_keyboard(MASA_LIST, "masa", cols=2)

        await query.edit_message_text(
            f"📅 Tarikh dipilih: *{format_tarikh_bm(tarikh_iso)}*\n\n⏰ Pilih masa:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return

    key, *rest = data.split("|")
    value = rest[0] if rest else None

    if key == "masa":
        context.user_data["masa"] = value
        keyboard = grid_keyboard(GURU_LIST, "guru_pengganti", cols=3, emoji="🟢")
        await query.edit_message_text("👨‍🏫 Pilih guru pengganti:", reply_markup=keyboard)

    elif key == "guru_pengganti":
        context.user_data["guru_pengganti"] = value
        keyboard = grid_keyboard(GURU_LIST, "guru_diganti", cols=3, emoji="🔴")
        await query.edit_message_text("👤 Pilih guru diganti:", reply_markup=keyboard)

    elif key == "guru_diganti":
        context.user_data["guru_diganti"] = value
        keyboard = grid_keyboard(KELAS_LIST, "kelas", cols=3)
        await query.edit_message_text("🏫 Pilih kelas:", reply_markup=keyboard)

    elif key == "kelas":
        context.user_data["kelas"] = value
        keyboard = grid_keyboard(SUBJEK_LIST, "subjek", cols=2)
        await query.edit_message_text("📚 Pilih subjek:", reply_markup=keyboard)

    elif key == "subjek":
        context.user_data["subjek"] = value
        context.user_data["images"] = []

        tarikh_iso = context.user_data.get("tarikh", "")
        tarikh_bm = format_tarikh_bm(tarikh_iso)
        hari_bm = get_hari_bm(tarikh_iso)

        await query.edit_message_text(
            f"📅 *Tarikh Rekod:* {tarikh_bm}\n"
            f"🗓 *Hari:* {hari_bm}\n"
            f"⏰ *Masa:* {context.user_data.get('masa','')}\n"
            f"👨‍🏫 *Guru Pengganti:* {context.user_data.get('guru_pengganti','')}\n"
            f"👤 *Guru Diganti:* {context.user_data.get('guru_diganti','')}\n"
            f"🏫 *Kelas:* {context.user_data.get('kelas','')}\n"
            f"📚 *Subjek:* {context.user_data.get('subjek','')}\n\n"
            "📸 Sila hantar **2 gambar** kelas relief.",
            parse_mode="Markdown"
        )


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
        blob.upload_from_filename(filename, content_type="image/jpeg")

        image_url = blob.generate_signed_url(version="v4", expiration=60*60*24*7, method="GET")

        context.user_data.setdefault("images", []).append(image_url)
        if len(context.user_data["images"]) < 2:
            return

        img1, img2 = context.user_data["images"]
        last_row = len(sheet.get_all_values()) + 1

        sheet.update(
            range_name=f"A{last_row}:I{last_row}",
            values=[[
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                context.user_data.get("tarikh", datetime.now().strftime("%Y-%m-%d")),
                context.user_data.get("masa", ""),
                context.user_data.get("guru_pengganti", ""),
                context.user_data.get("guru_diganti", ""),
                context.user_data.get("kelas", ""),
                context.user_data.get("subjek", ""),
                img1,
                img2
            ]]
        )

        sheet.update(range_name=f"J{last_row}", values=[[f"=IMAGE(H{last_row})"]], value_input_option="USER_ENTERED")
        sheet.update(range_name=f"K{last_row}", values=[[f"=IMAGE(I{last_row})"]], value_input_option="USER_ENTERED")

        context.user_data.clear()
        await update.message.reply_text("✅ Rekod kelas relief berjaya dihantar.\nTerima kasih cikgu 😊")

        try:
            os.remove(filename)
        except:
            pass

    except Exception as e:
        print("SYSTEM ERROR:", e)
        await update.message.reply_text(
            "⚠️ Berlaku ralat semasa proses muat naik.\nSila cuba semula atau maklumkan pentadbir."
        )


# ==================================================
# RUN BOT
# ==================================================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🟢 Hari Ini$"), hari_ini))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^📅 Tarikh Lain$"), tarikh_lain))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("Semak Rekod"), semak_rekod))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("Lihat Rekod Penuh"), lihat_penuh))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO, gambar))

    print("🤖 Bot Relief (Firebase) sedang berjalan...")
    app.run_polling()


if __name__ == "__main__":
    main()
