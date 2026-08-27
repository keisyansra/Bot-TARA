import os
import math
import pandas as pd
import glob
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

#PERLU DIBENARKAN!!!!
file_list = glob()
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
app.add_handler(CommandHandler('flow1', start))
app.add_handler(CommandHandler('menu', menu))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.LOCATION, handle_location))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

app.run_polling()