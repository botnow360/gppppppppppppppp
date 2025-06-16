import logging, os, time, requests
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL = os.getenv("TELEGRAM_CHANNEL_ID")

bot = Bot(token=TOKEN)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")

def get_spot():
    r = requests.get("https://api.mexc.com/api/v3/ticker/price", timeout=10)
    return {item["symbol"]: float(item["price"]) for item in r.json() if item["symbol"].endswith("USDT")}

def get_fut():
    r = requests.get("https://contract.mexc.com/api/v1/contract/ticker", timeout=10)
    return {item["symbol"]: float(item["lastPrice"]) for item in r.json().get("data", [])}

def check():
    spot = get_spot(); fut = get_fut()
    for sym, sp in spot.items():
        fsym = sym + "_USDT" if not sym.endswith("_USDT") else sym
        if fsym in fut and sp != 0:
            fr = fut[fsym]
            spread = abs(fr - sp) / sp * 100
            if spread >= 5:
                msg = (f"🔔 Spread Alert for {sym}:\n"
                       f"Spot: {sp:.4f}\n"
                       f"Futures: {fr:.4f}\n"
                       f"💥 Spread: {spread:.2f}%")
                bot.send_message(CHANNEL, msg)
                logging.info("Sent alert: %s", sym)

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(check, 'interval', seconds=60)
    scheduler.start()
    logging.info("Bot started on Python %s", os.getenv("PYTHON_VERSION", ""))
    while True:
        time.sleep(60)
