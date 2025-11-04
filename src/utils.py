import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)

API_KEY = "P9scVvXKu3F1SdIqsS0nKYndV8xBvxbC"
BASE_URL = "https://api.apilayer.com/exchangerates_data"
HEADERS = {
    "apikey": API_KEY
}

def get_currency_rates():
    currencies = ['USD', 'EUR']
    rates = []

    for currency in currencies:
        url = f"{BASE_URL}/convert?from=RUB&to={currency}&amount=1"
        response = requests.get(url, headers=HEADERS)

        # Проверяем статус
        response.raise_for_status()

        data = response.json()

        # В соответствии с документацией API, результат выглядит так:
        # {
        #   "date": "2018-02-22",
        #   "historical": "",
        #   "info": {
        #     "rate": 148.972231,
        #     "timestamp": 1519328414
        #   },
        #   "query": {
        #     "amount": 25,
        #     "from": "GBP",
        #     "to": "JPY"
        #   },
        #   "result": 3724.305775,
        #   "success": true
        # }
        rate_value = data.get('result')

        if rate_value is not None:
            rates.append({"currency": currency, "rate": rate_value})
        else:
            # Обработка ошибки, если ключа нет
            print(f"Не удалось получить курс для {currency}")

    return rates
