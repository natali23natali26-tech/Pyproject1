import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from src.utils import (
    get_greeting,
    read_transactions_from_excel,
    get_conversion_rate,
    get_currency_rates,
    get_stock_prices,
    get_stock_rate_list,
    filter_transactions,
    get_card_summary,
    get_top_transactions,
)


# Тест: get_greeting — параметризация

@pytest.mark.parametrize(
    "time_str, expected",
    [
        ("2025-04-05 06:00:00", "Доброе утро"),
        ("2025-04-05 14:00:00", "Добрый день"),
        ("2025-04-05 20:00:00", "Добрый вечер"),
        ("2025-04-05 03:00:00", "Доброй ночи"),
    ],
)
def test_get_greeting(time_str, expected):
    assert get_greeting(time_str) == expected


# Тест: read_transactions_from_excel

@patch("src.utils.pd.read_excel")
def test_read_transactions_success(mock_read):
    mock_read.return_value = pd.DataFrame([{"Сумма платежа": -100}])
    result = read_transactions_from_excel("fake_path.xlsx")
    assert len(result) == 1


@patch("src.utils.pd.read_excel", side_effect=FileNotFoundError)
def test_read_transactions_file_not_found(mock_read):
    result = read_transactions_from_excel("fake_path.xlsx")
    assert result == []


# Тест: get_conversion_rate

@patch("src.utils.requests.get")
@patch("src.utils.os.getenv", return_value="test_key")
def test_get_conversion_rate_success(mock_env, mock_get):
    mock_get.return_value = MagicMock(status_code=200,
                                      json=lambda: {"result": "90.5"})
    result = get_conversion_rate("USD", "RUB", "1")
    assert result == 90.5


@patch("src.utils.requests.get")
@patch("src.utils.os.getenv", return_value="test_key")
def test_get_conversion_rate_failure(mock_env, mock_get):
    mock_get.return_value = MagicMock(status_code=400, text="Error")
    result = get_conversion_rate("USD", "RUB", "1")
    assert result is None


# Тест: get_currency_rates

@patch("src.utils.get_conversion_rate")
def test_get_currency_rates(mock_conv):
    mock_conv.return_value = 90.5
    result = get_currency_rates(["USD"])
    assert result == [{"currency": "USD", "rate": 90.5}]


# Тест: get_stock_prices

@patch("src.utils.requests.get")
@patch("src.utils.os.getenv", return_value="test_key")
def test_get_stock_prices_success(mock_env, mock_get):
    mock_get.return_value = MagicMock(status_code=200,
                                      json=lambda: {"price": "198.45"})
    result = get_stock_prices("AAPL")
    assert result == 198.45


@patch("src.utils.requests.get")
@patch("src.utils.os.getenv", return_value="test_key")
def test_get_stock_prices_failure(mock_env, mock_get):
    mock_get.return_value = MagicMock(status_code=404)
    result = get_stock_prices("XYZ")
    assert result is None


# Тест: get_stock_rate_list

@patch("src.utils.get_stock_prices")
def test_get_stock_rate_list(mock_price):
    # AAPL, GOOGL (ошибка), MSFT
    mock_price.side_effect = [198.45, None, 150.3]
    result = get_stock_rate_list(["AAPL", "GOOGL", "MSFT"])
    assert len(result) == 2
    assert result[0]["stock"] == "AAPL"
    assert result[1]["stock"] == "MSFT"


# Тест: filter_transactions

def test_filter_transactions():
    data = [
        {"Сумма платежа": -100, "Категория": "Еда"},
        {"Сумма платежа": 200, "Категория": "Зарплата"},  # доход — исключить
        {"Сумма платежа": -50, "Категория": "Наличные"},  # исключить
        {"Сумма платежа": -80, "Категория": "Развлечения"},
    ]
    df = pd.DataFrame(data)
    result = filter_transactions(df.to_dict("records"))
    assert len(result) == 2
    assert "Еда" in result["Категория"].values
    assert "Развлечения" in result["Категория"].values


# Тест: get_card_summary

def test_get_card_summary():
    data = [
        {"Номер карты": "1111222233334444", "Сумма платежа": -1000},
        {"Номер карты": "1111222233334444", "Сумма платежа": -500},
        {"Номер карты": "5555666677778888", "Сумма платежа": -2000},
    ]
    df = pd.DataFrame(data)
    result = get_card_summary(df)
    assert len(result) == 2
    assert result[0]["last_digits"] == "4444"
    assert result[0]["total_spent"] == 1500
    assert result[0]["cashback"] == 15.0


# Тест: get_top_transactions

def test_get_top_transactions():
    data = [
        {"Дата платежа": "2025-01-01",
         "Сумма платежа": -100,
         "Категория": "Еда",
         "Описание": "Кофе"},
        {"Дата платежа": "2025-01-02",
         "Сумма платежа": -500,
         "Категория": "Одежда",
         "Описание": "Футболка"},
        {"Дата платежа": "2025-01-03",
         "Сумма платежа": -200,
         "Категория": "Транспорт",
         "Описание": "Такси"},
    ]
    df = pd.DataFrame(data)
    result = get_top_transactions(df, count=2)
    assert len(result) == 2
    assert result[0]["amount"] == 500
    assert result[1]["amount"] == 200
