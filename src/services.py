import math
from pathlib import Path
import json
from typing import Any, List, Dict
import pandas as pd
import re
import logging
from src.utils import read_transactions_from_excel, filter_transactions

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    Анализирует, сколько кэшбэка можно было бы
     получить по каждой категории за указанный месяц и год,
    если бы она была выбрана как категория повышенного кэшбэка.

    Кэшбэк рассчитывается как 1% от суммы расходов.
    Используются только реальные расходы (сумма < 0),
     исключая 'Наличные' и 'Переводы'.

    :param data: Список транзакций
    (словари с полями: «Дата платежа», «Категория», «Сумма платежа»)
    :param year: Год анализа (2018–2021)
    :param month: Месяц анализа (1–12)
    :return: JSON-строка: {"Категория 1": 1000.0, "Категория 2": 2000.0}
    :raises ValueError: Если год или месяц вне допустимого диапазона
    """
    logger.info(
        f"Анализ кешбэка по категориям:"
        f" {year}-{month:02d}, "
        f"количество транзакций: {len(data)}")

    # Проверка диапазона года
    if not 2018 <= year <= 2021:
        logger.error(f"Год вне диапазона: {year}")
        raise ValueError("Год должен быть в диапазоне с 2018 по 2021")

    # Проверка диапазона месяца
    if not 1 <= month <= 12:
        logger.error(f"Месяц вне диапазона: {month}")
        raise ValueError("Месяц должен быть от 1 до 12")

    # Проверка пустых данных
    if not data:
        logger.warning("Пустой список транзакций")
        return json.dumps({}, ensure_ascii=False, indent=2)

    try:
        # Преобразуем в DataFrame и фильтруем транзакции
        df = pd.DataFrame(data)
        filtered_df = filter_transactions(
            df.to_dict("records"))  # возвращает DataFrame

        # Преобразуем дату и фильтруем по году и месяцу
        filtered_df["Дата платежа"] = pd.to_datetime(
            filtered_df["Дата платежа"], dayfirst=True, errors="coerce")
        mask = (filtered_df["Дата платежа"].dt.year == year) & (
            filtered_df["Дата платежа"].dt.month == month)
        df_period = filtered_df[mask].copy()

        if df_period.empty:
            logger.info(f"Нет подходящих транзакций за {year}-{month:02d}")
            return json.dumps({}, ensure_ascii=False, indent=2)

        # Рассчитываем кэшбэк: 1% от модуля суммы
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

        logger.info(f"Расчёт завершён. Найдено категорий: {len(result)}")
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Ошибка при обработке транзакций: {e}")
        return json.dumps({},
                          ensure_ascii=False, indent=2)


def investment_bank(month: str,
                    transactions: List[Dict[str, Any]],
                    limit: Any) -> str:
    """
    Рассчитывает сумму, отложенную в «Инвесткопилку»
     за счёт округления трат до заданного порога.

    :param month: Месяц в формате 'YYYY-MM',
     за который рассчитывается накопление.
    :param transactions: Список словарей с транзакциями.
        Каждая транзакция содержит:
        - 'Дата операции': str, формат 'DD.MM.YYYY HH:MM:SS'
        - 'Сумма операции': float или int (отрицательные значения — траты)
        - 'Категория': str
    :param limit: Порог округления — 10, 50 или 100 рублей
     (может быть int или float).
    :return: JSON-строка в формате {"total_savings": X.XX}
    """
    # Логируем начало и тип limit для отладки
    logger.info(
        f"Расчёт Инвесткопилки для месяца:"
        f" {month}, лимит: {limit} "
        f"(тип: {type(limit)})")

    # Приводим limit к целому числу, если возможно
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        logger.error(
            f"Некорректный лимит (не число): {limit}, тип: {type(limit)}")
        return json.dumps({"total_savings": 0.0}, ensure_ascii=False, indent=2)

    # Проверка лимита и транзакций
    if not transactions:
        logger.warning("Пустые транзакции")
        return json.dumps({"total_savings": 0.0}, ensure_ascii=False, indent=2)

    if limit not in {10, 50, 100}:
        logger.warning(f"Некорректный лимит: {limit}")
        return json.dumps({"total_savings": 0.0}, ensure_ascii=False, indent=2)

    # Проверка формата месяца
    try:
        year, month_num = map(int, month.split('-'))
        if not (2018 <= year <= 2021) or not (1 <= month_num <= 12):
            logger.warning(f"Месяц "
                           f"вне диапазона:"
                           f" {month}")
            return json.dumps({"total_savings": 0.0},
                              ensure_ascii=False, indent=2)
    except (ValueError, TypeError):
        logger.error(f"Некорректный формат месяца: {month}")
        return json.dumps({"total_savings": 0.0},
                          ensure_ascii=False, indent=2)

    # Фильтруем транзакции: только траты, без 'Наличные' и 'Переводы'
    try:
        df_filtered = (
            filter_transactions(transactions))
        if df_filtered.empty:
            logger.info("Нет подходящих транзакций после фильтрации")
            return json.dumps({"total_savings": 0.0},
                              ensure_ascii=False,
                              indent=2)
    except Exception as e:
        logger.error(f"Ошибка при фильтрации транзакций: {e}")
        return json.dumps({"total_savings": 0.0},
                          ensure_ascii=False,
                          indent=2)

    # Преобразуем дату
    try:
        df_filtered['Дата операции'] = pd.to_datetime(
            df_filtered['Дата операции'],
            format='%d.%m.%Y %H:%M:%S',
            errors='coerce'
        )
        df_filtered['month'] = df_filtered['Дата операции'].dt.strftime(
            '%Y-%m')
    except Exception as e:
        logger.error(f"Ошибка при парсинге дат: {e}")
        return json.dumps({"total_savings": 0.0}, ensure_ascii=False, indent=2)

    # Фильтр по месяцу
    df_month = df_filtered[df_filtered['month'] == month]
    if df_month.empty:
        logger.info(f"Нет транзакций за месяц {month}")
        return json.dumps({"total_savings": 0.0}, ensure_ascii=False, indent=2)

    # Считаем сбережения
    total_savings = 0.0
    amounts = df_month['Сумма операции'].abs()
    for amount in amounts:
        if amount > 0:
            rounded_up = math.ceil(amount / limit) * limit
            total_savings += rounded_up - amount

    total_savings = round(total_savings, 2)
    logger.info(f"Инвесткопилка за {month}: {total_savings} руб.")

    # Возвращаем JSON
    return json.dumps({"total_savings": total_savings},
                      ensure_ascii=False, indent=2)


def search_person_transfers() -> str:
    """
    Ищет транзакции, относящиеся к переводам физическим лицам.

    Условия:
      - Категория: «Переводы»
      - В описании:
      имя
      + пробел
      + заглавная буква кириллицы
      + точка (например: «Валерий А.»)

    Обрабатывает пустые значения, None, NaN.
    Возвращает результат в формате JSON.

    :return: JSON-строка со списком транзакций.
    """
    # Загружаем транзакции
    try:
        transactions: list[dict[str, Any]] = read_transactions_from_excel(
            str(TRANSACTIONS_FILE))
        logger.info(f"Загружено {len(transactions)} транзакций из Excel.")
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных: {e}")
        return json.dumps([], ensure_ascii=False, indent=2)

    # Паттерн: имя (кириллица) + пробел + заглавная буква + точка
    pattern = re.compile(r"^[А-ЯЁ][а-яё]+\s[А-ЯЁ]\.$")

    result: list[dict[str, Any]] = []

    for transaction in transactions:
        # Извлекаем поля
        raw_category = transaction.get("Категория", "")
        raw_description = transaction.get("Описание", "")

        # Приводим к строке и очищаем
        try:
            category = str(raw_category).strip(
            ) if raw_category is not None else ""
        except (TypeError, AttributeError):
            category = ""

        try:
            description = str(raw_description).strip(
            ) if raw_description is not None else ""
        except (TypeError, AttributeError):
            description = ""

        # Исключаем пустые или некорректные значения
        if not category or not description:
            continue

        # Проверяем на 'nan', 'none'
        # и пустоту после преобразования
        if (category.lower() in ("nan", "none", "") or
                description.lower() in ("nan", "none", "")):
            continue

        # Проверяем критерии
        if category == "Переводы" and pattern.search(description):
            result.append(transaction)

    logger.info(f"Найдено {len(result)} переводов физическим лицам.")
    return json.dumps(result, ensure_ascii=False, indent=2)


# # Пример использования analyze_cashback_by_category
# if __name__ == "__main__":
#     data = read_transactions_from_excel(str(TRANSACTIONS_FILE))
#     result = analyze_cashback_by_category(data, year=2020, month=5)
#     print(result)

# Пример использования investment_bank
# if __name__ == "__main__":
#     transactions = (
#         read_transactions_from_excel(str(TRANSACTIONS_FILE)))
#     result = investment_bank(month="2021-03",
#                              transactions=transactions,
#                              limit=50)
#     print(f"Сумма в Инвесткопилке: {result} ₽")

# Пример использования find_person_transfers
# if __name__ == "__main__":
#     print(search_person_transfers())

# Пример использования search_person_transfers
# if __name__ == "__main__":
#     result_json = search_person_transfers()
#     print(result_json)

