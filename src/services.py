import json
import datetime
import logging
from typing import List, Dict, Any

# Включим логирование
logger = logging.getLogger(__name__)


def analyze_profitable_categories(data: List[Dict[str, Any]], year: int, month: int) -> str:
    from functools import reduce
    # Фильтруем транзакции по году и месяцу
    def is_in_month(tx):
        tx_date = datetime.datetime.strptime(tx["date"], "%Y-%m-%d")
        return tx_date.year == year and tx_date.month == month

    filtered = list(filter(is_in_month, data))

    # Группируем по категориям и считаем сумму кешбэка
    def reducer(acc, tx):
        category = tx.get("category", "Не определена")
        amount = tx.get("amount", 0)
        # Кешбэк 1% от суммы
        cashback = abs(amount) * 0.01
        acc[category] = acc.get(category, 0) + cashback
        return acc

    result_dict = reduce(reducer, filtered, {})

    # Возращаем JSON
    json_result = json.dumps(result_dict, ensure_ascii=False)
    logger.info("Анализ выгодных категорий завершен")
    return json_result


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> float:
    """
    Расчет суммы, которая может быть отложена в "Инвесткопилку", на основе округлений покупок.

    :param month: строка формата 'YYYY-MM'
    :param transactions: список транзакций с полями 'date' и 'amount'
    :param limit: порог округления
    :return: сумма, которая может быть отложена
    """
    from functools import reduce

    # Парсим месяц
    target_year, target_month = map(int, month.split('-'))

    # Фильтруем транзакции по месяцу
    filtered_tx = list(filter(lambda tx:
                              datetime.datetime.strptime(tx['date'], "%Y-%m-%d").year == target_year and
                              datetime.datetime.strptime(tx['date'], "%Y-%m-%d").month == target_month,
                              transactions
                              ))

    def accumulate_rounding(total, tx):
        amount = abs(tx['amount'])
        # Округляем сумму
        rounded = ((amount + limit - 1) // limit) * limit
        difference = rounded - amount
        return total + difference

    total_savings = reduce(accumulate_rounding, filtered_tx, 0.0)
    # Округляем до 2 знаков
    total_savings = round(total_savings, 2)
    logging.info(f"В копилку за {month} удалось собрать {total_savings} ₽")
    return total_savings

if __name__ == "__main__":
    # Пример для проверки analyze_profitable_categories
    data = [
        {"date": "2023-08-05", "amount": 1000, "category": "Развлечения"},
        {"date": "2023-08-15", "amount": 2000, "category": "Гаджеты"},
        {"date": "2023-07-20", "amount": 1500, "category": "Путешествия"},
        {"date": "2023-08-10", "amount": 3000, "category": "Развлечения"}
    ]
    print(analyze_profitable_categories(data, 2023, 8))
    # Проверка investment_bank
    transactions = [
        {"date": "2023-08-01", "amount": 1712},
        {"date": "2023-08-10", "amount": 500},
        {"date": "2023-08-15", "amount": 1050}
    ]
    print(investment_bank("2023-08", transactions, 50))
