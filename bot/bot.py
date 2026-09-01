import logging
import json

from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from telegram.request import HTTPXRequest

from config import BOT_TOKEN

from handlers.admin_handler import (
    handle_admin_approval,
    acc_command,
    deluser_command,
)

from handlers.start_handler import start_command
from handlers.help_handler import help_command

from handlers.flow1_handler import (
    handle_flow1_menu,
    handle_flow1_search_location,
    handle_flow1_location_search_text,
    handle_flow1_location_gps,
    handle_flow1_retry,
    handle_flow1_map_location,
)

from handlers.flow2_handler import (
    handle_flow2_menu,
    handle_flow2_options,
    handle_prospect_text_search,
    handle_location_search,
    handle_odp_callback,
    handle_flow2_pagination,
    handle_mark_visited,
    handle_reset_visited,
    handle_city_button,
)

from services.external_api import reverse_location
from services.db_service import get_nearby_odps_from_fastapi

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def post_init(application: Application):
    """Memaksa Telegram mengupdate daftar menu command otomatis."""
    commands = [
        BotCommand("start", "Membuka Menu Utama"),
        BotCommand("reset", "Mereset daftar prospek"),
        BotCommand("help", "Menampilkan panduan tutorial"),
        BotCommand("acc", "(Admin) Cek request user baru"),
        BotCommand("deluser", "(Admin) Hapus akses user"),
    ]
    await application.bot.set_my_commands(commands)
    print("✅ Daftar command berhasil di-push ke Telegram!")


# DISPATCHER UNTUK LOCATION 
async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Menentukan LOCATION yang dikirim user harus diproses
    oleh Flow 1 atau Flow 2 berdasarkan active_flow.
    """

    active_flow = context.user_data.get("active_flow")

    print(f"📍 Lokasi diterima | active_flow = {active_flow}")

    if active_flow == "flow1":
        await handle_flow1_location_gps(update, context)

    elif active_flow == "flow2":
        await handle_location_search(update, context)

    else:
        await update.message.reply_text(
            "⚠️ Silakan pilih fitur terlebih dahulu dari Menu Utama."
        )

#DISPATCHER UNTUK TEXT 
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Menentukan TEXT yang dikirim user harus diproses
    oleh Flow 1 atau Flow 2 berdasarkan active_flow.
    """

    active_flow = context.user_data.get("active_flow")

    print(f"💬 TEXT diterima | active_flow = {active_flow}")

    if active_flow == "flow1":
        await handle_flow1_location_search_text(update, context)

    elif active_flow == "flow2":
        await handle_prospect_text_search(update, context)

    else:
        await update.message.reply_text(
            "⚠️ Silakan pilih fitur terlebih dahulu dari Menu Utama."
        )


# MAIN 
def main():
    if not BOT_TOKEN:
        print("❌ Error: BOT_TOKEN belum diatur!")
        return

    request_config = HTTPXRequest(
        connection_pool_size=10,
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0
    )

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # --- HANDLERS PERINTAH ---
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("reset", handle_reset_visited))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("acc", acc_command))
    app.add_handler(CommandHandler("deluser", deluser_command))

    # HANDLERS TOMBOL KLIK (CALLBACK)

    # Admin
    app.add_handler(
        CallbackQueryHandler(
            handle_admin_approval,
            pattern=r"^(approve|reject|undo)_"
        )
    )

    # Kembali ke Menu Utama
    app.add_handler(
        CallbackQueryHandler(
            start_command,
            pattern=r"^menu_back_main$"
        )
    )

    # =========================
    # FLOW 1
    # =========================

    app.add_handler(
        CallbackQueryHandler(
            handle_flow1_menu,
            pattern=r"^menu_flow1$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            handle_flow1_search_location,
            pattern=r"^flow1_search_location$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            handle_flow1_retry,
            pattern=r"^flow1_retry$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            handle_flow1_map_location,
            pattern=r"^flow1_map_location$"
        )
    )

    # =========================
    # FLOW 2
    # =========================

    app.add_handler(
        CallbackQueryHandler(
            handle_flow2_menu,
            pattern=r"^menu_flow2$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            handle_flow2_pagination,
            pattern=r"^flow2_page_\d+$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            handle_flow2_options,
            pattern=r"^flow2_(by_pt|by_city|by_location)$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            handle_city_button,
            pattern=r"^search_city_"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            handle_odp_callback,
            pattern=r"^check_odp_"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            handle_mark_visited,
            pattern=r"^visited_"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            handle_reset_visited,
            pattern=r"^flow2_reset_visited$"
        )
    )

    # Help
    app.add_handler(
        CallbackQueryHandler(
            help_command,
            pattern=r"^menu_help$"
        )
    )

    # =========================
    # INPUT PESAN
    # =========================

    app.add_handler(
        MessageHandler(
            filters.LOCATION,
            handle_location
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text
        )
    )

    print("🚀 Bot TARA Berhasil Dijalankan! Siap Menerima Pesan...")
    app.run_polling()

# --- ENTRY POINT ---
if __name__ == "__main__":
    main()
