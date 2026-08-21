from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_ID
from services.user_service import get_pending_users, update_user_role
from services.user_service import get_pending_users, update_user_role, delete_user

async def acc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /acc untuk melihat daftar user yang minta akses (Hanya untuk Admin)"""
    if update.effective_user.id != int(ADMIN_ID):
        await update.message.reply_text("⛔ Anda tidak memiliki hak akses untuk perintah ini.")
        return

    pending_users = get_pending_users()

    if not pending_users:
        await update.message.reply_text("✅ Tidak ada antrean permintaan akses saat ini.")
        return

    await update.message.reply_text("📋 <b>Daftar Permintaan Akses (Pending):</b>", parse_mode="HTML")

    for user_id, username, full_name in pending_users:
        text = (
            f"👤 <b>Nama:</b> {full_name}\n"
            f"🔗 <b>Username:</b> @{username}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>"
        )
        keyboard = [
            [
                InlineKeyboardButton("✅ Terima (Sales)", callback_data=f"approve_{user_id}"),
                InlineKeyboardButton("❌ Tolak", callback_data=f"reject_{user_id}")
            ]
        ]
        await update.message.reply_text(
            text, 
            parse_mode="HTML", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def handle_admin_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler ketika Admin menekan tombol Terima / Tolak / Undo"""
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != int(ADMIN_ID):
        await query.answer("⛔ Hanya admin yang bisa klik tombol ini!", show_alert=True)
        return

    action, target_user_id = query.data.split("_")
    target_user_id = int(target_user_id)

    if action == "approve":
        update_user_role(target_user_id, "sales")
        await query.message.edit_text(f"✅ Akses <b>Disetujui</b> untuk User ID: <code>{target_user_id}</code>.", parse_mode="HTML")
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id, 
                text="🎉 <b>Akses Disetujui!</b>\nAdmin telah memberikan akses. Silakan ketik /start untuk membuka Menu Utama.",
                parse_mode="HTML"
            )
        except:
            pass

    elif action == "reject":
        update_user_role(target_user_id, "rejected")
        
        keyboard = [[InlineKeyboardButton("↩️ Batal Tolak (Kembalikan ke Pending)", callback_data=f"undo_{target_user_id}")]]
        
        await query.message.edit_text(
            f"❌ Akses <b>Ditolak</b> untuk User ID: <code>{target_user_id}</code>.", 
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id, 
                text="⛔ Maaf, permintaan akses Anda ke Bot TARA ditolak oleh Admin.\n\n_Jika Anda merasa ini adalah kesalahan, silakan ketik /start kembali untuk meminta ulang._", 
                parse_mode="Markdown"
            )
        except:
            pass

    elif action == "undo":
        update_user_role(target_user_id, "pending")
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Terima (Sales)", callback_data=f"approve_{target_user_id}"),
                InlineKeyboardButton("❌ Tolak", callback_data=f"reject_{target_user_id}")
            ]
        ]
        await query.message.edit_text(
            f"⏳ Status dikembalikan ke <b>Pending</b> untuk User ID: <code>{target_user_id}</code>.\nSilakan pilih tindakan:", 
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
async def deluser_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /deluser <id_telegram> untuk menghapus user dari database (Hanya Admin)"""

    if update.effective_user.id != int(ADMIN_ID):
        await update.message.reply_text("⛔ Anda tidak memiliki hak akses untuk perintah ini.")
        return

    if not context.args:
        await update.message.reply_text(
            "⚠️ <b>Format salah!</b>\nContoh cara pakai: <code>/deluser 1798054457</code>",
            parse_mode="HTML"
        )
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID harus berupa angka!")
        return

    success = delete_user(target_id)
    if success:
        await update.message.reply_text(f"🗑️ Akses untuk User ID <code>{target_id}</code> <b>berhasil dihapus</b> dari sistem.", parse_mode="HTML")
    else:
        await update.message.reply_text(f"❓ User ID <code>{target_id}</code> tidak ditemukan di dalam database.", parse_mode="HTML")