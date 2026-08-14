import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from config import BOT_TOKEN
from handlers.start_handler import start_command
from handlers.flow2_handler import (
    handle_flow2_menu,
    handle_flow2_options,
    handle_prospect_text_search, 
    handle_location_search,
    handle_odp_callback
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    if not BOT_TOKEN:
        print("❌ Error: BOT_TOKEN belum diatur!")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # --- HANDLERS PERINTAH ---
    app.add_handler(CommandHandler("start", start_command))

    # --- HANDLERS TOMBOL KLIK (CALLBACK) ---
    app.add_handler(CallbackQueryHandler(start_command, pattern=r"^menu_back_main$"))
    app.add_handler(CallbackQueryHandler(handle_flow2_menu, pattern=r"^menu_flow2$"))
    app.add_handler(CallbackQueryHandler(handle_flow2_options, pattern=r"^flow2_"))
    app.add_handler(CallbackQueryHandler(handle_odp_callback, pattern=r"^check_odp_"))

    # --- HANDLERS INPUT PESAN ---
    app.add_handler(MessageHandler(filters.LOCATION, handle_location_search))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prospect_text_search))

    print("🚀 Bot TARA Berhasil Dijalankan! Siap Menerima Pesan...")
    app.run_polling()

if __name__ == "__main__":
    main()