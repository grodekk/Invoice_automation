from decimal import Decimal, ROUND_HALF_UP

from num2words import num2words


def calculate_gross(amount_netto, vat_rate):
    netto = Decimal(str(amount_netto))
    vat = Decimal(str(vat_rate))

    gross = netto * (Decimal("1") + vat / Decimal("100"))

    return float(gross.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def build_position(order_data, vat_rate):
    amount_netto = round(order_data["amount_netto"], 2)
    amount_brutto = calculate_gross(amount_netto, vat_rate)
    amount_vat = round(amount_brutto - amount_netto, 2)

    order_number = order_data["order_number"]
    route_from = order_data["route_from"] or ""
    route_to = order_data["route_to"] or ""
    vehicle_number = order_data["vehicle_number"] or ""

    service_name = (
        f"Usługa transportowa, {order_number}, "
        f"{route_from} - {route_to}, {vehicle_number}"
    )

    return {
        "lp": "1",
        "nazwa": service_name,
        "jm": "usł.",
        "ilosc": 1,
        "cena_netto": amount_netto,
        "wartosc_netto": amount_netto,
        "stawka_vat": f"{vat_rate}%",
        "kwota_vat": amount_vat,
        "wartosc_brutto": amount_brutto,
        "waluta": order_data["currency"],
    }


def amount_to_words(amount, currency):
    value = Decimal(str(amount)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    integer_part = int(value)
    fractional_part = int(
        (value - integer_part) * 100
    )

    currency = currency.upper()

    if fractional_part == 0:
        return (
            f"{num2words(integer_part, lang='pl').capitalize()} "
            f"{currency}"
        )

    return (
        f"{num2words(integer_part, lang='pl')} "
        f"{currency} {fractional_part:02d}/100"
    )