import pytest
import pandas as pd
from unittest.mock import patch
from src.reports import spending_by_category, report_to_file_default, report_to_file

@pytest.fixture
def sample_transactions():
    data = {
        'date': ['2023-08-15', '2023-07-20', '2023-06-10', '2023-05-01', '2023-09-01'],
        'amount': [100, 200, 300, 400, 150],
        'category': ['Питание', 'Питание', 'Развлечения', 'Питание', 'Питание']
    }
    return pd.DataFrame(data)

@pytest.mark.parametrize("test_date,expected_start,expected_end,expected_count", [
    ("2023-09-15", "2023-06-17", "2023-09-15", 3),
])
def test_spending_by_category_filtering(sample_transactions, test_date, expected_start, expected_end, expected_count):
    fixed_now = pd.to_datetime("2023-09-15")
    with patch('reports.datetime') as mock_datetime:
        mock_datetime.datetime.now.return_value = fixed_now
        mock_datetime.datetime.strptime.side_effect = lambda date_str, fmt: pd.to_datetime(date_str)
        with patch('reports.json.dump') as mock_dump:
            result = spending_by_category(sample_transactions, 'Питание', test_date)
            mock_dump.assert_called()
            assert len(result) == expected_count
            for _, row in result.iterrows():
                date_obj = pd.to_datetime(row['date'])
                start = pd.to_datetime(expected_start)
                end = pd.to_datetime(expected_end)
                assert start <= date_obj <= end
                assert row['category'] == 'Питание'

def test_report_decorator_saves_file_default(sample_transactions):
    with patch('reports.json.dump') as mock_dump, patch('builtins.open') as mock_open:
        @report_to_file_default
        def dummy_func():
            return {"result": 42}
        dummy_func()
        mock_open.assert_called_with("dummy_func_report.json", 'w', encoding='utf-8')
        mock_dump.assert_called_once_with({"result": 42}, mock_open(), ensure_ascii=False, indent=4)

def test_report_decorator_saves_file_with_param(sample_transactions):
    with patch('reports.json.dump') as mock_dump, patch('builtins.open') as mock_open:
        @report_to_file('custom_report.json')
        def dummy_func():
            return {"status": "ok"}
        dummy_func()
        mock_open.assert_called_with('custom_report.json', 'w', encoding='utf-8')
        mock_dump.assert_called_once_with({"status": "ok"}, mock_open(), ensure_ascii=False, indent=4)
