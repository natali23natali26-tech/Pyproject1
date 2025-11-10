import os
import requests
import datetime
import pandas as pd
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path

from pandas import DataFrame

BASEDIR = Path(__file__).resolve().parent.parent

# API URL для получения курсов валют (или для конвертации)
CURRENCY_API_URL = "https://api.apilayer.com/exchangerates_data/latest"
# URL для конвертации валют
CONVERT_API_URL = "https://api.apilayer.com/exchangerates_data/convert"


def get_greeting(dt_str: str) -> str:
    """
    Принимает строку даты (%Y-%m-%d %H:%M:%S) и в зависимости от времени суток передает приветствие
    :param dt_str: дата
    :return: приветствие
    """
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


def read_transactions_from_excel(excel_path: str) -> list[dict]:
    """
    Считывает транзакции из Excel-файла и возвращает их в виде списка словарей.

    Функция загружает данные с первого листа файла, преобразует каждую строку
    в словарь, где ключи — названия столбцов (например, «Дата платежа», «Сумма платежа» и т.д.).

    :param excel_path: Путь к Excel-файлу (формат .xlsx или .xls).
    :type excel_path: str
    :return: Список словарей, представляющих транзакции.
             Каждый словарь соответствует одной строке в таблице.
             В случае ошибки возвращается пустой список.
    :rtype: List[Dict[str, Any]]

    :raises FileNotFoundError: Если файл по указанному пути не найден.
    :raises Exception: Если произошла ошибка при чтении файла (некорректный формат и т.п.).
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
    load_dotenv(BASEDIR / '.env')
    apikey = os.getenv('API_TOKEN_STOCKS')
    url = f"{CONVERT_API_URL}?from={from_currency}&to={to_currency}&amount={amount}"
    headers = {
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
    """
    Получает текущую цену одной акции через API Twelvedata
    """
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
    """
    Формирует список словарей с названием акции и ценой на нее
    :param stocks: идентификатор актива
    """
    rates = []
    for stock in stocks:
        price = get_stock_prices(stock)
        if price:
            rates.append({"stock": stock, "price": price})
    return rates


def filter_transactions(transactions: list[dict]) -> DataFrame:
    """
    Фильтрует транзакции, оставляя только расходы по заданным критериям.

    Отбирает транзакции, которые:
    - являются расходами (сумма платежа < 0);
    - не относятся к категориям «Наличные» и «Переводы»;
    - имеют заполненную (не NaN) категорию.

    :param transactions: Список словарей с данными о транзакциях.
                         Каждый словарь должен содержать:
                         - "Сумма платежа" (float/int): сумма операции;
                         - "Категория" (str или NaN): категория транзакции.
    :type transactions: List[Dict[str, Any]]
    :return: DataFrame с отфильтрованными транзакциями.
    :rtype: pandas.DataFrame

    Пример входных данных:
    [
        {
            "Дата платежа": "2023-10-01",
            "Сумма платежа": -1500.0,
            "Категория": "Еда",
            "Описание": "Обед"
        },
        ...
    ]
    """
    df = pd.DataFrame(transactions)
    df_filter = df[
        (df["Сумма платежа"] < 0) & (~df["Категория"].isin(['Наличные', 'Переводы'])) & (df["Категория"].notna())]
    return df_filter


def get_card_summary(df: DataFrame) -> list[dict]:
    """
   Формирует сводную статистику по банковским картам на основе транзакций.

    Для каждой уникальной карты вычисляет:
    - последние 4 цифры номера карты;
    - общую сумму расходов (по модулю, чтобы учесть отрицательные значения);
    - кэшбэк в размере 1% от суммы трат, округлённый до 2 знаков.

    :param df: DataFrame с транзакциями. Должен содержать столбцы:
               - "Номер карты" (str): полный номер карты;
               - "Сумма платежа" (float/int): сумма операции (отрицательная — расход).
    :type df: pandas.DataFrame
    :return: Список словарей с информацией по каждой карте. Каждый словарь содержит:
             - "last_digits" (str): последние 4 цифры номера карты;
             - "total_spent" (float): общая сумма трат (модуль);
             - "cashback" (float): начисленный кэшбэк (1% от total_spent).
    :rtype: List[Dict[str, object]]
    """
    cards = []
    group = df.groupby("Номер карты").agg({'Сумма платежа': 'sum'})
    cards_dict = group.to_dict(orient='index')
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


def get_top_transactions(df: DataFrame, count: int = 5) -> list[dict]:
    """
    Возвращает список словарей с топ транзакциями с наибольшей суммой платежа по убыванию
    :param df: DataFrame с транзакциями. Должен содержать столбцы:
               - "Сумма платежа" (float/int): сумма транзакции (отрицательная — расход);
               - "Дата платежа" (datetime): дата операции;
               - "Категория" (str): категория траты;
               - "Описание" (str): описание транзакции.
    :param count: Количество транзакций для возврата (по умолчанию 5).
    :type count: int
    :return: Список словарей с информацией о транзакциях, отсортированных по сумме.
             Каждый словарь содержит:
             - "date" (datetime): дата платежа;
             - "amount" (float): сумма платежа (по модулю);
             - "category" (str): категория;
             - "description" (str): описание.
    """
    top_list = []
    df_sorted = df.sort_values(by='Сумма платежа', ascending=True)
    top = df_sorted.head(count)
    top_transaction = top.to_dict(orient='records')
    for trancas in top_transaction:
        date = trancas['Дата платежа']
        amount = abs(trancas['Сумма платежа'])
        category = trancas['Категория']
        description = trancas['Описание']
        transaction = {
            "date": date,
            "amount": amount,
            "category": category,
            "description": description
        }
        top_list.append(transaction)
    return top_list

# Пример использования функций
# if __name__ == "__main__":
#     transactions = read_transactions_from_excel('../data/operations.xlsx')
#     df = filter_transactions(transactions)
#     print(get_top_transactions(df))
# print(transactions)
# print(get_card_summary(df))
# print(get_greeting('2025-07-24 15:00:00'))
# print(get_conversion_rate('USD', 'RUB', '1'))
# print(get_currency_rates(['USD', 'EUR']))
# print(get_stock_prices("GOOGL"))
# print(get_stock_rate_list(["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]))
