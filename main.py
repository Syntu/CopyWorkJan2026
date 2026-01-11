import os
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Direct Token halda pani huncha PythonAnywhere ma yadi .env milena vane
TOKEN = "TAPAIKO_BOT_TOKEN_YAHA_HALNUHOS"

# Function to fetch live trading data
def fetch_live_trading_data(symbol):
    url = "https://www.sharesansar.com/live-trading"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        if not table: return None
        rows = table.find_all('tr')[1:]
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 10: continue
            if cols[1].text.strip().upper() == symbol.upper():
                return {
                    'LTP': cols[2].text.strip(),
                    'Change': cols[4].text.strip(),
                    'High': cols[6].text.strip(),
                    'Low': cols[7].text.strip(),
                    'Vol': cols[8].text.strip(),
                    'PClose': cols[9].text.strip()
                }
    except Exception as e:
        print(f"Error: {e}")
    return None

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("नमस्ते! म NEPSE Bot। मलाई कुनै कम्पनीको Symbol पठाउनुहोस (उदा: SHINE, NICA)")

async def handle_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.strip().upper()
    await update.message.reply_chat_action("typing")
    
    data = fetch_live_trading_data(symbol)
    if data:
        res = (
            f"📊 <b>Stock: {symbol}</b>\n\n"
            f"LTP: रू {data['LTP']}\n"
            f"Change: {data['Change']}%\n"
            f"High/Low: {data['High']} / {data['Low']}\n"
            f"Volume: {data['Vol']}\n"
            f"Prev Close: {data['PClose']}\n\n"
            "<i>Source: ShareSansar</i>"
        )
    else:
        res = f"'{symbol}' को डेटा भेटिएन। बजार बन्द भएको हुन सक्छ वा Symbol गलत छ।"
    
    await update.message.reply_text(res, parse_mode=ParseMode.HTML)

if __name__ == "__main__":
    print("Bot is starting...")
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_stock))
    application.run_polling()
