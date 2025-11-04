from datetime import datetime


def get_greeting(time_str: str) -> str:
    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    hour = dt.hour
    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 17:
        return "Добрый день"
    elif 17 <= hour < 21:
        return "Добрый вечер"
    else:
        return "Доброй ночи"
