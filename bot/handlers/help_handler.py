from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler panduan cara penggunaan bot langkah demi langkah (Tutorial Flow 2 & Flow 3)"""
    
    text = (
        "📖 <b>PANDUAN PENGGUNAAN BOT TARA</b>\n"
        "<i>(Telkom Prospect & ODP Analytics)</i>\n\n"
        "Berikut langkah-langkah penggunaan fitur utama di Bot TARA:\n\n"
        "🔍 <b>1. Flow 2: Search Prospek & Cek ODP</b>\n"
        "• <b>Cari via Nama PT/CV:</b> Pilih menu lalu ketik nama instansi/perusahaan.\n"
        "• <b>Cari via Kota/Witel:</b> Pilih menu lalu ketik nama kota (contoh: <i>Malang, Kediri, Madiun</i>).\n"
        "• <b>Cari via GPS (Live Location):</b> Tekan ikon lampiran (📎) -> Pilih <b>Location</b> -> Kirim lokasi Anda saat ini.\n"
        "• <b>Cek ODP:</b> Klik tombol <b>[📍 Cek ODP Terdekat]</b> di bawah bubble PT untuk melihat ketersediaan port ODP.\n"
        "• <b>Tandai Kunjungan:</b> Klik <b>[✅ Tandai Sudah Dikunjungi]</b> agar prospek tersebut tidak muncul lagi di pencarian Anda.\n\n"
        "📈 <b>2. Flow 3: Analytics Bottleneck (>90%)</b>\n"
        "• Digunakan untuk melihat daftar ODP yang utilitas port-nya hampir penuh (≥90%) di setiap wilayah/witel.\n\n"
        "⚙️ <b>3. Perintah Cepat (Command):</b>\n"
        "• <code>/start</code> : Kembali ke Menu Utama.\n"
        "• <code>/reset</code> : Mereset daftar prospek yang sudah pernah ditandai.\n"
        "• <code>/help</code> : Menampilkan panduan tutorial ini.\n\n"
        "❓ <i>Butuh bantuan lebih lanjut atau kendala teknis? Hubungi PIC Admin di bawah.</i>"
    )

    keyboard = [
        [InlineKeyboardButton("💬 Hubungi PIC Admin", url="https://t.me/username_admin")],
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