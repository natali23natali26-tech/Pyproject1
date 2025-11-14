import pytest
from unittest.mock import patch
import json
import pandas as pd
from src.services import (
    analyze_cashback_by_category,
    investment_bank,
    search_person_transfers
)

# ———————————————————————
# ФИКСТУРЫ
# ———————————————————————


@pytest.fixture
def sample_transactions():
    """Пример транзакций для тестов."""
    return [
        {"Дата платежа": "05.01.2021 10:00:00",
         "Категория": "Супермаркеты", "Сумма платежа": -123.45},
        {"Дата платежа": "06.01.2021 11:00:00",
         "Категория": "Кафе", "Сумма платежа": -278.10},
        {"Дата платежа": "07.01.2021 12:00:00",
         "Категория": "Наличные", "Сумма платежа": -1000.00},
        {"Дата платежа": "08.01.2021 13:00:00",
         "Категория": "Переводы", "Сумма платежа": -500.00},
        {"Дата платежа": "05.02.2021 14:00:00",
         "Категория": "Супермаркеты", "Сумма платежа": -99.99},
        {"Дата платежа": "10.01.2021 09:00:00",
         "Категория": "Кафе", "Сумма платежа": -85.50},
    ]


@pytest.fixture
def sample_investment_transactions():
    """Транзакции для теста investment_bank."""
    return [{"Дата операции": "05.01.2021 10:00:00",
             "Сумма операции": -123.45,
             "Категория": "Супермаркеты"},
            {"Дата операции": "06.01.2021 11:00:00",
             "Сумма операции": -278.10,
             "Категория": "Кафе"},
            {"Дата операции": "07.01.2021 12:00:00",
             "Сумма операции": -99.99,
             "Категория": "Одежда"},
            {"Дата операции": "15.02.2021 14:00:00",
             "Сумма операции": -50.01,
             "Категория": "Кафе"},
            ]


@pytest.fixture
def mock_excel_data():
    """Мок-данные из operations.xlsx."""
    return [
        {"Категория": "Переводы", "Описание":
            "Валерий А.", "Сумма операции": -500.0},
        {"Категория": "Переводы", "Описание":
            "Анна Б.", "Сумма операции": -300.0},
        {"Категория": "Переводы", "Описание":
            "Оплата по QR", "Сумма операции": -200.0},
        {"Категория": "Супермаркеты", "Описание":
            "Валерий А.", "Сумма операции": -100.0},
        {"Категория": "Переводы", "Описание":
            "Иван И.", "Сумма операции": -400.0},
        {"Категория": None, "Описание":
            "Петр П.", "Сумма операции": -250.0},
        {"Категория": "nan", "Описание":
            "Мария М.", "Сумма операции": -150.0},
        {"Категория": "Переводы", "Описание":
            None, "Сумма операции": -100.0},
    ]


# ———————————————————————
# ТЕСТЫ: analyze_cashback_by_category
# ———————————————————————

@pytest.mark.parametrize("year,month,expected", [
    # 123.45 + 85.50 = 208.95 → 2.09, но 278.10 → 2.78 → Кафе = 2.78 + 0.86 =
    # 3.64
    (2021, 1, {"Супермаркеты": 1.23, "Кафе": 3.64}),
    (2021, 2, {"Супермаркеты": 1.00}),
    (2020, 1, {}),
])
def test_analyze_cashback_parametrized(
        sample_transactions, year, month, expected):
    """Параметризированный тест: правильный расчёт кэшбэка."""
    with patch("src.utils.filter_transactions") as mock_filter:
        # Фильтруем вручную
        filtered = [
            t for t in sample_transactions if f"{
                month:02d}.{year}" in t["Дата платежа"]]
        mock_filter.return_value = pd.DataFrame(filtered)

        result = json.loads(
            analyze_cashback_by_category(
                sample_transactions, year, month))
        rounded_result = {k: round(v, 2) for k, v in result.items()}
        rounded_expected = {k: round(v, 2) for k, v in expected.items()}

        assert rounded_result == rounded_expected


def test_analyze_cashback_invalid_month(sample_transactions):
    """Тест: выбрасывает ValueError при некорректном месяце."""
    with pytest.raises(ValueError, match="Месяц должен быть от 1 до 12"):
        analyze_cashback_by_category(sample_transactions, 2021, 15)


def test_analyze_cashback_empty_data():
    """Тест: пустые данные → пустой JSON."""
    result = analyze_cashback_by_category([], 2021, 1)
    assert json.loads(result) == {}


def test_analyze_cashback_no_transactions_in_period(sample_transactions):
    """Тест: нет транзакций в указанном месяце."""
    with patch("src.services.filter_transactions") as mock_filter:
        mock_filter.return_value = pd.DataFrame()
        result = analyze_cashback_by_category(sample_transactions, 2021, 1)
        assert json.loads(result) == {}


def test_analyze_cashback_date_parsing_error():
    """Тест: ошибка при парсинге даты → возвращает пустой JSON."""
    data = [{"Дата платежа": "некорректная_дата",
             "Категория": "Супермаркеты", "Сумма платежа": -100.0}]
    with patch("src.services.filter_transactions") as mock_filter:
        mock_filter.return_value = pd.DataFrame(data)
        result = json.loads(analyze_cashback_by_category(data, 2021, 1))
        assert result == {}

# ВЫДАЕТ ОШИБКУ


def test_analyze_cashback_empty_category_after_filter():
    """Тест: после фильтрации не остаётся подходящих категорий."""
    data = [{"Дата платежа": "05.01.2021",
             "Категория": "Наличные",
             "Сумма платежа": -100.0},
            {"Дата платежа": "06.01.2021",
             "Категория": "Переводы",
             "Сумма платежа": -200.0},
            ]
    with patch("src.services.filter_transactions") as mock_filter:
        mock_filter.return_value = pd.DataFrame()  # ← фильтрация удалила всё
        result = json.loads(analyze_cashback_by_category(data, 2021, 1))
        assert result == {}

# ТЕСТЫ: investment_bank


@pytest.mark.parametrize("month", ["2025-01", "2021-13", "abc", "2021/01", ""])
def test_investment_bank_invalid_month_format(
        sample_investment_transactions, month):
    """Тест: некорректный формат месяца → 0."""
    result = json.loads(
        investment_bank(
            month,
            sample_investment_transactions,
            10))
    assert result["total_savings"] == 0.0


def test_investment_bank_empty_transactions():
    """Тест: пустые транзакции → 0."""
    result = json.loads(investment_bank("2021-01", [], 10))
    assert result["total_savings"] == 0.0


def test_investment_bank_no_transactions_in_month(
        sample_investment_transactions):
    """Тест: нет трат в указанном месяце."""
    with patch("src.services.filter_transactions") as mock_filter:
        mock_filter.return_value = pd.DataFrame(sample_investment_transactions)
        result = json.loads(
            investment_bank(
                "2022-01",
                sample_investment_transactions,
                10))
        assert result["total_savings"] == 0.0


def test_investment_bank_correct_savings_calculation(
        sample_investment_transactions):
    """Тест: проверка правильности расчёта сбережений при округлении."""
    # Подменяем filter_transactions, чтобы он вернул нужные транзакции за
    # январь
    with patch("src.services.filter_transactions") as mock_filter:
        # Подготовим данные с правильными колонками
        mock_data = [{"Дата операции": "05.01.2021 10:00:00",
                      "Сумма операции": -123.45,
                      "Категория": "Супермаркеты"},
                     {"Дата операции": "06.01.2021 11:00:00",
                      "Сумма операции": -278.10,
                      "Категория": "Кафе"},
                     {"Дата операции": "07.01.2021 12:00:00",
                      "Сумма операции": -99.99,
                      "Категория": "Одежда"},
                     ]
        df_mock = pd.DataFrame(mock_data)
        df_mock["Дата операции"] = pd.to_datetime(
            df_mock["Дата операции"], format="%d.%m.%Y %H:%M:%S")
        df_mock["month"] = df_mock["Дата операции"].dt.strftime("%Y-%m")
        mock_filter.return_value = df_mock

        # Вызов функции
        result = json.loads(
            investment_bank(
                "2021-01",
                sample_investment_transactions,
                limit=10))

        # Ручной расчёт:
        # 123.45 → 130 → +6.55
        # 278.10 → 280 → +1.90
        # 99.99 → 100 → +0.01
        # Итого: 8.46
        assert result["total_savings"] == pytest.approx(8.46, abs=0.01)


def test_investment_bank_edge_amounts():
    """Тест: поведение при граничных суммах (0, 1, 10.00)."""
    transactions = [{"Дата операции": "05.01.2021 10:00:00",
                     "Сумма операции": -0.01,
                     "Категория": "Кафе"},
                    {"Дата операции": "06.01.2021 11:00:00",
                     "Сумма операции": -1.00,
                     "Категория": "Кафе"},
                    {"Дата операции": "07.01.2021 12:00:00",
                     "Сумма операции": -10.00,
                     "Категория": "Кафе"},
                    ]

    with patch("src.services.filter_transactions") as mock_filter:
        df_mock = pd.DataFrame(transactions)
        df_mock["Дата операции"] = pd.to_datetime(
            df_mock["Дата операции"], format="%d.%m.%Y %H:%M:%S")
        df_mock["month"] = df_mock["Дата операции"].dt.strftime("%Y-%m")
        mock_filter.return_value = df_mock

        result = json.loads(investment_bank("2021-01", transactions, limit=10))
        # 0.01 → 10 → +9.99
        # 1.00 → 10 → +9.00
        # 10.00 → 10 → +0.00
        # Итого: 18.99
        assert result["total_savings"] == pytest.approx(18.99, abs=0.01)


@pytest.mark.parametrize("invalid_limit", ["abc", None, {}, "10", "50.5"])
def test_investment_bank_invalid_limit_type(
        sample_investment_transactions, invalid_limit):
    """Тест: некорректный тип limit (не число) → 0.0."""
    result = json.loads(
        investment_bank(
            "2021-01",
            sample_investment_transactions,
            invalid_limit))
    assert result["total_savings"] == 0.0

# ———————————————————————
# ТЕСТЫ: search_person_transfers
# ———————————————————————


@patch("src.services.read_transactions_from_excel")
def test_search_person_transfers_valid_matches(mock_read, mock_excel_data):
    """Тест: корректные совпадения по паттерну."""
    mock_read.return_value = mock_excel_data

    result = json.loads(search_person_transfers())
    descriptions = [r["Описание"] for r in result]

    assert len(result) == 3
    assert "Валерий А." in descriptions
    assert "Анна Б." in descriptions
    assert "Иван И." in descriptions


@patch("src.services.read_transactions_from_excel")
def test_search_person_transfers_no_category_match(mock_read):
    """Тест: категория не «Переводы» — не учитывается."""
    mock_read.return_value = [
        {"Категория": "Супермаркеты", "Описание": "Валерий А."}]
    result = json.loads(search_person_transfers())
    assert result == []


@patch("src.services.read_transactions_from_excel")
def test_search_person_transfers_no_description_match(mock_read):
    """Тест: описание не соответствует паттерну."""
    mock_read.return_value = [
        {"Категория": "Переводы", "Описание": "Оплата по QR"}]
    result = json.loads(search_person_transfers())
    assert result == []


@patch("src.services.read_transactions_from_excel")
def test_search_person_transfers_handles_nan_and_none(mock_read):
    """Тест: корректная обработка None, 'nan', пустых строк."""
    mock_read.return_value = [
        {"Категория": None, "Описание": "Валерий А."},
        {"Категория": "nan", "Описание": "Анна Б."},
        {"Категория": "", "Описание": ""},
        {"Категория": "Переводы", "Описание": None},
        {"Категория": "Переводы", "Описание": "   "},
        {"Категория": "Переводы", "Описание": "Валерий А."},
    ]
    result = json.loads(search_person_transfers())
    assert len(result) == 1
    assert result[0]["Описание"] == "Валерий А."


@patch("src.services.read_transactions_from_excel")
def test_search_person_transfers_empty_data(mock_read):
    """Тест: пустой файл."""
    mock_read.return_value = []
    result = json.loads(search_person_transfers())
    assert result == []


@patch("src.services.read_transactions_from_excel")
def test_search_person_transfers_file_error(mock_read):
    """Тест: ошибка чтения файла → возвращает пустой список."""
    mock_read.side_effect = Exception("Файл не найден")
    result = json.loads(search_person_transfers())
    assert result == []

# ВЫДАЕТ ОШИБКУ


@patch("src.services.read_transactions_from_excel")
def test_search_person_transfers_pattern_matching(mock_read):
    """Тест: проверка паттерна имени и отчества с учётом очистки строки."""
    mock_read.return_value = [
        {"Категория": "Переводы",
         "Описание": "Иван И."},
        {"Категория": "Переводы",
         "Описание": "Петр П."},
        # ❌ нет точки
        {"Категория": "Переводы", "Описание": "Анна А"},
        # ✅ после strip() → "Валерий В."
        {"Категория": "Переводы",
         "Описание": "Валерий В. "},
        # ❌ лишний символ
        {"Категория": "Переводы",
         "Описание": "Мария М.!"},
        # ❌ не подходит
        {"Категория": "Переводы",
         "Описание": "Сергей С.С."},
        # ❌ имя слишком короткое
        {"Категория": "Переводы",
         "Описание": "А. А."},
    ]
    result = json.loads(search_person_transfers())
    descriptions = [r["Описание"] for r in result]
    assert len(result) == 3
    assert "Иван И." in descriptions
    assert "Петр П." in descriptions
    assert "Валерий В. " in descriptions  # оригинал сохраняется
