<<<<<<< HEAD
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
# Impor modul pencarian & ODP yang sudah kita buat di odp_engine.py
from odp_engine import get_prospects_by_query, check_odp_by_lead_id

# TOKEN DARI BOTFATHER KAMU
BOT_TOKEN = "8746053437:AAEpYcq6AQbDYQacifMv0GV8-Eoz7I2xN2g"

logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------
# 1. TAMPILAN AWAL SEPERTI PRD V2 (/start)
# ---------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    text = (
        f"🤖 **RADAR Bot**\n"
        f"Telkom Area Recommendation Assistant\n\n"
        f"Selamat datang, {user_name}! Mau mulai dari mana?"
    )
    keyboard = [
        [InlineKeyboardButton("🔍 Flow 1: Prospecting (cari pelanggan baru)", callback_data="flow1_start")],
        [InlineKeyboardButton("🚀 Flow 2: Existing Upgrade (rekomendasi upsell)", callback_data="flow2_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# ---------------------------------------------------------------------
# 2. HANDLER TOMBOL INLINE (FLOW 1 BERTAHAP)
# ---------------------------------------------------------------------
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # A. Klik Menu Flow 1
    if data == "flow1_start":
        context.user_data['state'] = 'WAITING_FLOW1_INPUT'
        text = (
            "🔍 **Flow 1: Prospecting**\n\n"
            "Silakan lakukan salah satu opsi berikut:\n"
            "1. Ketik **Nama PT/CV** (contoh: `Telkom`)\n"
            "2. Ketik **Nama Wilayah** (contoh: `Kediri`, `Kepanjen`)\n"
            "3. **Share Live Location** posisi kamu saat ini 📍"
        )
        keyboard = [[InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="menu_utama")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # B. Klik Tombol [📍 Cek ODP & port terdekat] pada Card Prospek
    elif data.startswith("check_odp_"):
        lead_id = int(data.split("_")[2])
        
        await query.edit_message_text("⏳ *Memeriksa ODP & menghitung kelayakan jaringan...*", parse_mode="Markdown")

        # Panggil backend hitung ODP dari odp_engine.py
        odp_res, msg = check_odp_by_lead_id(lead_id)

        if odp_res:
            res_text = (
                f"🏢 **{odp_res['prospect_nama']}**\n"
                f"🔌 ODP: `{odp_res['odp_name']}`\n"
                f"📏 Jarak: **{odp_res['distance_m']} meter**\n"
                f"📊 Status: **{odp_res['status']}** ({odp_res['used_port']}/{odp_res['total_port']} port terisi)\n\n"
                f"🟢 **LAYAK PASANG**"
            )
            if odp_res.get('is_redirected'):
                res_text += "\n_(Auto-Redirect: ODP terdekat sebelumnya FULL)_"

            keyboard = [
                [InlineKeyboardButton("🗺️ Buka rute Google Maps", url=odp_res['gmaps_url'])],
                [InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="menu_utama")]
            ]
        else:
            res_text = f"❌ {msg}"
            keyboard = [[InlineKeyboardButton("⬅️ Coba Cari Lagi", callback_data="flow1_start")]]

        await query.edit_message_text(res_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "flow2_start":
        await query.edit_message_text("🚀 **Flow 2 disiapkan.** (Saat ini kita fokus Flow 1 dulu ya!)", 
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="menu_utama")]]))

    elif data == "menu_utama":
        await start(update, context)

# ---------------------------------------------------------------------
# 3. HANDLER PENCARIAN TEKS (NAMA PT/CV ATAU WILAYAH)
# ---------------------------------------------------------------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state = context.user_data.get('state')

    if user_state == 'WAITING_FLOW1_INPUT':
        input_text = update.message.text.strip()
        
        await update.message.reply_text(f"🔍 *Menjalankan matching untuk '{input_text}'... Memuat prospek belum berlangganan.*", parse_mode="Markdown")

        # Cari berdasarkan nama dulu, jika kosong baru berdasarkan wilayah
        prospeks = get_prospects_by_query('name', input_text, limit=5)
        if not prospeks:
            prospeks = get_prospects_by_query('wilayah', input_text, limit=5)

        if not prospeks:
            await update.message.reply_text(
                f"⚠️ Tidak ditemukan prospek belum berlangganan untuk '{input_text}'.\nSilakan coba ketik nama PT/CV atau Wilayah lain."
            )
            return

        # Tampilkan Top 5 Prioritas Prospek (Sesuai PDF PRD V2)
        for p in prospeks:
            card_text = (
                f"🏢 **{p['nama']}**\n"
                f"🔴 **BELUM BERLANGGANAN - HIGH PRIORITY**\n"
                f"📍 {p['alamat'] if p['alamat'] else p['wilayah']}"
            )
            keyboard = [
                [InlineKeyboardButton("📍 Cek ODP & port terdekat", callback_data=f"check_odp_{p['lead_id']}")]
            ]
            await update.message.reply_text(card_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

        context.user_data['state'] = None

# ---------------------------------------------------------------------
# 4. HANDLER LOKASI (SHARE LIVE LOCATION / LOKASI CHAT)
# ---------------------------------------------------------------------
async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_location = update.message.location
    lat = user_location.latitude
    lon = user_location.longitude

    await update.message.reply_text(f"📍 *Menerima koordinat lokasi ({lat:.4f}, {lon:.4f})... Mencari prospek terdekat.*", parse_mode="Markdown")

    prospeks = get_prospects_by_query('liveloc', None, limit=5, sales_lat=lat, sales_lon=lon)

    if not prospeks:
        await update.message.reply_text("⚠️ Tidak ditemukan prospek belum berlangganan di sekitar radius lokasi kamu.")
        return

    for p in prospeks:
        card_text = (
            f"🏢 **{p['nama']}**\n"
            f"🔴 **BELUM BERLANGGANAN - HIGH PRIORITY**\n"
            f"📏 Jarak ke posisi kamu: **{p['dist_to_sales_m']} meter**\n"
            f"📍 {p['alamat'] if p['alamat'] else p['wilayah']}"
        )
        keyboard = [
            [InlineKeyboardButton("📍 Cek ODP & port terdekat", callback_data=f"check_odp_{p['lead_id']}")]
        ]
        await update.message.reply_text(card_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# ---------------------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))

    print("🚀 RADAR Bot Flow 1 Aktif! Silakan tes di Telegram.")
    app.run_polling()

if __name__ == "__main__":
    main()
=======
import os
import math
import pandas as pd
from dotenv import load_dotenv
from telegram import (
    Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

load_dotenv()
bot_token = os.getenv('BOT_TOKEN')

# load dataset ODP (pake raw string 'r' biar backslash path Windows gak error)
odp_df = pd.read_excel(r'C:\Magang 2026\Bot Telegram\DATA ODP WITEL JATIM BARAT 07072026.xlsx', sheet_name='Sheet3')

# buang baris yang koordinatnya rusak
odp_df = odp_df[
    (odp_df['LATITUDE'] != 0) & (odp_df['LONGITUDE'] != 0) &
    (odp_df['LATITUDE'].between(-11, 6)) & (odp_df['LONGITUDE'].between(95, 141))
].reset_index(drop=True)


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                    text="Halo! Selamat datang di bot Telegram saya.")
    await menu(update, context)   

async def puisi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_puisi = "bercahayalah jika kamu ingin dicintai setiap lawan jenis. 😉"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text_puisi)


async def pantun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_pantun = "jalan-jalan ke jakarta barat, pulangnya beli sempolan. kalau kamu tidak ingin bersahabat, mari kita pacaran"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text_pantun)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    print(f"pesan dari user: {message}")


# INLINE KEYBOARD BUTTONS
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📍 Cari ODP", callback_data='cari_odp')],
        [InlineKeyboardButton("❓ Bantuan", callback_data='bantuan')]
    ]
    await update.message.reply_text("Pilih menu:", reply_markup=InlineKeyboardMarkup(keyboard))


# yang terjadi setelah button ditekan
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'cari_odp':
        tombol = KeyboardButton("📍 Kirim Lokasi Saya", request_location=True)
        keyboard = ReplyKeyboardMarkup([[tombol]], resize_keyboard=True, one_time_keyboard=True)
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Kirim titik koordinat kamu 📍\n\n_Proses ambil lokasi GPS mungkin memakan waktu beberapa detik._",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    elif query.data == 'bantuan':
        await query.edit_message_text("Ketik /menu untuk menampilkan menu utama.")


# proses lokasi yang diterima dari user
async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_lat = update.message.location.latitude
    user_lon = update.message.location.longitude

    # kirim pesan sedang proses 
    processing_msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sedang mencari ODP terdekat... ⏳",
        reply_markup=ReplyKeyboardRemove()
    )

    jarak_list = []
    for _, row in odp_df.iterrows():
        jarak = haversine(user_lat, user_lon, row['LATITUDE'], row['LONGITUDE'])
        jarak_list.append({
            'STO': row['Telkom STO'],
            'ODP': row['ODP NAME'],
            'Jarak': jarak,
            'Sisa': row['AVAI'],
            'Lat' : row['LATITUDE'],
            'Lon' : row['LONGITUDE']
        })
    terdekat = sorted(jarak_list, key=lambda x: x['Jarak'])[:5]

    teks = f"Daftar 5 ODP terdekat:\n{'-'*30}\n"
    for i, o in enumerate(terdekat, start=1):
        status = "✅" if o['Sisa'] > 0 else "❌"
        maps_url = f"https://www.google.com/maps/dir/?api=1&destination={o['Lat']},{o['Lon']}"
        teks += f"{i}. {o['STO']} | {o['ODP']} | {o['Jarak']:.1f}m | Sisa: {o['Sisa']} {status} | {maps_url}\n"

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=teks,
        reply_markup=ReplyKeyboardRemove()
    )


app = ApplicationBuilder().token(bot_token).build()
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('puisi', puisi))
app.add_handler(CommandHandler('pantun', pantun))
app.add_handler(CommandHandler('menu', menu))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.LOCATION, handle_location))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

app.run_polling()
>>>>>>> origin/main
