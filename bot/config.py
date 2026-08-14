import os
from dotenv import load_dotenv

# Membaca file .env
load_dotenv()

# Mengambil BOT_TOKEN dari environment variable (.env)
BOT_TOKEN = os.getenv("BOT_TOKEN")