import os
import requests
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from dotenv import load_dotenv

# Environment variables load garne
load_dotenv()

# --- RENDER KO LAGI FLASK SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_flask():
    # Render le automatic PORT provide garchha, natra 8080 use hunchha
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    # Bot sangai Flask server pani background ma chalauna
    t = Thread(target=run_flask)
    t.start()
# ----------------------------------

# Global variables
users = {}
active_users = set()

# Function to fetch live trading data
def fetch_live_trading_data(symbol):
    url = "https://www.sharesansar.com/live-trading"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        if not table:
            return None

        rows = table.find_all('tr')[1:]
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 10: continue
            row_symbol = cols[1].text.strip()

            if row_symbol.upper() == symbol.upper():
                return {
                    'LTP': float(cols[2].text.strip().replace(',', '')),
                    'Change Percent': cols[4].text.strip(),
                    'Day High': float(cols[6].text.strip().replace(',', '')),
                    'Day Low': float(cols[7].text.strip().replace(',', '')),
                    'Volume': cols[8].text.strip(),
                    'Previous Close': float(cols[9].text.strip().replace(',', ''))
                }
    except Exception as e:
        print(f"Error live data: {e}")
    return None

# Function to fetch 52-week data
def fetch_52_week_data(symbol):
    url = "https://www.sharesansar.com/today-share-price"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        if not table:
            return None

        rows = table.find_all('tr')[1:]
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 24: continue
            row_symbol = cols[1].text.strip()

            if row_symbol.upper() == symbol.upper():
                return {
                    '52 Week High': float(cols[22].text.strip().replace(',', '')),
                    '52 Week Low': float(cols[23].text.strip().replace(',', ''))
                }
    except Exception as e:
        print(f"Error 52 week: {e}")
    return None

# Function to combine data
def fetch_stock_data(symbol):
    live_data = fetch_live_trading_data(symbol)
    week_data = fetch_52_week_data(symbol)

    if live_data and week_data:
        ltp = live_data['LTP']
        wh = week_data['52 Week High']
        wl = week_data['52 Week Low']

        live_data.update(week_data)
        live_data['Down From High'] = round(((wh - ltp) / wh) * 100, 2) if wh else 0
        live_data['Up From Low'] = round(((ltp - wl) / wl) * 100, 2) if wl else 0
        return live_data
    return None

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Store user (In-memory, will reset on restart)
    users[chat_id] = {"name": user.full_name, "username": user.username}
    
    welcome_text = (
        f"नमस्ते {user.first_name}! 🙏\n"
        "Syntoo's NEPSE BOT मा स्वागत छ।\n"
        "कुनै पनि कम्पनीको Symbol टाइप गर्नुहोस। (उदा: SHINE, NICA)"
    )
    await update.message.reply_text(welcome_text)

async def handle_stock_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().upper()
    # Simple check for symbols (usually 3-5 chars)
    if len(text) > 6: return

    symbol = text.replace("/", "") # Slash hatauna
    await update.message.reply_chat_action("typing")
    
    data = fetch_stock_data(symbol)
    if data:
        res = (
            f"📊 <b>Stock: {symbol}</b>\n\n"
            f"LTP: रू {data['LTP']}\n"
            f"Change: {data['Change Percent']}%\n"
            f"Day High/Low: {data['Day High']} / {data['Day Low']}\n"
            f"52W High/Low: {data['52 Week High']} / {data['52 Week Low']}\n"
            f"Volume: {data['Volume']}\n\n"
            f"📉 Down from High: {data['Down From High']}%\n"
            f"📈 Up from Low: {data['Up From Low']}%\n\n"
            "<i>Data provided by ShareSansar</i>"
        )
    else:
        res = f"माफ गर्नुहोस, '{symbol}' को डेटा फेला परेन। कृपया सही Symbol राख्नुहोस।"
    
    await update.message.reply_text(res, parse_mode=ParseMode.HTML)

if __name__ == "__main__":
    TOKEN = os.getenv("TELEGRAM_API_KEY")
    if not TOKEN:
        print("Error: TELEGRAM_API_KEY not found!")
        exit(1)

    # 1. Flask server background ma start garne
    keep_alive()

    # 2. Bot build garne
    application = ApplicationBuilder().token(TOKEN).build()

    # 3. Handlers thapne
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_stock_symbol))

    # 4. Bot run garne
    print("Bot is starting...")
    application.run_polling()
