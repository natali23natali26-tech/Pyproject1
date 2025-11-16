import json
import logging
from pathlib import Path


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ОПРЕДЕЛЯЕМ КОРЕНЬ ПРОЕКТА
BASEDIR = Path(__file__).resolve().parent

# ПУТИ
TRANSACTIONS_FILE = BASEDIR / "data" / "operations.xlsx"

# ИМПОРТ МОДУЛЕЙ (после определения BASEDIR)
try:
    from src.views import this_home
    from src.services import (
        analyze_cashback_by_category,
        investment_bank,
        search_person_transfers
    )
    from src.reports import spending_by_category
    from src.utils import read_transactions_from_excel, filter_transactions
    logger.info("Модули успешно импортированы")
except Exception as e:
    logger.critical(f"Ошибка импорта: {e}")
    exit(1)


def main():
    logger.info("Запуск главного скрипта...")

    if not TRANSACTIONS_FILE.exists():
        logger.error(f"Файл не найден: {TRANSACTIONS_FILE}")
        logger.error("Убедитесь, что папка 'data' с файлом 'operations.xlsx' "
                     "находится в корне проекта.")
        return  # ← выход только при ошибке

    # Если файл есть — продолжаем
    logger.info(f"Файл найден: {TRANSACTIONS_FILE}")

    # Загружаем транзакции
    transactions = read_transactions_from_excel(str(TRANSACTIONS_FILE))
    if not transactions:
        logger.error("Не удалось загрузить транзакции из файла")
        return

    logger.info(f"Загружено {len(transactions)} транзакций")

    # === 1. Главная страница ===
    logger.info("Генерация главной страницы...")
    try:
        home_data = this_home()
        print("\n" + "="*50)
        print("ГЛАВНАЯ СТРАНИЦА")
        print("="*50)
        print(json.dumps(home_data, ensure_ascii=False, indent=2))
    except Exception as e:
        logger.error(f"Ошибка при генерации главной страницы: {e}")

    # === 2. Кэшбэк по категориям ===
    logger.info("Анализ кэшбэка по категориям...")
    try:
        cashback_result = analyze_cashback_by_category(transactions, 2021, 5)
        print("\n" + "="*50)
        print("КЭШБЭК ПО КАТЕГОРИЯМ (Май 2021)")
        print("="*50)
        print(cashback_result)
    except Exception as e:
        logger.error(f"Ошибка анализа кэшбэка: {e}")

    # === 3. Инвесткопилка ===
    logger.info("Расчёт Инвесткопилки...")
    try:
        savings_result = investment_bank("2021-05", transactions, 100)
        print("\n" + "="*50)
        print("ИНВЕСТКОПИЛКА (2021-05, лимит 100 руб)")
        print("="*50)
        print(savings_result)
    except Exception as e:
        logger.error(f"Ошибка расчёта инвесткопилки: {e}")

    # === 4. Переводы физлицам ===
    logger.info("Поиск переводов физическим лицам...")
    try:
        transfers_result = search_person_transfers()
        print("\n" + "="*50)
        print("ПЕРЕВОДЫ ФИЗЛИЦАМ")
        print("="*50)
        print(transfers_result)
    except Exception as e:
        logger.error(f"Ошибка поиска переводов: {e}")

    # === 5. Отчёт по категории ===
    logger.info("Генерация отчёта по категории 'Супермаркеты'...")
    try:
        df = filter_transactions(transactions)
        report_result = spending_by_category(df, "Супермаркеты", "2021-05-10")
        print("\n" + "="*50)
        print("ОТЧЁТ: ТРАТЫ В СУПЕРМАРКЕТАХ")
        print("="*50)
        print(report_result)
    except Exception as e:
        logger.error(f"Ошибка генерации отчёта: {e}")

    logger.info("Все модули успешно выполнены!")



if __name__ == "__main__":
    main()
