from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /start atau callback tombol Kembali ke Menu Utama"""
    context.user_data["active_flow"] = None
    user_name = update.effective_user.first_name if update.effective_user else "Kak"

    text = (
        f"🤖 *Halo, {user_name}! Selamat Datang di Bot TARA*\n"
        f"_(Telkom Prospect & ODP Analytics)_\n\n"
        f"Silakan pilih menu layanan di bawah ini untuk memulai:"
    )

    keyboard = [
        [InlineKeyboardButton("📍 Cari ODP Terdekat", callback_data="menu_flow1")],
        [InlineKeyboardButton("🔍 Search Prospek & Cek ODP", callback_data="menu_flow2")],
        [InlineKeyboardButton("📈 Analytics Bottleneck (>90%)", callback_data="menu_flow3")],
        
        [InlineKeyboardButton("❓ Bantuan / Cara Penggunaan", callback_data="menu_help")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Jika dipanggil via klik tombol CallbackQuery
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    # Jika dipanggil via ketik /start biasa
    elif update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)