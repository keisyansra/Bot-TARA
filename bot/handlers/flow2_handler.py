import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.db_service import get_nearby_prospects_from_fastapi, search_prospects_from_fastapi
from services.visited_service import mark_as_visited, get_visited_prospect_ids, reset_user_visited


MAX_GPS_RADIUS_METERS = 5000 
PAGE_SIZE = 5

VALID_CITIES = [
    "BATU", "KEDIRI", "BLITAR", "TULUNGAGUNG", "NGANJUK", 
    "BOJONEGORO", "TUBAN", "MADIUN", "NGAWI", "PONOROGO", 
    "MAGETAN", "PACITAN", "MALANG", "KEPANJEN"
]

# buat hapus messages
async def clear_previous_messages(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Menghapus pesan bubble prospek sebelumnya agar chat tetap ringkas"""
    old_msg_ids = context.user_data.get('last_message_ids', [])
    for msg_id in old_msg_ids:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass
    context.user_data['last_message_ids'] = []

# buat next prospek yang udah dicentang
async def send_prospect_page(context: ContextTypes.DEFAULT_TYPE, chat_id: int, page: int = 0):
    """Render bubble daftar prospek dengan proteksi real-time visited filter"""
    
    user_id = chat_id 
    visited_ids = get_visited_prospect_ids(user_id)
    
    all_prospects = [
        item for item in context.user_data.get('all_prospects', [])
        if str(item.get('prospect', {}).get('id')) not in visited_ids
    ]
    context.user_data['all_prospects'] = all_prospects

    if not all_prospects:
        keyboard_back = [
            [InlineKeyboardButton("🔙 Kembali ke Pilihan Flow 2", callback_data="menu_flow2")],
            [InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_back_main")]
        ]
        nav_msg = await context.bot.send_message(
            chat_id=chat_id,
            text="✅ Semua prospek dalam daftar pencarian ini sudah selesai Anda kunjungi!",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard_back)
        )
        context.user_data['last_message_ids'] = [nav_msg.message_id]
        return

    # Pastikan index halaman tidak melebihi batas jika data berkurang
    max_page = (len(all_prospects) - 1) // PAGE_SIZE
    if page > max_page:
        page = max_page

    start_idx = page * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    current_page_items = all_prospects[start_idx:end_idx]

    cache_dict = context.user_data.get('prospects_cache', {})
    for item in current_page_items:
        p_id = item.get('prospect', {}).get('id')
        if p_id:
            cache_dict[str(p_id)] = item
    context.user_data['prospects_cache'] = cache_dict

    new_msg_ids = []

    for idx, item in enumerate(current_page_items, start=start_idx + 1):
        prospect = item.get('prospect', {})
        prospect_id = prospect.get('id')

        raw_nama = prospect.get('name') or prospect.get('nama') or '-'
        raw_alamat = str(prospect.get('alamat') or '-').strip()
        raw_wilayah = prospect.get('wilayah', '-')

        nama = html.escape(str(raw_nama))
        alamat = html.escape(str(raw_alamat))
        wilayah = html.escape(str(raw_wilayah))

        gmaps = prospect.get('url_gmaps') or f"https://www.google.com/maps/search/?api=1&query={nama.replace(' ', '+')}"

        # Cek apakah ada data jarak dari GPS sales
        dist_sales = prospect.get('distance_from_sales_m') or prospect.get('distance_m') or prospect.get('distance')
        if dist_sales is not None and str(dist_sales) != '-':
            dist_line = f"📐 Jarak dari Anda: <b>{round(float(dist_sales), 1)} meter</b>\n"
        else:
            dist_line = ""  

        msg = (
            f"🏢 <b>{idx}. {nama}</b>\n"
            f"📍 Alamat: {alamat} ({wilayah})\n"
            f"{dist_line}"
            f"📌 Status: <b>BELUM BERLANGGANAN</b>\n"
            f"🗺️ <a href='{gmaps}'>Buka Lokasi PT/CV di Google Maps</a>"
        )

        keyboard = [
            [InlineKeyboardButton("📍 Cek ODP Terdekat (<250m)", callback_data=f"check_odp_{prospect_id}")],
            [InlineKeyboardButton("✅ Tandai Sudah Dikunjungi", callback_data=f"visited_{prospect_id}")]
        ]

        sent_msg = await context.bot.send_message(
            chat_id=chat_id,
            text=msg,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        new_msg_ids.append(sent_msg.message_id)

    nav_buttons = []
    pagination_row = []

    if page > 0:
        prev_start = (page - 1) * PAGE_SIZE + 1
        prev_end = page * PAGE_SIZE
        pagination_row.append(
            InlineKeyboardButton(f"⬅️ Sebelumnya ({prev_start}-{prev_end})", callback_data=f"flow2_page_{page - 1}")
        )

    if end_idx < len(all_prospects):
        next_count = min(PAGE_SIZE, len(all_prospects) - end_idx)
        next_range = f"{end_idx + 1}-{end_idx + next_count}"
        pagination_row.append(
            InlineKeyboardButton(f"➡️ Selanjutnya ({next_range})", callback_data=f"flow2_page_{page + 1}")
        )

    if pagination_row:
        nav_buttons.append(pagination_row)

    nav_buttons.append([InlineKeyboardButton("🔙 Kembali ke Pilihan Flow 2", callback_data="menu_flow2")])
    nav_buttons.append([InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_back_main")])

    total_prospects = len(all_prospects)
    current_shown = min(end_idx, total_prospects)

    nav_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=f"✅ Menampilkan <b>{start_idx + 1}-{current_shown} dari {total_prospects}</b> data prospek:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(nav_buttons)
    )
    new_msg_ids.append(nav_msg.message_id)
    context.user_data['last_message_ids'] = new_msg_ids

#buat tandain yang udah dikunjungi (checklist)
async def handle_mark_visited(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler saat sales klik 'Tandai Sudah Dikunjungi'"""
    query = update.callback_query
    await query.answer("✅ Berhasil ditandai sudah dikunjungi!")

    prospect_id = query.data.replace("visited_", "")
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # 1. Simpan ke database SQLite
    mark_as_visited(user_id, prospect_id)

    # 2. Hapus prospek dari list memori sesi saat ini agar tidak muncul lagi saat di-Back/Next
    all_prospects = context.user_data.get('all_prospects', [])
    context.user_data['all_prospects'] = [
        item for item in all_prospects 
        if str(item.get('prospect', {}).get('id')) != str(prospect_id)
    ]

    # 3. Hapus bubble pesan PT tersebut dari layar
    try:
        await query.message.delete()
    except Exception:
        pass

async def handle_flow2_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        "🔍 *FLOW 2: SEARCH PROSPEK & CEK ODP TERDEKAT*\n\n"
        "Silakan pilih metode pencarian prospek/ODP yang ingin digunakan:"
    )

    keyboard = [
        [InlineKeyboardButton("🏢 Cari Berdasarkan Nama PT/CV", callback_data="flow2_by_pt")],
        [InlineKeyboardButton("🌆 Cari Berdasarkan Kota/Witel", callback_data="flow2_by_city")],
        [InlineKeyboardButton("📍 Kirim Lokasi Saat Ini (GPS)", callback_data="flow2_by_location")],
        [InlineKeyboardButton("🔙 Kembali ke Menu Utama", callback_data="menu_back_main")]
    ]

    await query.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# flow utama (search pt cv)
async def handle_flow2_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard_back = [[InlineKeyboardButton("🔙 Kembali ke Pilihan Flow 2", callback_data="menu_flow2")]]

    if query.data == "flow2_by_pt":
        context.user_data['search_mode'] = 'PT'
        await query.message.edit_text(
            "👉 Silakan ketik *Nama PT atau CV* yang ingin dicari:", 
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard_back)
        )

    elif query.data == "flow2_by_city":
        context.user_data['search_mode'] = 'CITY'
        
        # --- MEMBUAT GRID TOMBOL KOTA (3 KOLOM) ---
        cities = [
            "Malang", "Batu", "Kepanjen", 
            "Kediri", "Blitar", "Tulungagung", 
            "Nganjuk", "Bojonegoro", "Tuban", 
            "Madiun", "Ngawi", "Ponorogo"
        ]
        
        keyboard_cities = []
        row = []
        for city in cities:
            row.append(InlineKeyboardButton(city, callback_data=f"search_city_{city}"))
            if len(row) == 3:
                keyboard_cities.append(row)
                row = []
        if row: 
            keyboard_cities.append(row)
            
        keyboard_cities.append([InlineKeyboardButton("🔙 Kembali ke Pilihan Flow 2", callback_data="menu_flow2")])

        await query.message.edit_text(
            "📍 *Silakan pilih Kota/Wilayah dari daftar di bawah ini:*", 
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard_cities)
        )

    elif query.data == "flow2_by_location":
        instructions = (
            "📍 *PETUNJUK PENGIRIMAN LOKASI GPS*\n\n"
            "Silakan gunakan fitur lokasi bawaan Telegram:\n"
            "1. Tekan ikon **Lampiran / Klip Kertas (📎)** di pojok bawah.\n"
            "2. Pilih menu **Location / Lokasi**.\n"
            "3. Klik **Send My Current Location** atau pilih titik pada peta.\n\n"
            "_Bot akan menampilkan prospek terdekat di sekitar lokasi Anda._"
        )
        await query.message.edit_text(
            instructions, 
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard_back)
        )

async def handle_city_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler ketika salah satu tombol kota diklik"""
    query = update.callback_query
    await query.answer()

    # Ambil nama kota dari callback_data (contoh: "search_city_Malang" -> "Malang")
    city_name = query.data.replace("search_city_", "")
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    keyboard_back = [
        [InlineKeyboardButton("🔙 Kembali ke Pilihan Flow 2", callback_data="menu_flow2")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_back_main")]
    ]

    # Ubah teks menu menjadi status loading
    await query.message.edit_text(f"🔍 Mencari data prospek di kota: <b>{html.escape(city_name)}</b>...", parse_mode="HTML")

    # Ambil data dari FastAPI
    prospects = search_prospects_from_fastapi(city_name, limit=20)

    # Filter khusus kota agar lebih akurat
    if prospects:
        filtered_prospects = []
        for item in prospects:
            prospect = item.get('prospect', {})
            p_wilayah = str(prospect.get('wilayah', '')).upper()
            p_alamat = str(prospect.get('alamat', '')).upper()
            if city_name.upper() in p_wilayah or city_name.upper() in p_alamat:
                filtered_prospects.append(item)
        prospects = filtered_prospects

    # Filter out prospek yang sudah pernah dikunjungi oleh sales ini
    visited_ids = get_visited_prospect_ids(user_id)
    prospects = [item for item in prospects if str(item.get('prospect', {}).get('id')) not in visited_ids]

    if not prospects:
        await query.message.edit_text(
            f"❌ Data prospek di kota <b>{html.escape(city_name)}</b> tidak ditemukan atau semua sudah Anda kunjungi.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard_back)
        )
        return

    context.user_data['all_prospects'] = prospects
    context.user_data['prospects_cache'] = {}
    
    # Hapus pesan loading dan bubble lama
    try:
        await query.message.delete()
    except:
        pass
    await clear_previous_messages(context, chat_id)
    
    # Tampilkan bubble prospek
    await send_prospect_page(context, chat_id=chat_id, page=0)

# ketika user share live loc
async def handle_location_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_location = update.message.location
    lat = user_location.latitude
    lon = user_location.longitude
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    keyboard_back = [
        [InlineKeyboardButton("🔙 Kembali ke Pilihan Flow 2", callback_data="menu_flow2")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_back_main")]
    ]

    await update.message.reply_text(f"📍 Lokasi diterima (`{round(lat, 5)}, {round(lon, 5)}`).\nMengambil data..", parse_mode="Markdown")

    prospects = get_nearby_prospects_from_fastapi(lat, lon, limit=20)

    # Filter out prospek yang sudah pernah dikunjungi oleh sales ini
    visited_ids = get_visited_prospect_ids(user_id)
    prospects = [item for item in prospects if str(item.get('prospect', {}).get('id')) not in visited_ids]

    if not prospects:
        await update.message.reply_text(
            "❌ Tidak ditemukan prospek (atau semua prospek terdekat sudah Anda kunjungi).",
            reply_markup=InlineKeyboardMarkup(keyboard_back)
        )
        return

    first_item = prospects[0].get('prospect', {})
    closest_distance = first_item.get('distance_from_sales_m') or first_item.get('distance_m')

    if closest_distance is not None and float(closest_distance) > MAX_GPS_RADIUS_METERS:
        jarak_km = round(float(closest_distance) / 1000, 1)
        await update.message.reply_text(
            f"⚠️ <b>Lokasi di Luar Ruang Lingkup Operasional</b>\n\n"
            f"Titik lokasi Anda saat ini berjarak <b>{jarak_km} km</b> dari wilayah prospek terdekat (Melebihi batas max 5 km).\n\n"
            f"📌 <i>Layanan TARA saat ini hanya mencakup wilayah Witel Jatim Barat (Malang Raya, Kediri Raya, Madiun Raya).</i>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard_back)
        )
        return

    context.user_data['all_prospects'] = prospects
    context.user_data['prospects_cache'] = {}
    
    await clear_previous_messages(context, chat_id)
    await send_prospect_page(context, chat_id=chat_id, page=0)

# ketika user search by teks
async def handle_prospect_text_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = update.message.text.strip()
    search_mode = context.user_data.get('search_mode', 'PT')
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    keyboard_back = [
        [InlineKeyboardButton("🔙 Kembali ke Pilihan Flow 2", callback_data="menu_flow2")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_back_main")]
    ]

    if search_mode == 'CITY':
        city_input_upper = raw_text.upper()
        is_valid_city = any(city in city_input_upper for city in VALID_CITIES)
        
        if not is_valid_city:
            await update.message.reply_text(
                f"⚠️ Kota/Wilayah <b>{html.escape(raw_text)}</b> tidak termasuk dalam ruang lingkup wilayah operasional.\n\n"
                f"📌 <i>Kota yang tersedia: Malang, Batu, Kepanjen, Kediri, Blitar, Tulungagung, Nganjuk, Bojonegoro, Tuban, Madiun, Ngawi, Ponorogo, Magetan, Pacitan.</i>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard_back)
            )
            return

    await update.message.reply_text(f"🔍 Mencari data prospek: <b>{html.escape(raw_text)}</b>...", parse_mode="HTML")

    prospects = search_prospects_from_fastapi(raw_text, limit=20)

    if search_mode == 'CITY' and prospects:
        filtered_prospects = []
        for item in prospects:
            prospect = item.get('prospect', {})
            p_wilayah = str(prospect.get('wilayah', '')).upper()
            p_alamat = str(prospect.get('alamat', '')).upper()
            if raw_text.upper() in p_wilayah or raw_text.upper() in p_alamat:
                filtered_prospects.append(item)
        prospects = filtered_prospects

    # Filter out prospek yang sudah pernah dikunjungi oleh sales ini
    visited_ids = get_visited_prospect_ids(user_id)
    prospects = [item for item in prospects if str(item.get('prospect', {}).get('id')) not in visited_ids]

    if not prospects:
        await update.message.reply_text(
            "❌ Data tidak ditemukan atau sudah Anda tandai dikunjungi.",
            reply_markup=InlineKeyboardMarkup(keyboard_back)
        )
        return

    context.user_data['all_prospects'] = prospects
    context.user_data['prospects_cache'] = {}
    
    await clear_previous_messages(context, chat_id)
    await send_prospect_page(context, chat_id=chat_id, page=0)

# untuk pagination (next prospek)
async def handle_flow2_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    page = int(query.data.replace("flow2_page_", ""))
    chat_id = update.effective_chat.id

    await clear_previous_messages(context, chat_id)
    await send_prospect_page(context, chat_id=chat_id, page=page)

# cek odp terdekat
async def handle_odp_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    prospect_id = query.data.replace("check_odp_", "")
    cache = context.user_data.get('prospects_cache', {})
    item = cache.get(prospect_id)

    if not item:
        await query.message.reply_text("⚠️ Data prospek tidak ditemukan, silakan lakukan pencarian ulang.")
        return

    prospect = item.get('prospect', {})
    nearest_odp = item.get('nearest_odp', {})

    nama_pt = html.escape(str(prospect.get('name') or prospect.get('nama') or '-'))
    odp_name = html.escape(str(nearest_odp.get('name') or '-'))
    raw_odp_dist = nearest_odp.get('distance_m') or nearest_odp.get('distance')
    odp_dist = round(float(raw_odp_dist), 2) if raw_odp_dist is not None else '-'
    odp_port = nearest_odp.get('available_port', 0)
    badge = nearest_odp.get('status')

    odp_lat = nearest_odp.get('latitude')
    odp_lon = nearest_odp.get('longitude')

    if odp_lat and odp_lon:
        odp_gmaps = f"https://www.google.com/maps/search/?api=1&query={odp_lat},{odp_lon}"
    else:
        odp_gmaps = prospect.get('url_gmaps') or f"https://www.google.com/maps/search/?api=1&query={nama_pt.replace(' ', '+')}"

    if badge == 'siap_pasang':
        badge_icon = "🟢 <b>[SIAP PASANG]</b>"
        odp_info = (
            f"📡 Kode ODP: <b>{odp_name}</b>\n"
            f"📏 Jarak ke PT/CV: <b>{odp_dist} meter</b>\n"
            f"🔌 Sisa Port: <b>{odp_port} (AVAIL)</b>"
        )
    elif badge == 'di_luar_radius':
        badge_icon = "🟡 <b>[DI LUAR RADIUS >250m]</b>"
        odp_info = (
            f"📡 Kode ODP Terdekat: <b>{odp_name}</b>\n"
            f"📏 Jarak ke PT/CV: <b>{odp_dist} meter</b> (Cukup Jauh)\n"
            f"🔌 Sisa Port: <b>{odp_port}</b>"
        )
    else:
        badge_icon = "🔴 <b>[ODP TIDAK DITEMUKAN / FULL]</b>"
        odp_info = "⚠️ Tidak ada ODP available dalam radius terdekat dari lokasi ini."

    response = (
        f"📡 <b>HASIL PENGECEKAN ODP TERDEKAT</b>\n"
        f"🏢 Prospek: <b>{nama_pt}</b>\n\n"
        f"{badge_icon}\n"
        f"{odp_info}\n"
        f"🗺️ <a href='{odp_gmaps}'>Buka Titik Lokasi ODP di Google Maps</a>"
    )

    keyboard_quick_nav = [
        [
            InlineKeyboardButton("🔙 Cari Ulang Flow 2", callback_data="menu_flow2"),
            InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_back_main")
        ]
    ]

    sent_msg = await query.message.reply_text(
        text=response, 
        parse_mode="HTML", 
        disable_web_page_preview=True,
        reply_to_message_id=query.message.message_id,
        reply_markup=InlineKeyboardMarkup(keyboard_quick_nav)
    )

    last_ids = context.user_data.get('last_message_ids', [])
    last_ids.append(sent_msg.message_id)
    context.user_data['last_message_ids'] = last_ids

# Untuk tombol reset
async def handle_reset_visited(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler saat sales menjalankan /reset atau menekan tombol reset"""
    user_id = update.effective_user.id
    reset_user_visited(user_id)

    response_text = (
        "✅ <b>Riwayat kunjungan Anda berhasil di-reset!</b>\n\n"
        "Semua prospek yang sebelumnya ditandai kini dapat dicari dan dilihat kembali."
    )
    
    keyboard = [
        [InlineKeyboardButton("🔍 Cari Prospek (Flow 2)", callback_data="menu_flow2")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_back_main")]
    ]

    if update.message:
        await update.message.reply_text(
            response_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.edit_text(
            response_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )