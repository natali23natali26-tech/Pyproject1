import json
import os

import requests
import datetime
import pandas as pd
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path

BASEDIR = Path(__file__).resolve().parent.parent

# API URL для получения курсов валют (или для конвертации)
CURRENCY_API_URL = "https://api.apilayer.com/exchangerates_data/latest"
# URL для конвертации валют
CONVERT_API_URL = "https://api.apilayer.com/exchangerates_data/convert"



def get_greeting(dt_str: str) -> str:
    """ Принимает строку даты (%Y-%m-%d %H:%M:%S) и в зависимости от времени суток передает приветствие"""
    dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    hour = dt.hour
    if 5 <= hour < 12:
        message = "Доброе утро"
    elif 12 <= hour < 17:
        message = "Добрый день"
    elif 17 <= hour < 22:
        message = "Добрый вечер"
    else:
        message = "Доброй ночи"
    return message

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


def get_conversion_rate(from_currency: str, to_currency: str, amount: str) -> Optional[float]:
    """
    Получает стоимость валюты
    :param from_currency: конвертируемая валюта
    :param to_currency: результат конвертации
    :param amount: сумма конвертируемой валюты
    :return: результат конвертации
    """
    load_dotenv(BASEDIR/'.env')
    apikey = os.getenv('API_TOKEN_STOCKS')
    url = f"{CONVERT_API_URL}?from={from_currency}&to={to_currency}&amount={amount}"
    headers= {
        "apikey": apikey
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        rate = data.get("result")
        result = round(float(rate), 2)
        return result
    else:
        print(f"Ошибка при получении данных: {response.status_code} {response.text}")
        return None


def get_currency_rates(curr_list: list[str]) -> list[dict]:
    """
    Получения курса валюта
    :param curr_list: список валют
    :return: результат словарь с курсом валют. Шаблон: [{"currency": ..., "rate": ...},...]
    """
    rates = []
    for curr in curr_list:
        rate = get_conversion_rate(from_currency=curr, to_currency='RUB', amount='1')
        if rate:
            rates.append({"currency": curr, "rate": rate})
    return rates


def get_stock_prices(stock: str) -> Optional[float]:
    load_dotenv(BASEDIR / '.env')
    apikey = os.getenv('API_TOKEN_TWELVEDATA')
    url = f"https://api.twelvedata.com/price?symbol={stock}&apikey={apikey}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        rate = data.get("price")
        result = round(float(rate), 2)
        return result
    else:
        print(f"Ошибка при получении данных: {response.status_code} {response.text}")
        return None
    # stocks = ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]


def get_stock_rate_list(stocks: list) -> list[dict]:
    rates = []
    for stock in stocks:
        price = get_stock_prices(stock)
        if price:
            rates.append({"stock": stock, "price": price})
    return rates



# Пример использования функций
if __name__ == "__main__":
    # print(get_greeting('2025-07-24 15:00:00'))
    # print(get_conversion_rate('USD', 'RUB', '1'))
    # print(get_currency_rates(['USD', 'EUR']))
    # print(get_stock_prices("GOOGL"))
    # print(get_stock_rate_list(["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]))
