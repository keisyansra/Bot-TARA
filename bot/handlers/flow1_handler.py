import html

from telegram import (
    Update,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from services.db_service import get_nearby_odps_from_fastapi
from services.external_api import search_location, reverse_location 

async def handle_flow1_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Menampilkan pilihan cara mencari ODP:
    1. Menentukan lokasi melalui Telegram
    2. Mencari lokasi berdasarkan nama/alamat
    """

    context.user_data["active_flow"] = "flow1"
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "🗺️ Tentukan Lokasi di Peta",
                callback_data="flow1_map_location"
            )
        ],
        [
            InlineKeyboardButton(
                "🔎 Cari ODP",
                callback_data="flow1_search_location"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 Menu Utama",
                callback_data="menu_back_main"
            )
        ]
    ]

    await query.message.edit_text(
        "📡 <b>CARI ODP</b>\n\n"
        "Bagaimana kamu ingin menentukan lokasi?",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_flow1_map_location(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Memberikan petunjuk kepada user untuk memilih
    lokasi menggunakan fitur Location bawaan Telegram.
    """

    context.user_data["active_flow"] = "flow1"

    query = update.callback_query
    await query.answer()

    keyboard_back = [[
        InlineKeyboardButton(
            "⬅️ Kembali ke Pilihan Flow 1",
            callback_data="menu_flow1"
        )
    ]]

    await query.message.edit_text(
        "📍 <b>PETUNJUK PENGIRIMAN LOKASI</b>\n\n"
        "Silakan gunakan fitur lokasi bawaan Telegram:\n\n"
        "1. Tekan ikon Lampiran (📎) di samping kolom pesan.\n"
        "2. Pilih menu Location / Lokasi.\n"
        "3. Pilih Send My Current Location (Lokasi saat ini) ATAU geser peta dan tekan Send selected location (Lokasi pilihan).\n\n"
        "📡 Setelah lokasi dikirim, Bot TARA akan mencari 5 ODP terdekat dari titik tersebut.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard_back)
    )

async def handle_flow1_search_location(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Meminta user memasukkan nama lokasi/alamat.
    """
    context.user_data["active_flow"] = "flow1"
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "🔎 <b>CARI ODP</b>\n\n"
        "Ketik nama lokasi atau alamat yang ingin kamu cari.\n\n"
        "Bot TARA akan mencari 5 ODP terdekat dari lokasi tersebut.\n\n"
        "Contoh:\n"
        "• Alun-Alun Kota Malang\n"
        "• Jl. Soekarno Hatta, Malang\n"
        "• Universitas Brawijaya",
        parse_mode="HTML"
    )

    # Menandai bahwa user sedang berada di mode pencarian lokasi
    context.user_data["flow1_searching_location"] = True


async def handle_flow1_location_search_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Menerima teks lokasi dari user, kemudian mencari koordinat
    menggunakan Nominatim.
    """

    location_name = update.message.text.strip()

    # Pastikan user memang sedang dalam mode pencarian lokasi
    if not context.user_data.get("flow1_searching_location"):
        return

    context.user_data["flow1_searching_location"] = True

    processing_msg = await update.message.reply_text(
        "🔎 Sedang mencari lokasi... ⏳"
    )

    # Cari lokasi menggunakan Nominatim
    location = search_location(location_name)

    # Kalau lokasi tidak ditemukan
    if location is None:
        await processing_msg.edit_text(
            "⚠️ <b>Lokasi tidak ditemukan.</b>\n\n"
            "Coba masukkan nama lokasi atau alamat "
            "yang lebih spesifik.\n\n"
            "Contoh:\n"
            "• Alun-Alun Kota Malang\n"
            "• Jl. Soekarno Hatta, Malang\n"
            "• Universitas Brawijaya\n\n"
            "Silakan coba lagi.",
            parse_mode="HTML"
        )

        # Aktifkan kembali mode pencarian
        context.user_data["flow1_searching_location"] = True

        return

    # Kalau lokasi ditemukan
    lat = location["latitude"]
    lon = location["longitude"]

    await processing_msg.edit_text(
        "📍 Lokasi ditemukan.\n\n"
        f"<b>{html.escape(location['display_name'])}</b>\n\n"
        "Sedang mencari ODP terdekat... ⏳",
        parse_mode="HTML"
    )

    # Cari ODP berdasarkan koordinat hasil Nominatim
    await send_nearby_odps(
        update=update,
        context=context,
        lat=lat,
        lon=lon
    )


async def handle_flow1_location_gps(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Menerima lokasi GPS yang dikirim langsung oleh user.
    """

    user_location = update.message.location

    lat = user_location.latitude
    lon = user_location.longitude

    # Hilangkan keyboard "Kirim Lokasi Saya"
    await update.message.reply_text(
        "📍 Lokasi diterima.\n\n"
        "Sedang mencari ODP terdekat... ⏳",
        reply_markup=ReplyKeyboardRemove()
    )

    await send_nearby_odps(
        update=update,
        context=context,
        lat=lat,
        lon=lon
    )

async def send_nearby_odps(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    lat: float,
    lon: float
):
    """
    Mengambil ODP terdekat dari FastAPI dan menampilkan hasilnya
    ke Telegram.
    """

    odps = get_nearby_odps_from_fastapi(
        lat=lat,
        lon=lon,
        limit=5
    )

    # Tidak ada ODP
    if not odps:
        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Kembali ke Pilihan Flow 1",
                    callback_data="flow1_retry"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Menu Utama",
                    callback_data="menu_back_main"
                )
            ]
        ]

        await update.message.reply_text(
            "❌ <b>ODP tidak ditemukan.</b>\n\n"
            "Tidak ditemukan ODP dengan port tersedia "
            "di sekitar lokasi tersebut.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    teks = "📡 <b>ODP TERDEKAT</b>\n\n"

    keyboard = []

    for i, odp in enumerate(odps, start=1):

        nama = html.escape(
            str(odp.get("name") or "Nama ODP tidak tersedia")
        )

        witel = html.escape(
            str(odp.get("witel") or "-")
        )

        available_port = odp.get(
            "available_port",
            0
        )

        distance = odp.get(
            "distance_from_sales_m"
        )

        if distance is not None:
            distance_text = f"{float(distance):.1f} meter"
        else:
            distance_text = "-"

        latitude = odp.get("latitude")
        longitude = odp.get("longitude")

        gmaps_url = f"https://www.google.com/maps?q={latitude},{longitude}"

        teks += (
            f"<b>{i}. {nama}</b>\n"
            f"   Witel: {witel}\n"
            f"   Jarak: {distance_text}\n"
            f"   Available Port: {available_port}\n"
            f"  🗺 <a href='{gmaps_url}'>Lihat di Google Maps</a>\n\n"
        )

    # Tombol navigasi
    keyboard.append([
        InlineKeyboardButton(
            "⬅️ Kembali ke Pilihan Flow 1",
            callback_data="flow1_retry"
        )
    ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 Menu Utama",
            callback_data="menu_back_main"
        )
    ])

    await update.message.reply_text(
        teks,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_flow1_retry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Mengulang proses pencarian ODP.
    """

    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "🗺️ Tentukan Lokasi di Peta",
                callback_data="flow1_map_location"
            )
        ],
        [
            InlineKeyboardButton(
                "🔎 Cari ODP",
                callback_data="flow1_search_location"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 Menu Utama",
                callback_data="menu_back_main"
            )
        ]
    ]

    await query.message.reply_text(
        "🔄 <b>CARI ODP LAGI</b>\n\n"
        "Bagaimana kamu ingin menentukan lokasi?",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
