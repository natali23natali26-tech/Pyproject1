import json
from datetime import datetime
from pathlib import Path
from unittest.mock import mock_open, patch

import pandas as pd
import pytest

from src.reports import spending_by_category, save_report


@pytest.fixture
def df():
    """Тестовые транзакции."""
    return pd.DataFrame({
        "Дата операции": [
            "01.01.2020 12:00:00",  # входит в 3 месяца до 2020-04-01
            "15.02.2020 10:30:00",  # входит
            "10.03.2020 18:45:00",  # не тратит
            "05.05.2020 09:15:00",  # после 2020-04-01 → не входит
        ],
        "Категория": ["Супермаркеты",
                      "супермаркеты",
                      "Переводы",
                      "Супермаркеты"],
        "Сумма операции": [-1000.0, -2500.5, 5000.0, -1500.75],
        "Описание": ["Пятёрочка", "Перекрёсток", "Другу", "Ашан"]
    })


@pytest.fixture(autouse=True)
def mock_log():
    """Мок логгера."""
    with patch("src.reports.logger") as m:
        yield m


# --- 1. Параметризованные сценарии: основная логика ---
@pytest.mark.parametrize("category, date, total, warning, hint", [
    ("Супермаркеты", "2020-04-01",
     3500.5, None, None),  # только 2 операции до 2020-04-01
    ("Переводы", "2020-04-01", 0,
     "существует, но трат по ней не найдено", None),
    ("Неизвестная", "2020-04-01", 0,
     "не найдена", None),
    ("Супермаркеты", "2025-01-01", 0,
     "в указанный период", "Данные доступны с"),
])
def test_spending_by_category_scenarios(df,
                                        category,
                                        date,
                                        total,
                                        warning,
                                        hint):
    result = json.loads(spending_by_category(df, category, date))

    assert result["category"] == category
    assert abs(result["total"] - total) < 0.01

    if warning:
        assert warning in result["warning"]
        if hint:
            assert hint in result["hint"]
    else:
        assert "warning" not in result


# --- 2. Пустой DataFrame ---
def test_empty_df():
    result = json.loads(spending_by_category(pd.DataFrame(),
                                             "Супермаркеты"))
    assert result["warning"] == "Пустой DataFrame"


# --- 3. Тест: текущая дата (date=None) ---
def test_current_date(df, mock_log):
    with patch("src.reports.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2020, 4, 1)
        mock_dt.strptime = datetime.strptime

        result = json.loads(spending_by_category(df,
                                                 "Супермаркеты",
                                                 date=None))
        assert result["period"]["to"] == "2020-04-01"
        assert abs(result["total"] - 3500.5) < 0.01  # только 2 операции


# --- 4. Тест: структура spending (описание, дата, сумма) ---
def test_spending_structure(df):
    result = json.loads(spending_by_category(df,
                                             "Супермаркеты",
                                             "2020-04-01"))
    spending = result["spending"]

    assert len(spending) == 2  # 05.05.2020 — после 2020-04-01 → не входит
    assert spending[0]["amount"] == 1000.0
    assert spending[0]["date"] == "2020-01-01"
    assert spending[0]["description"] == "Пятёрочка"
    assert isinstance(spending[0]["amount"], float)


# --- 5. Тест: доступные категории (регистр, пробелы) ---
def test_available_categories(df):
    result = json.loads(spending_by_category(df, "  "
                                                 "супермаркеты  ",
                                             "2020-04-01"))
    assert result["category"] == "  супермаркеты  "


# --- 6. Тест: save_report — успешное сохранение ---
@patch("json.dump")
@patch("src.reports.open", new_callable=mock_open)
def test_save_report_success(mock_open, mock_dump, df, mock_log):
    spending_by_category(df, "Супермаркеты", filename=Path("test.json"))

    # Проверка open
    mock_open.assert_called_once()
    open_args, open_kwargs = mock_open.call_args
    assert str(open_args[0]) == "test.json"
    assert open_args[1] == "w"
    assert open_kwargs["encoding"] == "utf-8"

    # Проверка json.dump
    mock_dump.assert_called_once()
    dump_args, dump_kwargs = mock_dump.call_args

    assert dump_kwargs["ensure_ascii"] is False
    assert dump_kwargs["indent"] == 2
    assert dump_kwargs["default"] is str

    # Проверка лога
    mock_log.info.assert_called_with("Отчёт сохранён:"
                                     " test.json")


# --- 7. Тест: save_report — ошибка записи ---
@patch("src.reports.open", side_effect=PermissionError("No access"))
def test_save_report_permission_error(mock_open, df, mock_log):
    with pytest.raises(PermissionError):
        spending_by_category(df, "Супермаркеты",
                             filename=Path("forbidden.json"))
    mock_log.error.assert_called()


# 8. Тест: save_report — автогенерация имени файла
@patch("src.reports.datetime")
@patch("src.reports.Path.mkdir")
@patch("src.reports.open", new_callable=mock_open)
@patch("json.dump")
def test_save_report_auto_filename(mock_dump,
                                   mock_open,
                                   mock_mkdir,
                                   mock_dt, df,
                                   mock_log):
    mock_dt.now.return_value = datetime(2025,
                                        1,
                                        1,
                                        12,
                                        0,
                                        0)

    spending_by_category(df, "Супермаркеты")

    mock_mkdir.assert_called_once_with(exist_ok=True)
    mock_log.info.assert_called()
    log_msg = mock_log.info.call_args[0][0]
    assert "report_2025-01-01_12-00-00.json" in log_msg


# --- 9. Тест: save_report можно использовать отдельно ---
def test_save_report_standalone():
    @save_report
    def dummy():
        return '{"test": "ок"}'

    with patch("src.reports.open", new_callable=mock_open), patch("json.dump"):
        result = dummy(filename=Path("dummy.json"))
        assert json.loads(result) == {"test": "ок"}
