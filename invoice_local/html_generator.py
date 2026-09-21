import os
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from .calculator import amount_to_words


BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = BASE_DIR / "szablon_faktury.html"
OUTPUT_DIR = BASE_DIR / "output"

dll_dir = os.getenv("WEASYPRINT_DLL_DIR")

if dll_dir and Path(dll_dir).is_dir():
    os.add_dll_directory(dll_dir)

try:
    from weasyprint import HTML

except OSError as error:
    raise RuntimeError(
        "Nie można uruchomić WeasyPrint. "
        "Zainstaluj biblioteki GTK/Pango albo ustaw zmienną "
        "WEASYPRINT_DLL_DIR na folder z bibliotekami DLL."
    ) from error


def generate_invoice(
    invoice_number,
    issue_date,
    buyer,
    positions,
    place_of_issue,
    sale_date,
    exchange_rate,
    vat_rate,
    currency,
    seller,
    payment_days,
):
    env = Environment(
        loader=FileSystemLoader(str(BASE_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        undefined=StrictUndefined,
    )

    template = env.get_template(TEMPLATE_PATH.name)

    gross_amount = positions[0]["wartosc_brutto"]

    gross_amount_words = amount_to_words(
        gross_amount,
        currency,
    )

    rendered_invoice = template.render(
        numer_faktury=invoice_number,
        data_wystawienia=issue_date,
        klient=buyer,
        pozycje=positions,
        miejsce_wystawienia=place_of_issue,
        data_sprzedazy=sale_date,
        exchange_rate_message=exchange_rate,
        vat_rate=vat_rate,
        wartosc_brutto_slownie=gross_amount_words,
        waluta=currency,
        sprzedawca=seller,
        termin_platnosci_dni=payment_days,
    )

    OUTPUT_DIR.mkdir(exist_ok=True)

    safe_number = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        invoice_number,
    )

    html_path = OUTPUT_DIR / f"faktura_{safe_number}.html"
    pdf_path = OUTPUT_DIR / f"faktura_{safe_number}.pdf"

    if html_path.exists() or pdf_path.exists():
        raise ValueError(
            "Plik o tym numerze już istnieje. "
            "Wybierz inny numer faktury."
        )

    html_path.write_text(
        rendered_invoice,
        encoding="utf-8",
    )

    HTML(
        string=rendered_invoice,
        base_url=str(BASE_DIR),
    ).write_pdf(str(pdf_path))

    return pdf_path