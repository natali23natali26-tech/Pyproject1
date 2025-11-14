import logging
from pathlib import Path
from datetime import datetime
from utils import (get_greeting, get_currency_rates,
                   get_stock_rate_list,
                   read_transactions_from_excel,
                   get_card_summary,
                   get_top_transactions,
                   filter_transactions)

# Настраиваем логирование
logger = logging.getLogger(__name__)

CURRENCY_LIST = ['USD', 'EUR']
STOCK_LIST = ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]
BASEDIR = Path(__file__).resolve().parent.parent


def this_home():
    file_patch = str(BASEDIR / 'data' / 'operations.xlsx')
    logger.info(f"Загрузка транзакций из файла: {file_patch}")

    transactions = read_transactions_from_excel(file_patch)
    logger.info(f"Загружено {len(transactions)} транзакций")

    df = filter_transactions(transactions)
    logger.info(f"Отфильтровано {len(df)} транзакций после применения фильтра")

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.debug(f"Текущее время: {now}")

    greeting = get_greeting(now)
    logger.info(f"Сгенерировано приветствие: {greeting}")

    currency_rates = get_currency_rates(CURRENCY_LIST)
    logger.info(f"Получены курсы валют: {[r['currency'] for r in currency_rates]}")

    stock_prices = get_stock_rate_list(STOCK_LIST)
    logger.info(f"Получены цены акций: {[s['stock'] for s in stock_prices]}")

    cards = get_card_summary(df)
    logger.info(f"Сформирована сводка по {len(cards)} картам")

    top_transactions = get_top_transactions(df)
    logger.info(f"Определено {len(top_transactions)} топ-транзакций")

    result = {
        "greeting": greeting,
        "cards": cards,
        "top_transactions": top_transactions,
        "currency_rates": currency_rates,
        "stock_prices": stock_prices
    }
    logger.info("Главная страница успешно сформирована")

    return result

# Пример использования функции this_home
if __name__ == '__main__':
    print(this_home())
