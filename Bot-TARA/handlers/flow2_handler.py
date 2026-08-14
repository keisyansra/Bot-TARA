import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.db_service import get_nearby_prospects_from_fastapi, search_prospects_from_fastapi

async def handle_flow2_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler Menu Utama Flow 2"""
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

async def handle_flow2_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sub-menu pilihan Flow 2"""
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
        await query.message.edit_text(
            "👉 Silakan ketik *Nama Kota / Witel* (misal: *Malang*, *Kepanjen*, *Batu*):", 
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard_back)
        )

    elif query.data == "flow2_by_location":
        instructions = (
            "📍 *PETUNJUK PENGIRIMAN LOKASI GPS*\n\n"
            "Silakan gunakan fitur lokasi bawaan Telegram:\n"
            "1. Tekan ikon **Lampiran / Klip Kertas (📎)** di pojok bawah.\n"
            "2. Pilih menu **Location / Lokasi**.\n"
            "3. Klik **Send My Current Location** atau pilih titik pada peta.\n\n"
            "_Bot akan otomatis menampilkan 5 Prospek Terdekat dari lokasi Anda._"
        )
        await query.message.edit_text(
            instructions, 
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard_back)
        )

async def handle_location_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler saat sales Share Live Location GPS"""
    user_location = update.message.location
    lat = user_location.latitude
    lon = user_location.longitude

    await update.message.reply_text(f"📍 Lokasi diterima (`{round(lat, 5)}, {round(lon, 5)}`).\nMengambil data dari Backend Dyan...", parse_mode="Markdown")

    prospects = get_nearby_prospects_from_fastapi(lat, lon, limit=5)

    if not prospects:
        keyboard_empty = [
            [InlineKeyboardButton("🔙 Kembali ke Pilihan Flow 2", callback_data="menu_flow2")],
            [InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_back_main")]
        ]
        await update.message.reply_text(
            "❌ Tidak ditemukan prospek di sekitar lokasi Anda.",
            reply_markup=InlineKeyboardMarkup(keyboard_empty)
        )
        return

    # Simpan cache berdasar prospect ID
    cache_dict = {}
    for item in prospects:
        p_data = item.get('prospect', {})
        p_id = p_data.get('id')
        if p_id:
            cache_dict[str(p_id)] = item
    context.user_data['prospects_cache'] = cache_dict

    for idx, item in enumerate(prospects, 1):
        prospect = item.get('prospect', {})
        prospect_id = prospect.get('id')

        # BACA FIELD SESUAI STRUKTUR BARU DYAN
        raw_nama = prospect.get('name') or prospect.get('nama') or 'PT/CV Tanpa Nama'
        raw_alamat = (prospect.get('alamat') or 'Alamat Tidak Tersedia').strip()
        raw_wilayah = prospect.get('wilayah', '-')
        
        dist_sales = prospect.get('distance_from_sales_m')
        dist_str = f"{round(float(dist_sales), 1)} meter" if dist_sales is not None else "-"

        nama = html.escape(str(raw_nama))
        alamat = html.escape(str(raw_alamat))
        wilayah = html.escape(str(raw_wilayah))

        gmaps = prospect.get('url_gmaps') or f"https://www.google.com/maps/search/?api=1&query={nama.replace(' ', '+')}"
        match_status = prospect.get('customer_match_status')

        match_warning = ""
        if match_status in ["MATCH_CONFIDENT_SINGLE_TOKEN", "MATCH_POSSIBLE_SINGLE_TOKEN"]:
            match_warning = "\n⚠️ <b>Catatan:</b> Nama mirip dengan pelanggan lama (1 kata sama). Mohon verifikasi manual sebelum penawaran.\n"

        msg = (
            f"🏢 <b>{idx}. {nama}</b>\n"
            f"📍 Alamat: {alamat} ({wilayah})\n"
            f"📏 Jarak dari Anda: <b>{dist_str}</b>\n"
            f"📌 Status: <b>BELUM BERLANGGANAN</b>\n"
            f"{match_warning}"
            f"🗺️ <a href='{gmaps}'>Buka Lokasi PT/CV di Google Maps</a>"
        )

        keyboard = [[
            InlineKeyboardButton(
                "📍 Cek ODP Terdekat (<250m)", 
                callback_data=f"check_odp_{prospect_id}"
            )
        ]]

        await update.message.reply_text(
            msg, 
            parse_mode="HTML", 
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    nav_keyboard = [
        [InlineKeyboardButton("🔙 Kembali ke Pilihan Flow 2", callback_data="menu_flow2")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_back_main")]
    ]
    await update.message.reply_text(
        "✅ <b>Pencarian selesai.</b> Silakan pilih aksi selanjutnya:", 
        parse_mode="HTML", 
        reply_markup=InlineKeyboardMarkup(nav_keyboard)
    )

async def handle_prospect_text_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler saat sales ketik Nama PT/CV atau Kota"""
    raw_text = update.message.text.strip()

    await update.message.reply_text(f"🔍 Mencari data prospek: <b>{html.escape(raw_text)}</b>...", parse_mode="HTML")

    prospects = search_prospects_from_fastapi(raw_text, limit=5)

    if not prospects:
        keyboard_empty = [
            [InlineKeyboardButton("🔙 Kembali ke Pilihan Flow 2", callback_data="menu_flow2")],
            [InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_back_main")]
        ]
        await update.message.reply_text(
            "❌ Data tidak ditemukan atau sudah berlangganan.",
            reply_markup=InlineKeyboardMarkup(keyboard_empty)
        )
        return

    cache_dict = {}
    for item in prospects:
        p_data = item.get('prospect', {})
        p_id = p_data.get('id')
        if p_id:
            cache_dict[str(p_id)] = item
    context.user_data['prospects_cache'] = cache_dict

    for idx, item in enumerate(prospects, 1):
        prospect = item.get('prospect', {})
        prospect_id = prospect.get('id')

        # BACA FIELD SESUAI STRUKTUR BARU DYAN
        raw_nama = prospect.get('name') or prospect.get('nama') or 'PT/CV Tanpa Nama'
        raw_alamat = (prospect.get('alamat') or 'Alamat Tidak Tersedia').strip()
        raw_wilayah = prospect.get('wilayah', '-')

        nama = html.escape(str(raw_nama))
        alamat = html.escape(str(raw_alamat))
        wilayah = html.escape(str(raw_wilayah))

        gmaps = prospect.get('url_gmaps') or f"https://www.google.com/maps/search/?api=1&query={nama.replace(' ', '+')}"
        match_status = prospect.get('customer_match_status')

        match_warning = ""
        if match_status in ["MATCH_CONFIDENT_SINGLE_TOKEN", "MATCH_POSSIBLE_SINGLE_TOKEN"]:
            match_warning = "\n⚠️ <b>Catatan:</b> Nama mirip dengan pelanggan lama (1 kata sama). Mohon verifikasi manual sebelum penawaran.\n"

        msg = (
            f"🏢 <b>{idx}. {nama}</b>\n"
            f"📍 Alamat: {alamat} ({wilayah})\n"
            f"📌 Status: <b>BELUM BERLANGGANAN</b>\n"
            f"{match_warning}"
            f"🗺️ <a href='{gmaps}'>Buka Lokasi PT/CV di Google Maps</a>"
        )

        keyboard = [[
            InlineKeyboardButton(
                "📍 Cek ODP Terdekat (<250m)", 
                callback_data=f"check_odp_{prospect_id}"
            )
        ]]

        await update.message.reply_text(
            msg, 
            parse_mode="HTML", 
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    nav_keyboard = [
        [InlineKeyboardButton("🔙 Kembali ke Pilihan Flow 2", callback_data="menu_flow2")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_back_main")]
    ]
    await update.message.reply_text(
        "✅ <b>Pencarian selesai.</b> Silakan pilih aksi selanjutnya:", 
        parse_mode="HTML", 
        reply_markup=InlineKeyboardMarkup(nav_keyboard)
    )

async def handle_odp_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler saat tombol 'Cek ODP Terdekat' diklik"""
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
    raw_odp_dist = nearest_odp.get('distance_m')
    odp_dist = round(float(raw_odp_dist), 2) if raw_odp_dist is not None else '-'
    odp_port = nearest_odp.get('available_port', 0)
    badge = nearest_odp.get('status')

    # Link Google Maps
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

    # REPLYS TO SPECIFIC MESSAGE (Bubble Balasan Tepat di Bawah Bubble PT/CV)
    await query.message.reply_text(
        response, 
        parse_mode="HTML", 
        disable_web_page_preview=True,
        reply_to_message_id=query.message.message_id # <--- INI KUNCI UTAMANYA
    )