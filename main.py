import subprocess
import sys
import os
import sqlite3
import threading
import time
import re
import html as html_module
import atexit
import random
import string
import logging
import shutil
from datetime import datetime, timedelta
from threading import Thread

import psutil
import telebot
from telebot import types
import requests
from flask import Flask

# ========== AUTO INSTALL MISSING MODULES ==========
required_modules = ['psutil', 'pyTelegramBotAPI', 'flask', 'requests']

for module in required_modules:
    try:
        __import__(module)
    except ImportError:
        print(f"📦 Installing {module}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", module])

# ========== FLASK KEEP-ALIVE ==========
app = Flask('')

@app.route('/')
def home():
    return "⚡ DEV-KiKi Core - Universal Python & JS Cloud Hosting"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("🟣 Flask Keep-Alive started.")

# ========== BOT CONFIG ==========
bot_token = os.environ.get('BOT_TOKEN')  # ← GitHub Secret ကနေ ယူမယ်
OWNER_ID = int(os.environ.get("OWNER_ID", 7308292609))
ADMIN_ID = int(os.environ.get("ADMIN_ID", 7308292609))
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", '@kiki20251')

DATABASE_PATH = 'dev-KiKi_bot.db'

DEFAULT_FORCE_CHANNEL_IDS = [-1002236605624, -1003068786628]
DEFAULT_FORCE_GROUP_ID = -1002236605624

DEFAULT_CHANNEL_LINKS = {
    -1002236605624: "https://t.me/KMM_MOD1",
    -1003068786628: "https://t.me/Sketchware_Beginner_Developer"
}
DEFAULT_GROUP_LINK = "https://t.me/M_MOD1"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_BOTS_DIR = os.path.join(BASE_DIR, 'upload_bots')
os.makedirs(UPLOAD_BOTS_DIR, exist_ok=True)

bot = telebot.TeleBot(bot_token, threaded=True, num_threads=10)

# Global variables
bot_scripts = {}
bot_scripts_lock = threading.Lock()
user_subscriptions = {}
user_files = {}
active_users = set()
admin_ids = {ADMIN_ID, OWNER_ID}
banned_users = set()
bot_locked = False
force_join_enabled = True
FREE_USER_LIMIT = 1
force_channel_ids = list(DEFAULT_FORCE_CHANNEL_IDS)
force_group_id = DEFAULT_FORCE_GROUP_ID

SUPPORTED_EXTENSIONS = {'.py': '🐍 Python', '.js': '🟨 JavaScript (Node.js)'}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

invite_links = {}
conn = None

# ========== ကျန်တဲ့ ကုဒ်အားလုံး (ယခင်ကုဒ်ကနေ ကူးထည့်ပါ) ==========
# ... (သင့်မူရင်း ကုဒ်ရဲ့ ကျန်တဲ့အပိုင်း အားလုံး ထည့်ပါ) ...

# အောက်ပါ function နှစ်ခုကို အစားထိုးပါ
def create_force_join_message():
    channels = [get_channel_name(ch_id) for ch_id in force_channel_ids]
    ch_text = "\n".join([f"├─ {name}" for name in channels])
    return f"""
╔══════════════════════════╗
║   🔐 <b>အဖွဲ့ဝင်ဖြစ်ရန် လိုအပ်</b>   ║
╚══════════════════════════╝

📣 <b>ချန်နယ်များ</b>
{ch_text}
👥 <b>အုပ်စု</b>
└─ {get_group_name(force_group_id)}

✅ အောက်ပါခလုတ်များနှိပ် → စစ်ဆေးပါ
    """

def create_force_join_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch_id in force_channel_ids:
        link = get_or_create_invite_link(ch_id)
        name = get_channel_name(ch_id).replace("<b>","").replace("</b>","")
        markup.add(types.InlineKeyboardButton(f"📣 {name}", url=link))
    
    group_link = get_or_create_invite_link(force_group_id)
    markup.add(types.InlineKeyboardButton("👥 အုပ်စုသို့ဝင်ရန်", url=group_link))
    markup.add(types.InlineKeyboardButton("✅ အဖွဲ့ဝင်စစ်ဆေးပါ", callback_data='check_membership'))
    return markup

# ကျန်တဲ့ ကုဒ်ကို ဆက်ထည့်ပါ (ယခင်ကုဒ်အတိုင်း)
if __name__ == '__main__':
    keep_alive()
    install_nodejs()
    while True:
        try:
            bot.infinity_polling(timeout=60)
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(5)
