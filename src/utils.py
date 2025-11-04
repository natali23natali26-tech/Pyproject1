import json
import requests
import datetime
import pandas as pd

# API URL для получения курсов валют (или для конвертации)
CURRENCY_API_URL = "https://api.apilayer.com/exchangerates_data/latest"
# URL для конвертации валют
CONVERT_API_URL = "https://api.apilayer.com/exchangerates_data/convert"
STOCK_API_URL = "https://finnhub.io/api/v1/quote?symbol={}"
API_TOKEN_STOCKS = "P9scVvXKu3F1SdIqsS0nKYndV8xBvxbC"

def get_greeting(dt_str):
    dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    hour = dt.hour
    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 17:
        return "Добрый день"
    elif 17 <= hour < 22:
        return "Добрый вечер"
    else:
        return "Доброй ночи"

def load_user_settings(filepath='user_settings.json'):
    with open(filepath, 'r', encoding='utf-8') as f:
        settings = json.load(f)
    return settings

def get_transactions_for_period(start_date, end_date):
    # Заготовка для получения транзакций
    transactions = [
        {
            "date": "2021-12-21",
            "amount": 1198.23,
            "category": "Переводы",
            "description": "Перевод Кредитная карта. ТП 10.2 RUR"
        },
        {
            "date": "2021-12-20",
            "amount": 829.00,
            "category": "Супермаркеты",
            "description": "Лента"
        },
        {
            "date": "2021-12-20",
            "amount": 421.00,
            "category": "Различные товары",
            "description": "Ozon.ru"
        },
        {
            "date": "2021-12-16",
            "amount": -14216.42,
            "category": "ЖКХ",
            "description": "ЖКУ Квартира"
        },
        {
            "date": "2021-12-16",
            "amount": 453.00,
            "category": "Бонусы",
            "description": "Кешбэк за обычные покупки"
        },
    ]
    # Можно добавить фильтр по дате, если есть реальные данные
    return transactions

def get_top_transactions(transactions, count=5):
    df = pd.DataFrame(transactions)
    df_sorted = df.sort_values(by='amount', ascending=False)
    top = df_sorted.head(count)
    return top.to_dict(orient='records')

def get_currency_rates():
    try:
        response = requests.get(CURRENCY_API_URL, headers={
            "apikey": "P9scVvXKu3F1SdIqsS0nKYndV8xBvxbC"  # API ключ
        })
        response.raise_for_status()
        data = response.json()
        rates = []
        for curr in ["USD", "EUR"]:
            rate = data['rates'].get(curr)
            if rate:
                rates.append({"currency": curr, "rate": rate})
        return rates
    except Exception as e:
        print(f"Ошибка получения курсов валют: {e}")
        return []

def get_conversion_rate(from_currency, to_currency, amount):
    url = f"{CONVERT_API_URL}?from={from_currency}&to={to_currency}&amount={amount}"
    headers= {
        "apikey": "P9scVvXKu3F1SdIqsS0nKYndV8xBvxbC"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("result")
    else:
        print(f"Ошибка при получении данных: {response.status_code} {response.text}")
        return None

def get_stock_prices():
    stocks = ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]
    prices = []
    for stock in stocks:
        try:
            url = STOCK_API_URL.format(stock)
            response = requests.get(url, params={'token': API_TOKEN_STOCKS})
            response.raise_for_status()
            data = response.json()
            price = data.get('c')  # текущая цена
            if price:
                prices.append({"stock": stock, "price": price})
        except Exception as e:
            print(f"Ошибка при получении цены {stock}: {e}")
    return prices

# Пример использования функций
if __name__ == "__main__":
    # Получение текущих курсов валют
    rates = get_currency_rates()
    print("Курсы валют:", rates)

    # Конвертация 100 USD в EUR
    converted_amount = get_conversion_rate("USD", "EUR", 100)
    if converted_amount:
        print(f"100 USD равно {converted_amount} EUR")

    # Получение цен акций
    stock_prices = get_stock_prices()
    print("Цены акций:", stock_prices)
