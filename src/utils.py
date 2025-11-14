import os
import requests
import datetime
import pandas as pd
from typing import Optional
import logging
from dotenv import load_dotenv
from pathlib import Path

from pandas import DataFrame

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASEDIR = Path(__file__).resolve().parent.parent

# API URL для получения курсов валют (или для конвертации)
CURRENCY_API_URL = "https://api.apilayer.com/exchangerates_data/latest"
# URL для конвертации валют
CONVERT_API_URL = "https://api.apilayer.com/exchangerates_data/convert"


def get_greeting(dt_str: str) -> str:
    """
    Принимает строку даты (%Y-%m-%d %H:%M:%S)
    и в зависимости от времени суток передает приветствие
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
    Считывает транзакции из Excel-файла и
    возвращает их в виде списка словарей.

    Функция загружает данные с первого листа файла,
     преобразует каждую строку
    в словарь, где ключи — названия столбцов
    (например, «Дата платежа», «Сумма платежа» и т.д.).

    :param excel_path: Путь к Excel-файлу (формат .xlsx или .xls).
    :raises FileNotFoundError:
    Если файл по указанному пути не найден.
    :raises Exception:
    Если произошла ошибка при чтении файла (некорректный формат и т.п.).
    """
    try:
            df = pd.read_excel(excel_path)
            transactions = df.to_dict(orient='records')
            logger.info(f"Успешно загружено {len(transactions)} транзакций из {excel_path}")
            return transactions
    except FileNotFoundError:
            logger.error(f"Файл не найден: {excel_path}")
            return []
    except Exception as e:
            logger.error(f"Ошибка при чтении Excel-файла: {e}")
            return []


def get_conversion_rate(from_currency: str,
                        to_currency: str,
                        amount: str) -> Optional[float]:
    """
    Получает стоимость валюты
    :param from_currency: конвертируемая валюта
    :param to_currency: результат конвертации
    :param amount: сумма конвертируемой валюты
    :return: результат конвертации
    """
    load_dotenv(BASEDIR / '.env')
    apikey = os.getenv('API_TOKEN_STOCKS')
    url = (f"{CONVERT_API_URL}"
           f"?from={from_currency}"
           f"&to={to_currency}&amount={amount}")
    headers = {
        "apikey": apikey
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        rate = data.get("result")
        result = round(float(rate), 2)
        logger.info(f"Успешная конвертация: {amount} {from_currency} → {result} {to_currency}")
        return result
    else:
        logger.error(
            f"Ошибка при получении данных от API конвертации: "
            f"статус {response.status_code}, ответ: {response.text}")
        return None # ДОБАВЛЯЛА ЛОГИРОВАНИЕ ПРОВЕРЬ РАБОТУ


def get_currency_rates(curr_list: list[str]) -> list[dict]:
    """
    Получения курса валюта
    :param curr_list: список валют
    :return: результат словарь с курсом валют.
    """
    rates = []
    for curr in curr_list:
        rate = get_conversion_rate(
            from_currency=curr, to_currency='RUB', amount='1')
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
        logger.info(f"Получена цена акции {stock}: {result} USD")
        return result
    else:
        logger.error(
            f"Ошибка при получении данных о акции {stock}: "
            f"статус {response.status_code}, ответ: {response.text}")
        return None # ДОБАВЛЯЛА ЛОГИРОВАНИЕ ПРОВЕРЬ РАБОТУ
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
        (df["Сумма платежа"] < 0)
        & (~df["Категория"].isin(['Наличные', 'Переводы']))
        & (df["Категория"].notna())]
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
               - "Сумма платежа" (float/int): сумма операции.
    :type df: pandas.DataFrame
    :return: Список словарей с информацией по каждой карте.
    Каждый словарь содержит:
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
    Возвращает список словарей с топ транзакциями
     с наибольшей суммой платежа по убыванию
    :param df: DataFrame с транзакциями. Должен содержать столбцы:
               - "Сумма платежа" (float/int): сумма транзакции;
               - "Дата платежа" (datetime): дата операции;
               - "Категория" (str): категория траты;
               - "Описание" (str): описание транзакции.
    :param count: Количество транзакций для возврата (по умолчанию 5).
    :return: Список словарей с информацией о транзакциях,
     отсортированных по сумме.
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

# Пример использования функции read_transactions_from_excel
# if __name__ == "__main__":
#     transactions = read_transactions_from_excel('../data/operations.xlsx')
#     df = filter_transactions(transactions)

# Пример использования функции get_top_transactions
# if __name__ == "__main__":
#     transactions = read_transactions_from_excel('../data/operations.xlsx')
#     df = filter_transactions(transactions)
#     print(get_top_transactions(df))
#     print(transactions)

# Пример использования функции get_card_summary
# if __name__ == "__main__":
#     transactions = read_transactions_from_excel('../data/operations.xlsx')
#     df = filter_transactions(transactions)
#     print(get_card_summary(df))

# Пример использования функции get_greeting
# if __name__ == "__main__":
#     print(get_greeting('2025-07-24 15:00:00'))

# Пример использования функции get_conversion_rate
# if __name__ == "__main__":
#     print(get_conversion_rate('USD', 'RUB', '1'))

# Пример использования функции get_currency_rates
# if __name__ == "__main__":
#     print(get_currency_rates(['USD', 'EUR']))

# Пример использования функции get_stock_prices
# if __name__ == "__main__":
#     print(get_stock_prices("GOOGL"))

# Пример использования функции get_stock_rate_list
# if __name__ == "__main__":
#     print(get_stock_rate_list(["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]))
