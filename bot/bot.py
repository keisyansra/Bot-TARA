import logging
import json

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters, ContextTypes
)

from bot.config import BOT_TOKEN

from bot.handlers.flow1_handler import (
    handle_flow1_menu,
    handle_flow1_current_location,
    handle_flow1_search_location,
    handle_flow1_location_search_text,
    handle_flow1_location_gps,
    handle_flow1_retry,
    handle_flow1_map_location
)

from bot.handlers.flow2_handler import (
    handle_flow2_menu,
    handle_flow2_options,
    handle_prospect_text_search, 
    handle_location_search,
    handle_odp_callback
)

from bot.handlers.start_handler import start_command  
from bot.services.external_api import reverse_location
from bot.services.db_service import get_nearby_odps_from_fastapi

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

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

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))

    # --- HANDLERS TOMBOL KLIK (CALLBACK) ---
    # --- FLOW 1 --- 
    app.add_handler(
        CallbackQueryHandler(
            handle_flow1_menu, 
            pattern=r"^menu_flow1$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            handle_flow1_current_location,
            pattern=r"^flow1_current_location$"
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

    # --- FLOW 2 ---
    app.add_handler(
        CallbackQueryHandler(
            handle_flow2_menu,
            pattern=r"^menu_flow2$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            handle_flow2_options,
            pattern=r"^flow2_"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            handle_odp_callback,
            pattern=r"^check_odp_"
        )
    )

    # --- KEMBALI KE MENU UTAMA ---
    app.add_handler(
        CallbackQueryHandler(
            start_command,
            pattern=r"^menu_back_main$"
        )
    )

    # --- INPUT PESAN ---
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