from pathlib import Path
import pandas as pd
from typing import List, Dict

from src.utils import read_transactions_from_excel

# Определяем корень проекта: два уровня выше текущего файла
BASEDIR = Path(__file__).resolve().parent.parent

# Путь к файлу относительно корня проекта
TRANSACTIONS_FILE = BASEDIR / "data" / "operations.xlsx"


def analyze_cashback_by_category(
    data: List[Dict],
    year: int,
    month: int
) -> List[Dict]:
    """
    Анализирует кэшбэк по категориям за указанный месяц и год.

    Фильтрует транзакции по дате (только указанный год и месяц),
    суммирует значения из столбца «Кэшбэк» по каждой категории,
    игнорируя пустые или некорректные значения.

    :param data: Список транзакций. Каждый словарь должен содержать:
                 - «Дата платежа» (str или datetime);
                 - «Категория» (str);
                 - «Кэшбэк» (float, int или None).
    :param year: Год анализа (от 2018 до 2021 включительно).
    :param month: Месяц анализа (1–12).
    :return: Список словарей с полями «Категория» и «Кэшбэк», отсортированный по убыванию кэшбэка.
    :raises ValueError: Если год или месяц вне диапазона.
    """
    if not 2018 <= year <= 2021:
        raise ValueError("Год должен быть в диапазоне с 2018 по 2021")
    if not 1 <= month <= 12:
        raise ValueError("Месяц должен быть от 1 до 12")

    # Преобразуем список в DataFrame
    df = pd.DataFrame(data)

    # Преобразуем столбец "Дата платежа" в дату
    df["Дата платежа"] = pd.to_datetime(df["Дата платежа"], dayfirst=True, errors="coerce")

    # Создаем маску фильтрации по году и месяцу
    mask = (df["Дата платежа"].dt.year == year) & (df["Дата платежа"].dt.month == month)
    filtered = df[mask].copy()

    # Обрабатываем столбец "Кэшбэк"
    filtered["Кэшбэк"] = pd.to_numeric(filtered["Кэшбэк"], errors="coerce")
    filtered = filtered.dropna(subset=["Кэшбэк"])
    filtered = filtered[filtered["Кэшбэк"] > 0]

    # Группируем по категории и считаем сумму
    cashback_summary = (
        filtered.groupby("Категория")["Кэшбэк"]
        .sum()
        .round(2)
        .sort_values(ascending=False)
    )

    # Формируем итоговый список
    result_list = [
        {"Категория": category, "Кэшбэк": float(value)}
        for category, value in cashback_summary.items()
    ]

    return result_list


if __name__ == "__main__":
    # Читаем данные, передавая путь как строку
    data = read_transactions_from_excel(str(TRANSACTIONS_FILE))
    # Анализ данных за январь 2021 (пример)
    try:
        result = analyze_cashback_by_category(data, year=2021, month=1)
        print(result)
    except ValueError as e:
        print(f"Ошибка: {e}")
