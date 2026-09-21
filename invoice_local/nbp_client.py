from datetime import datetime, timedelta

import requests


def find_previous_business_day(date_of_sale):
    previous_day = date_of_sale - timedelta(days=1)

    while previous_day.weekday() in (5, 6):
        previous_day -= timedelta(days=1)

    return previous_day


def get_exchange_rate(currency_code, date_of_sale):
    if isinstance(date_of_sale, str):
        date_of_sale = datetime.strptime(
            date_of_sale,
            "%Y-%m-%d",
        )

    previous_business_day = find_previous_business_day(date_of_sale)
    formatted_date = previous_business_day.strftime("%Y-%m-%d")

    url = (
        f"https://api.nbp.pl/api/exchangerates/rates/A/"
        f"{currency_code}/{formatted_date}/"
    )

    response = requests.get(url, timeout=15)

    if response.status_code != 200:
        return None

    data = response.json()
    rate_data = data["rates"][0]

    return {
        "currency": currency_code,
        "rate": rate_data["mid"],
        "table_number": rate_data["no"],
        "date": formatted_date,
    }