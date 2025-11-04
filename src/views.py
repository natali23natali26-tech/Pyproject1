import json
from datetime import datetime as dt, timedelta
from utils import get_greeting, load_user_settings, get_transactions_for_period, get_top_transactions, \
    get_currency_rates, get_stock_prices


def main_page_data(datetime_str):
    # Получить приветствие
    greeting = get_greeting(datetime_str)

    # Определить период: с начала месяца по входящую дату
    date_obj = dt.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    start_of_month = date_obj.replace(day=1)
    end_date = date_obj.strftime("%Y-%m-%d")
    start_date = start_of_month.strftime("%Y-%m-%d")

    # Получить транзакции за период
    transactions = get_transactions_for_period(start_date, end_date)

    # Обработка транзакций
    total_spent = sum(t['amount'] for t in transactions)
    cashback = total_spent / 100  # 1 рубль на 100 рублей
    top_transactions = get_top_transactions(transactions, 5)

    # Извлечение последних 4 цифр карты
    # Предположим, что у нас есть список карт
    cards = [
        {"card_number": "1234567812345814"},
        {"card_number": "9876543298767512"}
    ]
    cards_data = []
    for card in cards:
        last_digits = card['card_number'][-4:]
        cards_data.append({
            "last_digits": last_digits,
            "total_spent": round(total_spent, 2),
            "cashback": round(cashback, 2)
        })

    # Загружаем настройки пользователя
    settings = load_user_settings()
    user_currencies = settings.get('user_currencies', [])
    user_stocks = settings.get('user_stocks', [])

    # Получаем курсы валют
    currency_rates = get_currency_rates()

    # Получаем цены на акции
    stock_prices = get_stock_prices()

    # Формируем ответ
    response = {
        "greeting": greeting,
        "cards": cards_data,
        "top_transactions": top_transactions,
        "currency_rates": currency_rates,
        "stock_prices": stock_prices
    }

    return json.dumps(response, ensure_ascii=False)
