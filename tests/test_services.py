import pytest
from unittest.mock import patch
import json
import datetime
from src.services import analyze_profitable_categories, investment_bank, analyze_profitable_categories, investment_bank

@pytest.mark.parametrize(
    "data,year,month,expected",
    [
        (
            [
                {"date": "2023-08-05", "amount": 1000, "category": "Развлечения"},
                {"date": "2023-08-15", "amount": 2000, "category": "Гаджеты"},
                {"date": "2023-07-20", "amount": 1500, "category": "Путешествия"},
                {"date": "2023-08-10", "amount": 3000, "category": "Развлечения"}
            ],
            2023,
            8,
            {
                "Развлечения": (1000 + 3000) * 0.01,
                "Гаджеты": 2000 * 0.01
            }
        ),
        (
            [
                {"date": "2024-01-10", "amount": 500, "category": "Напитки"},
                {"date": "2024-01-20", "amount": 1000, "category": "Общение"}
            ],
            2024,
            1,
            {
                "Напитки": 500 * 0.01,
                "Общение": 1000 * 0.01
            }
        ),
        (
            [
                {"date": "2023-09-01", "amount": 300, "category": "Продукты"}
            ],
            2023,
            8,
            {}
        ),
    ]
)
def test_analyze_profitable_categories(data, year, month, expected):
    result_json = analyze_profitable_categories(data, year, month)
    result = json.loads(result_json)
    # Проверка, что полученная сумма совпадает с ожидаемой
    for cat, cashback in expected.items():
        assert abs(result.get(cat, 0) - cashback) < 1e-6
    # Проверка, что все категории ожидаемые есть в результате
    for key in expected:
        assert key in result

@pytest.mark.parametrize(
    "transactions,month_str,limit,expected",
    [
        (
            [
                {"date": "2023-08-01", "amount": 1712},
                {"date": "2023-08-10", "amount": 500},
                {"date": "2023-08-15", "amount": 1050}
            ],
            "2023-08",
            50,
            # Расчет:
            # 1712: округление (1712+50-1)//50*50 = (1712+49)//50*50 = (1761)//50*50= 35*50=1750; difference=1750-1712=38
            # 500: ((500+49)//50)*50= (549)//50*50= 10*50=500; difference=0
            # 1050: ((1050+49)//50)*50= (1099)//50*50= 21*50=1050; difference=0
            # Сумма=38+0+0=38
            38.0
        ),
        (
            [
                {"date": "2023-09-01", "amount": 600}
            ],
            "2023-09",
            100,
            # 600: ((600+99)//100)*100= (699)//100*100=6*100=600 разница=0
            0.0
        ),
        (
            [
                {"date": "2023-08-01", "amount": 1234}
            ],
            "2023-08",
            50,
            # 1234: ((1234+49)//50)*50= (1283)//50*50=25*50=1250 разница=16
            16.0
        ),
    ]
)
def test_investment_bank(transactions, month_str, limit, expected):
    result = investment_bank(month_str, transactions, limit)
    assert abs(result - expected) < 1e-2
