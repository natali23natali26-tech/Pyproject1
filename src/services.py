import json
import datetime
from typing import List, Dict, Any
from itertools import groupby
from collections import defaultdict
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def analyze_profitable_categories(data: pd.DataFrame, year: int, month: int) -> str:
    """
    Анализирует наиболее выгодные категории кешбэка за указанный месяц и год.
    Возвращает JSON строку с суммами по категориям.
    """

    # Преобразует значение 'date' из строки в объект datetime.
    # Проверяет, относится ли эта дата к указанному году (year) и месяцу (month).
    # Возвращает True, если дата в нужном месяце, иначе — False.
    # Чтобы фильтровать только те транзакции, которые произошли именно в выбранном месяце.
    def is_in_month(row):
        date = pd.to_datetime(row['date'])
        return date.year == year and date.month == month

    # Создание отфильтрованных данных
    filtered_data = list(
        map(lambda row: row, filter(is_in_month, data.itertuples(index=False)))
    )

    # Исключить переводы и категории в иностранных валютах
    # Предположим, что переводы по категории 'Перевод' или похожие не влучают
    def is_valid_category(row):
        categoria = getattr(row, 'category', '')
        currency = getattr(row, 'currency', 'RUB')
        return (
                categoria.lower() != 'перевод' and
                currency in ['RUB', 'EUR', 'TRY']
        )

    valid_transactions = list(filter(is_valid_category, filtered_data))

    # Группировка по категориям и подсчет суммы кешбэка
    #Создаем словарь category_bonuses, где ключ — категория, значение — сумма кешбэка за все транзакции в этой категории.
    # Для каждой транзакции: извлекаем сумму кешбэка (cashback), если нет — по умолчанию 0;
    # извлекаем название категории (category), если нет — "Неизвестная";
    # добавляем кешбэк в сумму по этой категории.
    category_bonuses = defaultdict(float)

    for row in valid_transactions:
        cashback = getattr(row, 'cashback', 0)
        category = getattr(row, 'category', 'Неизвестная')
        category_bonuses[category] += cashback

    # словарь из подсчитанных сумм по категориям
    result_json = json.dumps({k: v for k, v in category_bonuses.items()}, ensure_ascii=False)
    return result_json


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> float:
    """
    Рассчитывает сумму, которую можно отложить в инвестиционный фонд, округляя операции до лимита.
    """
    # Преобразуем месяц в год и месяц
    year_month = datetime.datetime.strptime(month, "%Y-%m")
    year = year_month.year
    month_num = year_month.month

    # Фильтр транзакций на месяц и валидных условий
    def is_in_month(transaction):
        t_date_str = transaction.get('Дата операции')
        try:
            t_date = datetime.datetime.strptime(t_date_str, "%Y-%m-%d")
        except Exception as e:
            logger.warning(f"Некорректная дата: {t_date_str} — {e}")
            return False
        return t_date.year == year and t_date.month == month_num and transaction.get('Статус') == 'OK'

    month_transactions = list(filter(is_in_month, transactions))

    # Вычисление округленной суммы и накопленной разницы
    def transaction_rounding(trans):
        amount = trans.get('Сумма операции', 0)
        # Округляем сумму до ближайшего лимита
        rounded = int(round(amount / limit) * limit)
        difference = rounded - amount
        return max(difference, 0)  # только отрицательные значения (деньги в копилке)

    # Используя map для получения разниц
    total_savings = sum(
        map(lambda t: transaction_rounding(t), month_transactions)
    )

    return total_savings
