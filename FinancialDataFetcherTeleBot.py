import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import pytz
import logging
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Optional
import sys
import os
import telebot
import re



# Telegram Bot Configuration
API_TOKEN = 'API KEY'
bot = telebot.TeleBot(API_TOKEN)

# Basic configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]  # Console output only
)
logger = logging.getLogger(__name__)

# Application settings
CONFIG = {
    'base_url': 'https://www.tgju.org',
    'timeout': 15,
    'max_retries': 3,
    'retry_delay': 2,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'currency_ids': {
        'price_dollar_rl': 'US Dollar',
    'price_eur': 'Euro',
    'price_gbp': 'British Pound',
    'price_try': 'Turkish Lira',
    'price_aed': 'UAE Dirham',
    'price_cny': 'Chinese Yuan',
    'price_rub': 'Russian Ruble',
    'price_jpy': 'Japanese Yen',
    'price_inr': 'Indian Rupee',
    'price_sar': 'Saudi Riyal',
    'price_cad': 'Canadian Dollar',
    'price_aud': 'Australian Dollar',
    'price_chf': 'Swiss Franc',
    'price_sek': 'Swedish Krona',
    'price_nok': 'Norwegian Krone',
    'price_dkk': 'Danish Krone',
    'price_kwd': 'Kuwaiti Dinar',
    'price_bhd': 'Bahraini Dinar',
    'price_omr': 'Omani Rial',
    'price_qar': 'Qatari Riyal'
    },
    'gold_items': {
        'geram18': '18K Gold (per gram)',
        'sekeb': ' Emami Gold Coin',
        'nim': 'Half Emami Gold Coin',
        'rob': 'Quarter Emami Gold Coin',
        'geram24': '24K Gold (per gram)'
    },
    'crypto_ids': {  # ✅ NEW
        'bitcoin': 'Bitcoin',
        'ethereum': 'Ethereum',
        'tether': 'Tether',
        'dogecoin': 'Dogecoin',
        'litecoin': 'Litecoin'
    }

}


class FinancialDataFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': CONFIG['user_agent']})
        self.tehran_timezone = pytz.timezone('Asia/Tehran')

    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[BeautifulSoup]:
        for attempt in range(CONFIG['max_retries']):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=CONFIG['timeout']
                )
                response.raise_for_status()
                return BeautifulSoup(response.text, 'html.parser')
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < CONFIG['max_retries'] - 1:
                    time.sleep(CONFIG['retry_delay'])
                continue
        return None

    def fetch_crypto(self) -> Dict:
        """Fetch cryptocurrency prices via TGJU's JSON API"""
        logger.info("Fetching cryptocurrency prices via TGJU API...")
        url = "https://api.tgju.org/v1/market/dataservice/crypto-assets?type=performance"
        try:
            response = self.session.get(url, timeout=CONFIG['timeout'])
            response.raise_for_status()
            result = response.json()

            cryptos = {}
            for entry in result.get('data', []):
                sym = entry.get('symbol')
                if not sym:
                    continue
                name = sym  # or map symbol to full name if preferred

                price_irr = entry.get('p_irr') or entry.get('p')
                change = entry.get('dp') or entry.get('d')

                cryptos[name] = {
                    'price': f"{price_irr} IRR",
                    'change': f"{change}",
                    'timestamp': self._get_current_time()
                }
            return cryptos

        except Exception as e:
            logger.error(f"Failed to fetch crypto: {e}")
            return {}

    def fetch_currencies(self) -> Dict:
        """Fetch currency rates from TGJU"""
        logger.info("Fetching currency rates...")
        soup = self._make_request(f"{CONFIG['base_url']}/currency")
        if not soup:
            return {}

        currencies = {}
        for currency_id, name in CONFIG['currency_ids'].items():
            element = soup.find('tr', {'data-market-row': currency_id})
            if element:
                price_element = element.find('td', {'class': 'nf'})
                change_element = element.find('td', {'class': 'change'})

                price = price_element.get_text(strip=True) if price_element else 'N/A'
                change = change_element.get_text(strip=True) if change_element else 'N/A'

                currencies[name] = {
                    'price': f"{price} IRR",
                    'change': change,
                    'timestamp': self._get_current_time()
                }
        return currencies

    def fetch_gold_and_coins(self) -> Dict:
        """Fetch gold and coin prices from TGJU"""
        logger.info("Fetching gold and coin prices...")
        results = {}

        def fetch_item(item_id, item_name):
            soup = self._make_request(f"{CONFIG['base_url']}/profile/{item_id}")
            if not soup:
                return None

            price_element = soup.find('span', {'class': 'value'})
            change_element = soup.find('span', {'class': 'change'})

            price = price_element.get_text(strip=True) if price_element else 'N/A'
            change = change_element.get_text(strip=True) if change_element else 'N/A'

            return {
                'price': f"{price} IRR",
                'change': change,
                'timestamp': self._get_current_time()
            }

        # Using multithreading for faster execution
        with ThreadPoolExecutor() as executor:
            futures = {}
            for item_id, item_name in CONFIG['gold_items'].items():
                futures[item_name] = executor.submit(fetch_item, item_id, item_name)

            for name, future in futures.items():
                result = future.result()
                if result:
                    results[name] = result

        return results

    def fetch_all(self) -> Dict:
        """Fetch all financial data concurrently"""
        logger.info("Starting to fetch all financial data...")
        start_time = time.time()

        with ThreadPoolExecutor() as executor:
            currencies_future = executor.submit(self.fetch_currencies)
            gold_future = executor.submit(self.fetch_gold_and_coins)
            crypto_future = executor.submit(self.fetch_crypto)  # ✅ NEW

            results = {
                "Foreign Currencies": currencies_future.result(),
                "Gold & Coins": gold_future.result(),
                "Cryptocurrencies": crypto_future.result(),  # ✅ NEW
                "metadata": {
                    "source": "TGJU.ORG",
                    "fetch_time": self._get_current_time(),
                    "execution_time": f"{time.time() - start_time:.2f} seconds"
                }
            }

        logger.info("Successfully fetched all financial data")
        return results

    def _get_current_time(self) -> str:
        """Get current time in Tehran timezone"""
        return datetime.now(self.tehran_timezone).strftime("%Y-%m-%d %H:%M:%S %Z%z")




class DataVisualizer:
    @staticmethod
    def create_price_chart(data: Dict, category: str, filename: str = None):
        """Create a price chart for a specific category"""
        items = data.get(category, {})
        if not items:
            logger.warning(f"No data available for category: {category}")
            return

        names = []
        prices = []

        price_data = []
        for name, details in items.items():
            price_str = re.sub(r'[^\d\.]', '', details['price'])
            if price_str:
                price_data.append((name, float(price_str)))

        # sort by price descending
        price_data.sort(key=lambda x: x[1], reverse=True)

        names, prices = zip(*price_data) if price_data else ([], [])


class TGJUFinanceBot:
    def __init__(self):
        self.fetcher = FinancialDataFetcher()
        self.visualizer = DataVisualizer()

# Initialize the bot handler
finance_bot = TGJUFinanceBot()


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = """
    🤖 *ربات قیمت ارز و طلا و رمزارز* 🤖

    این ربات آخرین قیمت‌های ارز و طلا و رمزارز را از سایت TGJU نمایش می‌دهد.

    دستورات:
    /currencies - نمایش قیمت ارزها
    /gold - نمایش قیمت طلا و سکه
    /crypto نمایش قیمت رمزارز ها
    """
    bot.reply_to(message, welcome_text, parse_mode='Markdown')


@bot.message_handler(commands=['currencies'])
def send_currencies(message):
    try:
        data = finance_bot.fetcher.fetch_currencies()

        output = "💵 *نرخ ارزها:*\n\n"
        output += f"⏰ آخرین بروزرسانی: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        for name, details in data.items():
            change_icon = "📈" if '-' not in details['change'] else "📉"
            output += f"- {name}: {details['price']} ({change_icon} {details['change']})\n"
        bot.send_message(message.chat.id, output, parse_mode='Markdown')
        bot.send_message(message.chat.id, """دستورات:
    /currencies - نمایش قیمت ارزها
    /gold - نمایش قیمت طلا و سکه
    /crypto نمایش قیمت رمزارز هاش قیمت رمزارز ها""")


    except Exception as e:
        bot.reply_to(message, f"خطا در دریافت اطلاعات ارزها: {str(e)}")


@bot.message_handler(commands=['gold'])
def send_gold(message):
    try:
        data = finance_bot.fetcher.fetch_gold_and_coins()

        output = "🏅 *قیمت طلا و سکه:*\n\n"
        output += f"⏰ آخرین بروزرسانی: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        for name, details in data.items():
            change_icon = "📈" if '-' not in details['change'] else "📉"
            output += f"- {name}: {details['price']} ({change_icon} {details['change']})\n"
        bot.send_message(message.chat.id, output, parse_mode='Markdown')
        bot.send_message(message.chat.id, """دستورات:
    /currencies - نمایش قیمت ارزها
    /gold - نمایش قیمت طلا و سکه
    /crypto نمایش قیمت رمزارز ها""")


    except Exception as e:
        bot.reply_to(message, f"خطا در دریافت اطلاعات طلا و سکه: {str(e)}")

@bot.message_handler(commands=['crypto'])
def send_crypto(message):
    try:
        data = finance_bot.fetcher.fetch_crypto()
        output = "💲 *رمزارز :*\n\n"
        output += f"⏰ آخرین بروزرسانی: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        for name, details in data.items():
            change_icon = "📈" if '-' not in details['change'] else "📉"
            output += f"- {name}: {details['price']} ({change_icon} {details['change']})\n"
        bot.send_message(message.chat.id, output, parse_mode='Markdown')
        bot.send_message(message.chat.id, """دستورات:
    /currencies - نمایش قیمت ارزها
    /gold - نمایش قیمت طلا و سکه
    /crypto نمایش قیمت رمزارز ها""" )

    except Exception as e:
        bot.reply_to(message, f"خطا در دریافت اطلاعات رمز ارز ها: {str(e)}")



if __name__ == "__main__":
    print("Bot is running...")
    bot.polling()
