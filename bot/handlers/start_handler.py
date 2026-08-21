from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_ID
from services.user_service import get_user_role, register_user, update_user_role

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or "-"
    full_name = user.full_name or "-"

    role = get_user_role(user_id)

    if not role:
        if user_id == int(ADMIN_ID):
            register_user(user_id, username, full_name, 'admin')
            role = 'admin'
        else:
            register_user(user_id, username, full_name, 'pending')
            await update.message.reply_text(
                "⏳ <b>Menunggu Persetujuan Admin</b>\n\n"
                "Akun Anda berhasil didaftarkan ke sistem dan sedang menunggu persetujuan (ACC) dari Admin TARA. "
                "Anda akan menerima notifikasi jika akses sudah diberikan.", 
                parse_mode="HTML"
            )
            
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"🔔 Ada user baru ({full_name}) meminta akses! Ketik /acc untuk meninjau."
                )
            except:
                pass
            return

    # 2. Blokir jika masih pending atau ditolak
    # 2. Blokir jika masih pending atau ditolak
    if role == 'pending':
        await update.message.reply_text("⏳ Akun Anda masih dalam antrean persetujuan Admin. Harap tunggu info selanjutnya.")
        return
    
    elif role == 'rejected':
        # --- FITUR OTOMATIS RE-APPLY ---
        # Ubah statusnya di database jadi pending lagi
        update_user_role(user_id, 'pending')
        
        await update.message.reply_text(
            "⏳ <b>Permintaan Ulang Dikirim</b>\n\n"
            "Permintaan akses Anda telah diajukan kembali ke Admin. Harap tunggu persetujuan.", 
            parse_mode="HTML"
        )
        
        # Kirim notif kilat ke kamu (Admin)
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔔 User yang sebelumnya ditolak ({full_name}) meminta ulang akses! Ketik /acc untuk meninjau."
            )
        except:
            pass
        return

    # 3. Tampilkan Menu Utama jika lolos (Sales / Admin)
    text = (
        f"🤖 Halo, {full_name}! Selamat Datang di Bot TARA\n"
        "<i>(Telkom Prospect & ODP Analytics)</i>\n\n"
        "Silakan pilih menu layanan di bawah ini untuk memulai:"
    )

    keyboard = [
        [InlineKeyboardButton("🔍 Flow 2: Search Prospek & Cek ODP", callback_data="menu_flow2")],
        [InlineKeyboardButton("📈 Flow 3: Analytics Bottleneck (>90%)", callback_data="menu_flow3")],
        [InlineKeyboardButton("❓ Bantuan / Cara Penggunaan", callback_data="menu_help")]
    ]

    if update.message:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))