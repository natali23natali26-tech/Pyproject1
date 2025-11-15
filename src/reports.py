import json
import logging
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from src.utils import read_transactions_from_excel

# Настройки путей
BASEDIR: Path = Path(__file__).resolve().parent.parent
TRANSACTIONS_FILE: Path = BASEDIR / "data" / "operations.xlsx"
DEFAULT_FILE: Path = BASEDIR / "reports" / "report_{date}.json"

# Логирование
logger: logging.Logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | "
                           "%(levelname)s | "
                           "%(message)s")


def save_report(func: Any) -> Any:
    """
    Декоратор: сохраняет результат функции в JSON-файл.

    Если не указан параметр `filename`, создаёт файл с временной меткой.
    Автоматически создаёт директорию, если её нет.
    Логирует успешное сохранение или ошибку.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> str:
        filename: Optional[Path] = kwargs.pop("filename", None)
        result: str = func(*args, **kwargs)

        if not filename:
            now: str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = (
                DEFAULT_FILE.with_name(DEFAULT_FILE.name.
                                       format(date=now)))

        filename.parent.mkdir(exist_ok=True)

        try:
            with open(filename, "w",
                      encoding="utf-8") as f:
                json.dump(json.loads(result), f,
                          ensure_ascii=False,
                          indent=2,
                          default=str)
            logger.info(f"Отчёт сохранён: {filename}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении: {e}")
            raise

        return result

    return wrapper


@save_report
def spending_by_category(
        transactions: pd.DataFrame,
        category: str,
        date: Optional[str] = None
) -> str:
    """
    Возвращает JSON-отчёт о тратах по указанной категории
     за последние 3 месяца.

    Поддерживает диагностику:
    - Категория не найдена → возвращает список доступных
    - Нет трат по категории → предупреждение
    - Нет данных в указанном периоде → подсказка с диапазоном дат

    Args:
        transactions: DataFrame с транзакциями. Должен содержать колонки:
                      «Дата операции», «Категория», «Сумма операции»
        category: Название категории (регистронезависимо)
        date: Дата в формате "ГГГГ-ММ-ДД".
        Если None — используется текущая дата.

    Returns:
        JSON-строка с полями:
        - category: запрошенная категория
        - period: период анализа (from/to)
        - total: сумма трат в рублях
        - spending: список операций (дата, сумма, описание)
        - warning: текст предупреждения (если есть)
        - available_categories: список всех категорий (если запрошенной нет)
        - hint: подсказка по диапазону дат (если нет данных за период)
    """
    if transactions.empty:
        return json.dumps({
            "category": category,
            "total": 0,
            "spending": [],
            "warning": "Пустой DataFrame"
        }, ensure_ascii=False, indent=2)

    # Настройка дат
    target: datetime = datetime.now() if not date \
        else datetime.strptime(date, "%Y-%m-%d")
    start: datetime = target - pd.DateOffset(months=3)

    # Подготовка данных
    df: pd.DataFrame = transactions.copy()
    df["Дата операции"] = (
        pd.to_datetime(df["Дата операции"],
                       format="%d.%m.%Y %H:%M:%S",
                       errors="coerce"))
    df["Категория"] = df["Категория"].astype(str).str.lower().str.strip()
    cat: str = category.strip().lower()

    # Получаем все существующие категории
    available_categories: List[str] = (
        df["Категория"].dropna().unique().tolist())

    # 1. Проверка: существует ли категория?
    if cat not in available_categories:
        logger.warning(f"Категория '{category}' не найдена в данных")
        result: Dict[str, Any] = {
            "category": category,
            "period": {"from": start.strftime("%Y-%m-%d"),
                       "to": target.strftime("%Y-%m-%d")},
            "total": 0,
            "spending": [],
            "warning": f"Категория '{category}' не найдена",
            "available_categories": sorted(available_categories)
        }
        return json.dumps(result, ensure_ascii=False, indent=2)

    # 2. Фильтрация: только траты в указанной категории
    category_mask: pd.Series = (
            (df["Категория"] == cat) &
            (df["Сумма операции"] < 0))
    filtered_by_category: pd.DataFrame = df[category_mask]

    if filtered_by_category.empty:
        logger.info(f"Категория '{category}' существует, но трат по ней нет")
        result = {
            "category": category,
            "period": {"from": start.strftime("%Y-%m-%d"),
                       "to": target.strftime("%Y-%m-%d")},
            "total": 0,
            "spending": [],
            "warning": f"Категория '{category}'"
                       f" существует, но трат по ней не найдено"
        }
        return json.dumps(result, ensure_ascii=False, indent=2)

    # 3. Фильтрация по дате
    date_mask: pd.Series = (
            (filtered_by_category["Дата операции"] >= start) &
            (filtered_by_category["Дата операции"] <= target)
    )
    filtered: pd.DataFrame = filtered_by_category[date_mask]

    if filtered.empty:
        logger.warning(
            f"Нет операций по категории '{category}' "
            f"в период с {start.strftime('%Y-%m-%d')} "
            f"по {target.strftime('%Y-%m-%d')}")
        result = {
            "category": category,
            "period": {"from": start.strftime("%Y-%m-%d"),
                       "to": target.strftime("%Y-%m-%d")},
            "total": 0,
            "spending": [],
            "warning": f"Нет операций по категории "
                       f"'{category}' в указанный период",
            "hint": f"Данные доступны с {df['Дата операции'].min().date()} "
                    f"по {df['Дата операции'].max().date()}"
        }
        return json.dumps(result, ensure_ascii=False, indent=2)

    # 4. Формирование результата
    spending: List[Dict[str, Any]] = [
        {
            "date":
                row["Дата операции"].strftime("%Y-%m-%d"),
            "amount":
                round(abs(row["Сумма операции"]), 2),
            "description":
                str(row.get("Описание", "")).strip()
        }
        for _, row in filtered.iterrows()
    ]

    total: float = round(sum(item["amount"] for item in spending), 2)

    result = {
        "category": category,
        "period": {"from": start.strftime("%Y-%m-%d"),
                   "to": target.strftime("%Y-%m-%d")},
        "total": total,
        "spending": spending
    }

    logger.info(f"Сформирован отчёт: {category} — {total} ₽")
    return json.dumps(result, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    if not TRANSACTIONS_FILE.exists():
        logger.error("Файл операций не найден: %s", TRANSACTIONS_FILE)
        exit(1)

    data = read_transactions_from_excel(str(TRANSACTIONS_FILE))
    if not data:
        logger.error("Не удалось загрузить данные из Excel")
        exit(1)

    df = pd.DataFrame(data)

    if "Категория" not in df.columns:
        logger.error("Отсутствует колонка 'Категория' в данных")
        exit(1)

    result = spending_by_category(
        transactions=df,
        category="Супермаркеты",
        date="2020-04-05"
    )
