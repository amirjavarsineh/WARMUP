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
        'price_jpy': 'Japanese Yen'
    },
    'gold_items': {
        'geram18': '18K Gold (per gram)',
        'sekeb': 'Emami Gold Coin',
        'nim': 'Half Emami Gold Coin',
        'rob': 'Quarter Emami Gold Coin',
        'geram24': '24K Gold (per gram)'
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

            results = {
                "Foreign Currencies": currencies_future.result(),
                "Gold & Coins": gold_future.result(),
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

        for name, details in items.items():
            try:
                # Extract numeric value from price string
                price_str = details['price'].replace('IRR', '').replace(',', '').strip()
                price = float(price_str)

                names.append(name)
                prices.append(price)
            except (ValueError, KeyError) as e:
                logger.warning(f"Could not process price for {name}: {str(e)}")
                continue

        if not names:
            logger.warning("No valid data to plot")
            return

        plt.figure(figsize=(12, 6))
        bars = plt.bar(names, prices, color=['gold' if 'Gold' in name or 'Coin' in name else 'skyblue' for name in names])

        plt.title(f'{category} Prices - {data["metadata"]["fetch_time"]}')
        plt.xlabel('Item')
        plt.ylabel('Price (IRR)')
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        # Add values on top of each bar
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2., height,
                     f'{height:,.0f}',
                     ha='center', va='bottom')

        plt.tight_layout()

        if filename:
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            logger.info(f"Chart saved as {filename}")
        else:
            plt.show()

        plt.close()


class DataExporter:
    @staticmethod
    def save_to_json(data: Dict, filename: str):
        """Save data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info(f"Data successfully saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save JSON file: {str(e)}")

    @staticmethod
    def save_to_csv(data: Dict, filename: str):
        """Save data to CSV file"""
        try:
            flat_data = []
            for category, items in data.items():
                if category == 'metadata':
                    continue

                for name, details in items.items():
                    flat_data.append({
                        'category': category,
                        'name': name,
                        'price': details['price'],
                        'change': details['change'],
                        'timestamp': details['timestamp']
                    })

            df = pd.DataFrame(flat_data)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            logger.info(f"Data successfully saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save CSV file: {str(e)}")

    @staticmethod
    def save_to_excel(data: Dict, filename: str):
        """Save data to Excel file"""
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                for category, items in data.items():
                    if category == 'metadata':
                        continue

                    flat_data = []
                    for name, details in items.items():
                        flat_data.append({
                            'Name': name,
                            'Price': details['price'],
                            'Change': details['change'],
                            'Timestamp': details['timestamp']
                        })

                    df = pd.DataFrame(flat_data)
                    df.to_excel(writer, sheet_name=category[:31], index=False)

            logger.info(f"Data successfully saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save Excel file: {str(e)}")


class TGJUFinanceApp:
    def __init__(self):
        self.fetcher = FinancialDataFetcher()
        self.visualizer = DataVisualizer()
        self.exporter = DataExporter()

    def run(self):
        """Run the application"""
        print("\n" + "=" * 60)
        print("💰 TGJU Financial Data Fetcher".center(60))
        print("=" * 60)

        try:
            # Fetch data
            data = self.fetcher.fetch_all()

            # Display results
            self._display_results(data)

            # Save data
            self._save_data_prompt(data)

            # Generate charts
            self._generate_charts_prompt(data)

            print("\n✅ Operation completed successfully.")

        except KeyboardInterrupt:
            print("\n❌ Operation canceled by user.")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            sys.exit(1)

    def _display_results(self, data: Dict):
        """Display results in a formatted way"""
        print("\n" + "=" * 60)
        print("📊 Financial Data Results".center(60))
        print("=" * 60)
        print(f"Fetch Time: {data['metadata']['fetch_time']}")
        print(f"Execution Time: {data['metadata']['execution_time']}")
        print("-" * 60)

        for category, items in data.items():
            if category == 'metadata':
                continue

            print(f"\n🔹 {category.upper()}:")
            print("-" * 60)
            for name, details in items.items():
                change_color = '\033[92m' if '-' not in details['change'] else '\033[91m'
                reset_color = '\033[0m'

                print(f"{name:<30}: {details['price']:>20} \t{change_color}{details['change']}{reset_color}")
            print("-" * 60)

    def _save_data_prompt(self, data: Dict):
        """Prompt user to save data"""
        choice = input("\nDo you want to save the data? (y/n): ").strip().lower()
        if choice == 'y':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"tgju_finance_{timestamp}"

            # Create output directory if it doesn't exist
            os.makedirs('output', exist_ok=True)

            try:
                # Save in different formats
                self.exporter.save_to_json(data, f"output/{base_filename}.json")
                self.exporter.save_to_csv(data, f"output/{base_filename}.csv")
                self.exporter.save_to_excel(data, f"output/{base_filename}.xlsx")

                print("Data successfully saved in 'output' directory.")
            except Exception as e:
                print(f"Error saving files: {str(e)}")

    def _generate_charts_prompt(self, data: Dict):
        """Prompt user to generate charts"""
        choice = input("\nDo you want to generate charts? (y/n): ").strip().lower()
        if choice == 'y':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs('charts', exist_ok=True)

            for category in data.keys():
                if category == 'metadata':
                    continue

                filename = f"charts/{category}_{timestamp}.png"
                self.visualizer.create_price_chart(data, category, filename)

            print("Charts successfully saved in 'charts' directory.")


if __name__ == "__main__":
    app = TGJUFinanceApp()
    app.run()