import re
from datetime import datetime
from pathlib import Path
from PyPDF2 import PdfReader
from .models import ParsedOrder


def parse_date_any(value):
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(value).strip(), fmt)
        except ValueError:
            continue
    return None


def _country(value):
    match = re.search(r"[A-Z]{2}", value or "")
    return match.group(0) if match else None


def extract_order_data(pdf_path) -> ParsedOrder:
    with Path(pdf_path).open("rb") as file:
        text = "\n".join((page.extract_text() or "") for page in PdfReader(file).pages)

    lines = text.splitlines()
    order = None
    net = None
    route_from = route_to = vehicle = None

    marker = "Zlecenie przewozowe"
    if marker in text:
        order = text.split(marker, 1)[1].splitlines()[0].strip()

    if "Usługa transportowa" in text:
        for line in text.split("Usługa transportowa", 1)[1].splitlines():
            match = re.search(r"(\d[\d\s.,]*)", line)
            if match:
                try:
                    net = float(match.group(1).replace(" ", "").replace(",", "."))
                    break
                except ValueError:
                    pass

    for index, line in enumerate(lines):
        if "Komentarze" in line:
            found = [row.strip() for row in lines[max(0, index - 10) : index] if re.search(r"[A-Z]{2}", row)]
            if len(found) >= 2:
                route_from, route_to = found[-2], found[-1]
            elif found:
                route_from = found[-1]

        if "Nr rejestracyjny" in line:
            for row in lines[index : index + 5]:
                match = re.search(r"\b[A-Z0-9]{5,8}\b", row)
                if match:
                    vehicle = match.group(0)
                    break

    dates = [date for line in lines if (date := parse_date_any(line))]
    sale_date = max(dates) if dates else datetime.now()
    return ParsedOrder(order, net, route_from, route_to, sale_date, vehicle)
