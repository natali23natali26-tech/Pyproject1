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

# def load_user_settings(filepath='user_settings.json'):
#     with open(filepath, 'r', encoding='utf-8') as f:
#         settings = json.load(f)
#     return settings

def read_transactions_from_excel(excel_path):
    """
    Считывает финансовые операции из Excel-файла.
    Args:
        excel_path (str): Путь к Excel-файлу.
    Returns:
        list: Список словарей с транзакциями.
    """
    try:
        df = pd.read_excel(excel_path)  # Читаем данные из Excel файла в DataFrame
        transactions = df.to_dict(orient='records')  # Преобразуем DataFrame в список словарей
        return transactions  # Возвращаем список транзакций
    except FileNotFoundError:
        print(f"Ошибка: Файл не найден по пути {excel_path}")  # Обрабатываем ошибку, если файл не найден
        return []
    except Exception as e:
        print(f"Ошибка при чтении Excel-файла: {e}")  # Обрабатываем любые другие исключения
        return []




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

def filter_transactions(transactions):
    df = pd.DataFrame(transactions)
    df_filter = df[(df["Сумма платежа"] < 0) & (~df["Категория"].isin(['Наличные', 'Переводы'])) & (df["Категория"].notna())]
    return df_filter

def get_card_summary(df) -> list[dict]:
    cards = []
    group = df.groupby("Номер карты").agg({'Сумма платежа': 'sum'})
    cards_dict = group.to_dict(orient = 'index')
    for key, value in cards_dict.items():
        last_digits = key[-4:]
        total_spent = abs(value['Сумма платежа'])
        cashback = round(total_spent / 100, 2)
        card = {
            "last_digits": last_digits,
            "total_spent": total_spent,
            "cashback": cashback
        }
        cards.append(card)
    return cards


def get_top_transactions(df, count=5):
    top_list = []
    df_sorted = df.sort_values(by='Сумма платежа', ascending=True)
    top = df_sorted.head(count)
    top_transaction = top.to_dict(orient='records')
    for trancas in top_transaction:
        date = trancas['Дата платежа']
        amount = abs(trancas['Сумма платежа'])
        category = trancas['Категория']
        description = trancas['Описание']
        transaction ={
            "date": date,
            "amount": amount,
            "category": category,
            "description": description
        }
        top_list.append(transaction)
    return top_list


# Пример использования функций
if __name__ == "__main__":
    transactions = read_transactions_from_excel('../data/operations.xlsx')
    df = filter_transactions(transactions)
    print(get_top_transactions(df))
    # print(transactions)
    # print(get_card_summary(df))
    # print(get_greeting('2025-07-24 15:00:00'))
    # print(get_conversion_rate('USD', 'RUB', '1'))
    # print(get_currency_rates(['USD', 'EUR']))
    # print(get_stock_prices("GOOGL"))
    # print(get_stock_rate_list(["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]))
