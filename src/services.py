import math
from pathlib import Path
import json
from typing import Any

import pandas as pd

from src.utils import read_transactions_from_excel, filter_transactions

# Определяем корень проекта: два уровня выше текущего файла
BASEDIR = Path(__file__).resolve().parent.parent

# Путь к файлу относительно корня проекта
TRANSACTIONS_FILE = BASEDIR / "data" / "operations.xlsx"


def analyze_cashback_by_category(
        data: list[dict],
        year: int,
        month: int
) -> str:
    """
    Анализирует, сколько кэшбэка можно было бы получить по каждой категории за указанный месяц и год,
    если бы она была выбрана как категория повышенного кэшбэка.

    Кэшбэк рассчитывается как 1% от суммы расходов (по аналогии с get_card_summary).
    Используются только реальные расходы (сумма < 0), исключая 'Наличные' и 'Переводы'.

    :param data: Список транзакций (словари с полями: «Дата платежа», «Категория», «Сумма платежа»)
    :param year: Год анализа (2018–2021)
    :param month: Месяц анализа (1–12)
    :return: JSON-строка: {"Категория 1": 1000.0, "Категория 2": 2000.0}
    :raises ValueError: Если год или месяц вне допустимого диапазона
    """
    if not 2018 <= year <= 2021:
        raise ValueError("Год должен быть в диапазоне с 2018 по 2021")

    if not 1 <= month <= 12:
        raise ValueError("Месяц должен быть от 1 до 12")

    if not data:
        return json.dumps({}, ensure_ascii=False, indent=2)

        # Преобразуем в DataFrame и фильтруем транзакции (используем внешнюю функцию)
    df = pd.DataFrame(data)
    filtered_df = filter_transactions(df.to_dict("records"))  # возвращает DataFrame

    # Преобразуем дату и фильтруем по году и месяцу
    filtered_df["Дата платежа"] = pd.to_datetime(filtered_df["Дата платежа"], dayfirst=True, errors="coerce")
    mask = (filtered_df["Дата платежа"].dt.year == year) & (filtered_df["Дата платежа"].dt.month == month)
    df_period = filtered_df[mask].copy()

    if df_period.empty:
        return json.dumps({}, ensure_ascii=False, indent=2)

    # Рассчитываем кэшбэк: 1% от модуля суммы платежа (как в get_card_summary)
    df_period["Кэшбэк"] = df_period["Сумма платежа"].abs() * 0.01

    # Группируем по категории
    cashback_by_category = (
        df_period.groupby("Категория")["Кэшбэк"]
        .sum()
        .round(2)
        .sort_values(ascending=False)
        .to_dict()
    )

    # Преобразуем numpy типы в стандартные Python
    result = {cat: float(val) for cat, val in cashback_by_category.items()}

    return json.dumps(result, ensure_ascii=False, indent=2)


def investment_bank(month: str, transactions: list[dict[str, Any]], limit: int) -> float:
    """
    Рассчитывает сумму, отложенную в «Инвесткопилку» за счёт округления трат до заданного порога.

    :param month: Месяц в формате 'YYYY-MM', за который рассчитывается накопление.
    :param transactions: Список словарей с транзакциями.
        Каждая транзакция содержит:
        - 'Дата операции': str, формат 'DD.MM.YYYY HH:MM:SS'
        - 'Сумма операции': float или int (отрицательные значения — траты)
        - 'Категория': str
    :param limit: Порог округления — 10, 50 или 100 рублей.
    :return: Сумма, отложенная в «Инвесткопилку» за месяц (округлённая до 2 знаков).
    """
    # Проверка входных данных
    if not transactions or limit not in {10, 50, 100}:
        return 0.0

    # Проверка формата и диапазона месяца: год 2018–2021, месяц 1–12
    try:
        year, month_num = map(int, month.split('-'))
        if not (2018 <= year <= 2021) or not (1 <= month_num <= 12):
            return 0.0
    except (ValueError, TypeError):
        return 0.0

    # Фильтруем транзакции: только траты, без 'Наличные' и 'Переводы'
    df_filtered = filter_transactions(transactions)

    # Преобразуем дату: формат '31.12.2021 16:44:00'
    df_filtered['Дата операции'] = pd.to_datetime(
        df_filtered['Дата операции'],
        format='%d.%m.%Y %H:%M:%S',
        errors='coerce'
    )
    df_filtered['month'] = df_filtered['Дата операции'].dt.strftime('%Y-%m')

    # Фильтр по нужному месяцу
    df_month = df_filtered[df_filtered['month'] == month]
    if df_month.empty:
        return 0.0

    # Используем 'Сумма операции' (по ТЗ), берём абсолютные значения трат
    amounts = df_month['Сумма операции'].abs()

    # Считаем сбережения: округление вверх до ближайшего кратного limit
    total_savings = 0.0
    for amount in amounts:
        if amount > 0:
            rounded_up = math.ceil(amount / limit) * limit
            total_savings += rounded_up - amount

    return round(total_savings, 2)




# Пример использования analyze_cashback_by_category
# if __name__ == "__main__":
#     data = read_transactions_from_excel(str(TRANSACTIONS_FILE))
#     result = analyze_cashback_by_category(data, year=2020, month=5)
#     print(result)

# Пример использования investment_bank
# if __name__ == "__main__":
#     transactions = read_transactions_from_excel(str(TRANSACTIONS_FILE))
#     result = investment_bank(month="2024-03", transactions=transactions, limit=50)
#     print(f"Сумма в Инвесткопилке: {result} ₽")
