import os
import json
import pytz
from datetime import datetime, date, timedelta


from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

import firebase_admin
from firebase_admin import credentials, storage
from reportlab.platypus import KeepTogether

import gspread
from google.oauth2.service_account import Credentials
from collections import Counter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
import matplotlib.pyplot as plt

MALAYSIA_TZ = pytz.timezone("Asia/Kuala_Lumpur")
# ==================================================
# CONFIG
# ==================================================
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SHEET_ID = "1bBnCG5ODsqQspRj_-fViRIXJGMo0w7hgbTH6p56gNuM"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1bBnCG5ODsqQspRj_-fViRIXJGMo0w7hgbTH6p56gNuM/edit"
FIREBASE_BUCKET = "relief-31bc6.firebasestorage.app"

ADMIN_IDS = [
    522707506,
    3998287,
    5114021646,
    14518619,
    53256464,
    8214543588
]


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

# PATCH: kekalkan sheet asal + tambah akses spreadsheet
spreadsheet = gc.open_by_key(SHEET_ID)
sheet = spreadsheet.sheet1   # JANUARI (default)


# ==================================================
# DATA
# ==================================================
MASA_LIST = ["7.45–8.15", "8.15–8.45", "8.45–9.15", "9.15–9.45", "9.45–10.15",
             "10.15–10.45", "10.45–11.15", "11.15–11.45", "11.45–12.15", "12.15–12.45", "12.45–1.15"]

GURU_LIST = [
    "Mohd Faizal Bin Ahmad", "Shahairi Bin Suratman", "Mohd Khairul Nizam Bin Hazari",
    "Suemanie A.P. Ee @Quah Chin We", "Abdul Ghani Bin Abdul Karim", "Abu Bakar Bin Sahari", "Mohd Asri Bin Isma'ail", "Mohamad Hamdan Bin Mohd Noor",
    "Muhammad Asyraf Bin Abdullah Zawawi", "Azizul Rahim Bin Ismail", "Nurul Asyiqin Binti Osman", "Azlinawati Binti Yaakob", 
     "Noor Aizah Binti Ilias",  "Noor Azlin Binti Teh", "Noor Azlinda Binti Abdullah", "Azura Binti Mohamad", "Basirah Binti Bacharudin",
    "Chithrra A/P Damodharan", "Endhumathy A/P Veeraiah", "Fadzilah Binti Jahaya", "Faridah Binti Muda","Norul Fazlin Binti Zainal Karib",
    "Nur Imanina Binti Shaari", "Masita Binti Ismail", "Mazura Binti Abdul Aziz",  "Siti Munirah Binti Munadzir","Normasita Bt Elias", "Mohd Huzaini Bin Husin",
     "Noor Jareena Binti Mohamud Kassim", "Roslan Bin Mohd Yusoff","Rusmaliza Binti Abdul Rahman",
    "Siti Rohayu Binti Zakaria","Mohd Noor Safwan Bin Md Noor","Suria Binti Ismail", "Umamageswari A/P Muniandy", "Uzma Farzana Binti Ridzuan", "Wan Nur Aqielah Binti Wan Shahar","Muhammad Yusuf Bin Zainol Abidin",
      "Za'aimah Binti Shakir", "Nurulzahilah Binti Ibrahim", "Zarina Binti Mohamad", "Zuraini Binti Hassan"
]

GURU_DISPLAY = {
    "Mohd Faizal Bin Ahmad": "GB",
    "Shahairi Bin Suratman": "PK1",
    "Mohd Khairul Nizam Bin Hazari": "PK HEM",
    "Suemanie A.P. Ee @Quah Chin We": "PK KOKU",

    "Abdul Ghani Bin Abdul Karim": "Abdul Ghani",
    "Abu Bakar Bin Sahari": "Abu Bakar",
    
    "Mohd Asri Bin Isma'ail": "Asri",
    "Mohamad Hamdan Bin Mohd Noor": "Hamdan",
    "Muhammad Asyraf Bin Abdullah Zawawi": "Asyraf",
    "Azizul Rahim Bin Ismail": "Azizul Rahim",
    "Nurul Asyiqin Binti Osman": "Asyiqin",
    "Azlinawati Binti Yaakob": "Azlinawati",
    "Noor Aizah Binti Ilias": "Aizah",
    "Noor Azlin Binti Teh": "Azlin",
    
    "Noor Azlinda Binti Abdullah": "Azlinda",
    "Azura Binti Mohamad": "Azura",
    "Basirah Binti Bacharudin": "Basirah",

    "Chithrra A/P Damodharan": "Chithrra",
    "Endhumathy A/P Veeraiah": "Endhumathy",
    "Fadzilah Binti Jahaya": "Fadzilah",
    "Faridah Binti Muda": "Faridah",
    "Norul Fazlin Binti Zainal Karib": "Fazlin",

      "Nur Imanina Binti Shaari": "Imanina",

    "Masita Binti Ismail": "Masita",
    "Mazura Binti Abdul Aziz": "Mazura",
    "Siti Munirah Binti Munadzir": "Munirah",
    "Normasita Bt Elias": "Normasita",
    "Mohd Huzaini Bin Husin": "Huzaini",

     "Noor Jareena Binti Mohamud Kassim": "Jareena",

    

   


    

    
    "Roslan Bin Mohd Yusoff": "Roslan",
    "Rusmaliza Binti Abdul Rahman": "Rusmaliza",

    "Siti Rohayu Binti Zakaria": "Rohayu",

    "Mohd Noor Safwan Bin Md Noor": "Safwan",
    "Suria Binti Ismail": "Suria",

    "Umamageswari A/P Muniandy": "Umamageswari",
    "Uzma Farzana Binti Ridzuan": "Uzma",
    "Wan Nur Aqielah Binti Wan Shahar": "Wan Aqielah",

     "Muhammad Yusuf Bin Zainol Abidin": "Yusuf",

    "Za'aimah Binti Shakir": "Za'aimah",
     "Nurulzahilah Binti Ibrahim": "Zahilah",
    "Zarina Binti Mohamad": "Zarina",
    "Zuraini Binti Hassan": "Zuraini"
}

KELAS_LIST = ["1 Amber", "1 Amethyst", "1 Aquamarine", "2 Amber", "2 Amethyst", "2 Aquamarine",
              "3 Amber", "3 Amethyst", "3 Aquamarine", "4 Amber", "4 Amethyst", "4 Aquamarine",
              "5 Amber", "5 Amethyst", "5 Aquamarine", "6 Amber", "6 Amethyst", "6 Aquamarine"]

SUBJEK_LIST = ["Bahasa Melayu", "Bahasa Inggeris", "Bahasa Arab", "Sains", "Sejarah", "Matematik",
               "RBT", "PJPK", "PSV", "Muzik", "Moral", "Pendidikan Islam"]

def header_footer(canvas, doc):
    canvas.saveState()

    # ===== HEADER =====
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawCentredString(
        doc.pagesize[0] / 2,
        doc.pagesize[1] - 1.5 * cm,
        "RELIEF CHECK-IN TRACKER SK LABU BESAR"
    )

    # Garis bawah header
    canvas.line(
        2 * cm,
        doc.pagesize[1] - 1.7 * cm,
        doc.pagesize[0] - 2 * cm,
        doc.pagesize[1] - 1.7 * cm
    )

    # ===== FOOTER =====
    canvas.setFont("Helvetica", 9)
    canvas.drawCentredString(
        doc.pagesize[0] / 2,
        1.5 * cm,
        "Sinergi Ke Arah Lonjakan Bestari"
    )
    canvas.drawCentredString(
        doc.pagesize[0] / 2,
        1.0 * cm,
        "#LabuBest"
    )

    canvas.restoreState()

def get_paling_kurang(counter):
    if not counter:
        return None, 0
    min_val = min(counter.values())
    for k, v in counter.items():
        if v == min_val:
            return k, v

def get_guru_tiada_ganti(guru_list, guru_ganti_counter):
    return [g for g in guru_list if guru_ganti_counter.get(g, 0) == 0]



def get_data_7_hari():
    hari_ini = datetime.now(MALAYSIA_TZ).date()
    mula = hari_ini - timedelta(days=6)

    kelas = Counter()
    subjek = Counter()
    guru_ganti = Counter()
    guru_diganti = Counter()

    for i in range(7):
        tarikh = mula + timedelta(days=i)
        tarikh_iso = tarikh.strftime("%Y-%m-%d")
        sheet = get_sheet_by_month(tarikh_iso)

        rows = sheet.get_all_values()
        data = rows[1:] if len(rows) > 1 else []

        for r in data:
            if len(r) < 7 or r[1] != tarikh_iso:
                continue
            kelas[r[5]] += 1
            subjek[r[6]] += 1
            guru_ganti[r[3]] += 1
            guru_diganti[r[4]] += 1

    return kelas, subjek, guru_ganti, guru_diganti

def plot_bar(counter, tajuk, filename, top=5):
    data = counter.most_common(top)
    if not data:
        return None

    labels = [d[0] for d in data]
    values = [d[1] for d in data]

    plt.figure(figsize=(8,4))
    plt.bar(labels, values)
    plt.title(tajuk)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

    return filename

def plot_bar_kurang(counter, tajuk, filename, bottom=5):
    if not counter:
        return None

    data = [(k, v) for k, v in counter.items() if v > 0]
    if not data:
        return None

    data = sorted(data, key=lambda x: x[1])[:bottom]

    labels = [d[0] for d in data]
    values = [d[1] for d in data]

    plt.figure(figsize=(8,4))
    plt.bar(labels, values)
    plt.title(tajuk)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

    return filename



def get_julat_ahad_khamis():
    today = datetime.now(MALAYSIA_TZ).date()
    # Monday=0 ... Sunday=6
    hari_ke = today.weekday()

    # Cari Ahad
    ahad = today - timedelta(days=(hari_ke + 1) % 7)

    # Khamis = Ahad + 4 hari
    khamis = ahad + timedelta(days=4)

    return ahad, khamis

def bina_pdf(gambar_list):
    filename = f"Analisis_Relief_{datetime.now(MALAYSIA_TZ).date()}.pdf"
    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    story = []

    ahad, khamis = get_julat_ahad_khamis()
    


    tarikh_teks = (
    f"Tempoh Analisis: "
    f"{ahad.strftime('%d/%m/%Y')} (Ahad) "
    f"hingga {khamis.strftime('%d/%m/%Y')} (Khamis)"
    )

    story.append(Paragraph(tarikh_teks, styles["Normal"]))
    

    
    story.append(Spacer(1, 12))


    story.append(Paragraph("<b>ANALISIS RELIEF MINGGUAN</b>", styles["Title"]))
    story.append(Spacer(1, 12))

    # === Senarai guru 0 kali mengganti (TEKS SAHAJA) ===
    _, _, guru_ganti, _ = get_data_7_hari()
    guru_0 = get_guru_tiada_ganti(GURU_LIST, guru_ganti)

    if guru_0:
        story.append(Paragraph(
            "<b>Guru Tidak Terlibat Dalam Relief Minggu Ini:</b>",
            styles["Heading3"]
    ))

    senarai = ", ".join(guru_0)
    story.append(Paragraph(senarai, styles["Normal"]))
    story.append(Spacer(1, 12))


    for tajuk, img in gambar_list:
        section = []

        section.append(Paragraph(tajuk, styles["Heading2"]))
        section.append(Spacer(1, 6))
        section.append(Image(img, width=400, height=200))
        section.append(Spacer(1, 20))

        story.append(KeepTogether(section))

    doc.build(
    story,
    onFirstPage=header_footer,
    onLaterPages=header_footer
    )

    return filename
# ==================================================
# GRID KEYBOARD
# ==================================================
def grid_keyboard(items, callback_prefix, cols=2, emoji=None):
    keyboard = []
    row = []

    for item in items:

        # paparan nama pendek
        display = GURU_DISPLAY.get(item, item)

        text = f"{emoji} {display}" if emoji else display

        row.append(
            InlineKeyboardButton(text, callback_data=f"{callback_prefix}|{item}")
        )

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
# PATCH: PILIH SHEET IKUT BULAN
# ==================================================
def get_sheet_by_month(tarikh_iso):
    dt = datetime.strptime(tarikh_iso, "%Y-%m-%d")

    bulan_map = {
        1: "Sheet1",
        2: "Februari",
        3: "MAC",
        4: "APRIL",
        5: "MEI",
        6: "JUN",
        7: "JULAI",
        8: "OGOS",
        9: "SEPTEMBER",
        10: "OKTOBER",
        11: "NOVEMBER",
        12: "DISEMBER"
    }

    try:
        return spreadsheet.worksheet(bulan_map[dt.month])
    except:
        return spreadsheet.sheet1


# ==================================================
# START
# ==================================================
async def analisis_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Menjana laporan analisis mingguan...")

    kelas, subjek, guru_ganti, guru_diganti = get_data_7_hari()

    if not kelas:
        await update.message.reply_text("Tiada data relief untuk 7 hari terakhir.")
        return

    files = []
    files.append(("🏫 Kelas Paling Banyak Diganti", plot_bar(kelas, "Kelas Diganti", "kelas.png")))
    files.append(("📚 Subjek Paling Banyak Diganti", plot_bar(subjek, "Subjek Diganti", "subjek.png")))
    files.append(("👨‍🏫 Guru Paling Banyak Mengganti", plot_bar(guru_ganti, "Guru Mengganti", "guru_ganti.png")))
    files.append(("👤 Guru Paling Banyak Diganti", plot_bar(guru_diganti, "Guru Diganti", "guru_diganti.png")))
    files.append(("👨‍🏫 Guru Paling Kurang Mengganti",
    plot_bar_kurang(guru_ganti, "Guru Paling Kurang Mengganti", "guru_kurang.png", bottom=5)))


    files = [f for f in files if f[1]]

    pdf = bina_pdf(files)

    await update.message.reply_document(
        document=open(pdf, "rb"),
        caption="📊 Laporan Analisis Relief Mingguan"
    )

    # cleanup
    for _, f in files:
        os.remove(f)
    os.remove(pdf)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    reply_keyboard = [
    [KeyboardButton("🟢 Hari Ini"), KeyboardButton("📅 Tarikh Lain")],
    [KeyboardButton("📊 Semak Rekod Hari Ini"), KeyboardButton("📈 Analisis Mingguan (PDF)")],
    [KeyboardButton("📊 Lihat Rekod Penuh (Admin)")]
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
    today_iso = datetime.now(MALAYSIA_TZ).strftime("%Y-%m-%d")
    today_display = datetime.now(MALAYSIA_TZ).strftime("%d/%m/%Y")

    # PATCH: baca tab ikut bulan semasa
    today_sheet = get_sheet_by_month(today_iso)

    rows = today_sheet.get_all_values()
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

    context.user_data["tarikh"] = datetime.now(MALAYSIA_TZ).strftime("%Y-%m-%d")

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

    today = datetime.now(MALAYSIA_TZ).date()
    context.user_data["calendar_year"] = today.year
    context.user_data["calendar_month"] = today.month

    await show_calendar(update, context)


# ==================================================
# SHOW CALENDAR
# ==================================================
async def show_calendar(update, context):

    year = context.user_data["calendar_year"]
    month = context.user_data["calendar_month"]
    today = datetime.now(MALAYSIA_TZ).date()

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
        if tarikh_obj > datetime.now(MALAYSIA_TZ).date():
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
# IMAGE HANDLER (PATCH DI SINI)
# ==================================================
async def gambar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        photo = update.message.photo[-1]
        file = await photo.get_file()
        filename = f"{user.id}_{datetime.now(MALAYSIA_TZ).strftime('%Y%m%d_%H%M%S')}.jpg"
        await file.download_to_drive(filename)

        blob = bucket.blob(f"relief/{filename}")
        blob.upload_from_filename(filename, content_type="image/jpeg")

        image_url = blob.generate_signed_url(version="v4", expiration=60*60*24*7, method="GET")

        context.user_data.setdefault("images", []).append(image_url)
        if len(context.user_data["images"]) < 2:
            return

        img1, img2 = context.user_data["images"]

        tarikh_iso = context.user_data.get(
            "tarikh", datetime.now(MALAYSIA_TZ).strftime("%Y-%m-%d")
        )

        sheet = get_sheet_by_month(tarikh_iso)

        # LATEST DI ATAS (ROW 2)
        sheet.insert_row([
            datetime.now(MALAYSIA_TZ).strftime("%Y-%m-%d %H:%M:%S"),
            tarikh_iso,
            context.user_data.get("masa", ""),
            context.user_data.get("guru_pengganti", ""),
            context.user_data.get("guru_diganti", ""),
            context.user_data.get("kelas", ""),
            context.user_data.get("subjek", ""),
            img1,
            img2,
            "",
            ""
        ], 2)

        sheet.update("J2", [["=IMAGE(H2)"]], value_input_option="USER_ENTERED")
        sheet.update("K2", [["=IMAGE(I2)"]], value_input_option="USER_ENTERED")

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
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("Analisis Mingguan \\(PDF\\)"), analisis_pdf))


    print("🤖 Bot Relief (Firebase) sedang berjalan...")
    app.run_polling()


if __name__ == "__main__":
    main()
