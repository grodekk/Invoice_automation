import re
from datetime import datetime
from pathlib import Path

from PyPDF2 import PdfReader


EUROPEAN_COUNTRY_CODES = {
    "AL", "AD", "AM", "AT", "AZ", "BY", "BE", "BA", "BG", "HR",
    "CY", "CZ", "DK", "EE", "FI", "FR", "GE", "DE", "GR", "HU",
    "IS", "IE", "IT", "KZ", "XK", "LV", "LI", "LT", "LU", "MT",
    "MD", "MC", "ME", "NL", "NO", "PL", "PT", "RO", "RU", "SM",
    "RS", "SK", "SI", "ES", "SE", "CH", "TR", "UA", "GB", "VA",
    "D-",
}


def extract_order_data(pdf_path):
    order_number = None
    vehicle_number = None
    amount_netto = None
    currency = None
    route_from = None
    route_to = None
    sale_date = None
    formatted_date = None

    with Path(pdf_path).open("rb") as pdf_file:
        pdf_reader = PdfReader(pdf_file)
        first_page = pdf_reader.pages[0]
        text = first_page.extract_text() or ""

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if "Zlecenie przewozowe" in text:
        start = text.index("Zlecenie przewozowe") + len("Zlecenie przewozowe")
        order_number = text[start:].strip().splitlines()[0].strip()

    vehicle_number_found = False

    for line in lines:
        if "Nr rejestracyjny" in line:
            vehicle_number_found = True
            continue

        if vehicle_number_found:
            match = re.search(r"\b\w{7}\b", line)

            if match:
                vehicle_number = match.group()
                break

    if "Usługa transportowa" in text:
        start = text.index("Usługa transportowa") + len("Usługa transportowa")

        for line in text[start:].splitlines():
            if not line.strip():
                continue

            match = re.match(
                r"(\d+[\.,]?\d*)\s*([A-Za-z]+)",
                line.strip(),
            )

            if match:
                amount_netto = float(match.group(1).replace(",", "."))
                currency = match.group(2).upper()

            break

    if "Komentarze" in lines:
        comments_index = lines.index("Komentarze")
        found_routes = []

        for index in range(comments_index - 1, -1, -1):
            line = lines[index].strip()

            if any(code in line for code in EUROPEAN_COUNTRY_CODES):
                found_routes.append(line)

                if len(found_routes) == 2:
                    break

        if len(found_routes) >= 1:
            route_to = found_routes[0]

        if len(found_routes) >= 2:
            route_from = found_routes[1]

    if "Data" in lines:
        date_index = lines.index("Data")

        if date_index + 2 < len(lines):
            date_string = lines[date_index + 2].strip()

            for date_format in ("%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y"):
                try:
                    sale_date = datetime.strptime(
                        date_string,
                        date_format,
                    )
                    formatted_date = sale_date.strftime("%d-%m-%Y")
                    break

                except ValueError:
                    continue

    return {
        "order_number": order_number,
        "vehicle_number": vehicle_number,
        "amount_netto": amount_netto,
        "currency": currency,
        "route_from": route_from,
        "route_to": route_to,
        "sale_date": sale_date,
        "formatted_date": formatted_date,
    }