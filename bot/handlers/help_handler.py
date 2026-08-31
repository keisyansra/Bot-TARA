from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler panduan penggunaan fitur Bot TARA."""
    
    text = (
        "📖 <b>PANDUAN PENGGUNAAN BOT TARA</b>\n"
        "<i>(Telkom Prospect & ODP Analytics)</i>\n\n"
        "<b>1. 📍 Cek ODP Terdekat</b>\n"
        "Fokus ke ketersediaan jaringan/infrastruktur secara cepat.\n\n"
        "• <b>Tentukan Lokasi di Peta:</b>\n"
        "Gunakan fitur lokasi Telegram.\n"
        "Tekan 📎 → Location → pilih titik pada peta → Send selected location.\n\n"
        "• <b>Cari ODP:</b>\n"
        "Ketik nama jalan, gedung, atau area secara manual di kolom chat untuk mencari ODP di sekitarnya.\n\n"
        "<b>2. 🏢 Cari Prospek Terdekat</b>\n"
        "Fokus ke aktivitas hunting dan daftar PT/CV yang belum berlangganan.\n\n"
        "• <b>Cari via Nama PT/CV:</b>\n"
        "Ketik nama instansi/perusahaan.\n\n"
        "• <b>Cari via Kota/Witel:</b>\n"
        "Klik tombol pilihan kota/wilayah yang muncul di layar.\n"
        "Contoh: Malang, Kediri, Madiun.\n\n"
        "• <b>Cari via GPS:</b>\n"
        "Gunakan fitur lokasi Telegram.\n"
        "Tekan 📎 → Location → Send My Current Location.\n\n"
        "• <b>Cek ODP:</b>\n"
        "Klik tombol <b>[📍 Cek ODP Terdekat]</b> di bawah detail PT untuk melihat ketersediaan port ODP.\n\n"
        "• <b>Tandai Kunjungan:</b>\n"
        "Klik <b>[✅ Tandai Sudah Dikunjungi]</b> agar prospek tersebut tidak muncul lagi di pencarian Anda.\n\n"
        "<b>3. ⚙️ Command</b>\n\n"
        "<code>/start</code>\n"
        "Membuka Menu Utama.\n\n"
        "<code>/reset</code>\n"
        "Mereset daftar prospek yang sudah pernah ditandai/dikunjungi.\n\n"
        "<code>/help</code>\n"
        "Menampilkan panduan tutorial ini.\n\n"
        "<code>/acc</code>\n"
        "Khusus Admin — mengecek request akses user baru.\n\n"
        "<code>/deluser</code>\n"
        "Khusus Admin — menghapus akses user yang sudah terdaftar.\n\n"
        "Butuh bantuan lebih lanjut atau mengalami kendala teknis?\n"
        "Hubungi PIC Admin: @nadaalmira"
    )

    keyboard = [
        [InlineKeyboardButton("💬 Hubungi PIC Admin", url="https://t.me/nadaalmira")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_back_main")]
    ]

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.edit_text(
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif update.message:
        await update.message.reply_text(
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
