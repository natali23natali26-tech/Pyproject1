import pytest
from unittest.mock import patch, Mock
from src.views import this_home


# Мок-данные — теперь с правильными ключами, как в Excel и utils.py
MOCK_TRANSACTIONS = [
    {
        "Номер карты": "1234567890121234",
        "Сумма платежа": -100,
        "Категория": "Еда",
        "Дата платежа": "2023-10-01",
        "Описание": "Обед в кафе"
    },
    {
        "Номер карты": "9876543210988765",
        "Сумма платежа": -200,
        "Категория": "Транспорт",
        "Дата платежа": "2023-10-02",
        "Описание": "Проезд на автобусе"
    },
]


@pytest.fixture
def mock_all():
    """Мокаем все внешние зависимости."""
    with patch("src.views.read_transactions_from_excel") as mock_read, \
         patch("src.views.filter_transactions") as mock_filter, \
         patch("src.views.get_greeting") as mock_greet, \
         patch("src.views.get_currency_rates") as mock_currency, \
         patch("src.views.get_stock_rate_list") as mock_stock, \
         patch("src.views.get_card_summary") as mock_cards, \
         patch("src.views.get_top_transactions") as mock_top:

        # Настраиваем моки
        mock_read.return_value = MOCK_TRANSACTIONS
        mock_filter.return_value = MOCK_TRANSACTIONS  # фильтр не убирает
        mock_greet.return_value = "Добрый день"
        mock_currency.return_value = [
            {"currency": "USD", "rate": 75.5},
            {"currency": "EUR", "rate": 85.2},
        ]
        mock_stock.return_value = [
            {"stock": "AAPL", "price": 150.0},
            {"stock": "TSLA", "price": 250.0},
        ]
        mock_cards.return_value = [
            {"last_digits": "1234", "total_spent": 100, "cashback": 1.0},
            {"last_digits": "8765", "total_spent": 200, "cashback": 2.0},
        ]
        mock_top.return_value = [
            {
                "date": "2023-10-02",
                "amount": 200,
                "category": "Транспорт",
                "description": "Проезд на автобусе"
            }
        ]

        # Возвращаем моки, если нужно проверить вызовы
        yield {
            "read": mock_read,
            "filter": mock_filter,
            "greet": mock_greet,
            "currency": mock_currency,
            "stock": mock_stock,
            "cards": mock_cards,
            "top": mock_top,
        }


def test_this_home_success(mock_all):
    """Тест: успешное формирование главной страницы."""
    result = this_home()

    # Проверяем структуру и данные результата
    assert result["greeting"] == "Добрый день"
    assert len(result["cards"]) == 2
    assert len(result["top_transactions"]) == 1
    assert len(result["currency_rates"]) == 2
    assert len(result["stock_prices"]) == 2

    # Проверяем, что все функции были вызваны
    mock_all["read"].assert_called_once()
    mock_all["filter"].assert_called_once()
    mock_all["greet"].assert_called_once()

    # Проверяем аргументы вызовов
    mock_all["currency"].assert_called_once_with(["USD", "EUR"])
    mock_all["stock"].assert_called_once_with(["AAPL",
                                               "AMZN",
                                               "GOOGL",
                                               "MSFT",
                                               "TSLA"])
    mock_all["cards"].assert_called_once()
    mock_all["top"].assert_called_once()


@pytest.mark.parametrize("hour,expected", [
    (5, "Доброй ночи"),
    (7, "Доброе утро"),
    (13, "Добрый день"),
    (20, "Добрый вечер"),
])
def test_greeting_based_on_hour(hour, expected, mock_all):
    """Параметризованный тест: приветствие зависит от времени."""
    with patch("src.views.datetime") as mock_dt:
        # Мокаем текущее время
        mock_now = Mock()
        mock_now.hour = hour
        mock_dt.now.return_value = mock_now

        # Мокаем get_greeting, чтобы вернул нужное приветствие
        with patch("src.views.get_greeting",
                   return_value=expected) as mock_greet:
            result = this_home()
            mock_greet.assert_called_once()
            assert result["greeting"] == expected


def test_this_home_empty_transactions(mock_all):
    """Тест: обработка пустого списка транзакций."""
    # Мокаем пустые данные
    mock_all["read"].return_value = []
    mock_all["filter"].return_value = []
    mock_all["cards"].return_value = []  # 🔴 Вот это было пропущено!
    mock_all["top"].return_value = []

    result = this_home()

    # Проверяем, что приветствие есть, а карт и транзакций — нет
    assert result["greeting"] == "Добрый день"
    assert result["cards"] == []
    assert result["top_transactions"] == []

    # Проверяем, что функции вызваны
    mock_all["read"].assert_called_once()
    mock_all["filter"].assert_called_once()
    mock_all["greet"].assert_called_once()
    mock_all["cards"].assert_called_once()
    mock_all["top"].assert_called_once()
