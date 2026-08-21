import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from telegram import BotCommand
from handlers.admin_handler import handle_admin_approval, acc_command, deluser_command
from handlers.admin_handler import handle_admin_approval, acc_command
from handlers.admin_handler import handle_admin_approval
from telegram.request import HTTPXRequest
from config import BOT_TOKEN
from handlers.start_handler import start_command
from handlers.help_handler import help_command  
from handlers.flow2_handler import (
    handle_flow2_menu,
    handle_flow2_options,
    handle_prospect_text_search, 
    handle_location_search,
    handle_odp_callback,
    handle_flow2_pagination,
    handle_mark_visited,
    handle_reset_visited,
    handle_city_button
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


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

    app = Application.builder().token(BOT_TOKEN).build()

    # HANDLERS PERINTAH (COMMAND)
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("reset", handle_reset_visited))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("acc", acc_command))
    app.add_handler(CommandHandler("deluser", deluser_command))

    # HANDLERS TOMBOL KLIK (CALLBACK)
    app.add_handler(CallbackQueryHandler(handle_admin_approval, pattern=r"^(approve|reject|undo)_"))
    app.add_handler(CallbackQueryHandler(start_command, pattern=r"^menu_back_main$"))
    app.add_handler(CallbackQueryHandler(handle_flow2_menu, pattern=r"^menu_flow2$"))
    app.add_handler(CallbackQueryHandler(handle_flow2_pagination, pattern=r"^flow2_page_\d+$"))
    app.add_handler(CallbackQueryHandler(handle_flow2_options, pattern=r"^flow2_(by_pt|by_city|by_location)$"))
    app.add_handler(CallbackQueryHandler(handle_city_button, pattern=r"^search_city_"))
    app.add_handler(CallbackQueryHandler(handle_odp_callback, pattern=r"^check_odp_"))
    app.add_handler(CallbackQueryHandler(handle_mark_visited, pattern=r"^visited_"))
    app.add_handler(CallbackQueryHandler(handle_reset_visited, pattern=r"^flow2_reset_visited$"))
    app.add_handler(CallbackQueryHandler(help_command, pattern=r"^menu_help$"))
    

    # HANDLERS INPUT PESAN 
    app.add_handler(MessageHandler(filters.LOCATION, handle_location_search))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prospect_text_search))
    

    print("🚀 Bot TARA Berhasil Dijalankan! Siap Menerima Pesan...")
    app.run_polling()

if __name__ == "__main__":
    main()