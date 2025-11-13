import pandas as pd
import json
import datetime
from functools import wraps
import logging
from typing import Optional

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler('reports.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# Декоратор без параметров: сохраняет в файл с названием по умолчанию
def report_to_file_default(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        filename = f"{func.__name__}_report.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
            logger.info(f"Отчет сохранен в файл {filename}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении файла {filename}: {e}")
        return result
    return wrapper


# Декоратор с параметром: принимает имя файла
def report_to_file(filename):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=4)
                logger.info(f"Отчет сохранен в файл {filename}")
            except Exception as e:
                logger.error(f"Ошибка при сохранении файла {filename}: {e}")
            return result
        return wrapper
    return decorator


@report_to_file_default
def spending_by_category(
    transactions: pd.DataFrame,
    category: str,
    date: Optional[str] = None
) -> pd.DataFrame:
    """
    Возвращает траты по заданной категории
     за последние 3 месяца от указанной даты.
    Если дата не передана, используется текущая дата.
    """
    # Если дата не указана, берем текущую
    if date is None:
        end_date_dt = datetime.datetime.now()
    else:
        end_date_dt = datetime.datetime.strptime(date, "%Y-%m-%d")
    # Расчет начальной даты — три месяца назад
    start_date_dt = end_date_dt - datetime.timedelta(days=90)

    # Фильтрация по дате и категории
    # Предполагается, что в транзакциях
    # есть колонка 'date' в формате "%Y-%m-%d"
    mask_date = (transactions['date']
                 >= start_date_dt.strftime("%Y-%m-%d")) & \
                (transactions['date']
                 <= end_date_dt.strftime("%Y-%m-%d"))
    mask_category = transactions['category'] == category
    filtered = transactions[mask_date & mask_category]

    # Можно сгруппировать и посчитать сумму, если нужно.
    # Но по ТЗ функция возвращает DataFrame
    # с транзакциями по категории за период
    return filtered
