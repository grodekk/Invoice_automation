import os
import json
from pathlib import Path
import ctypes

try:
    lib = ctypes.CDLL('D:/msys2/mingw64/bin/libgobject-2.0-0.dll')
    print("Biblioteka załadowana pomyślnie")
except OSError as e:
    print(f"Błąd: {e}")

try:
    lib_pango = ctypes.CDLL('D:/msys2/mingw64/bin/libpango-1.0-0.dll')
    print("Biblioteka Pango załadowana pomyślnie")
except OSError as e:
    print(f"Błąd przy ładowaniu Pango: {e}")

try:
    lib_fontconfig = ctypes.CDLL('D:/msys2/mingw64/bin/libfontconfig-1.dll')
    print("Biblioteka Fontconfig załadowana pomyślnie")
except OSError as e:
    print(f"Błąd przy ładowaniu Fontconfig: {e}")

import tkinter as tk
from tkinter import filedialog, messagebox
from PyPDF2 import PdfReader
import requests
from num2words import num2words
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from weasyprint import HTML
import re
from datetime import datetime, timedelta


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"

DEFAULT_CONFIG = {
    "miejsce_wystawienia": "Miasto demonstracyjne",
    "termin_platnosci_dni": 45,
    "sprzedawca": {
        "nazwa": "Transport DEMO",
        "adres": "Przykładowa 1",
        "miasto": "00-000 Miasto demonstracyjne",
        "nip": "DEMO-NIP-SPRZEDAWCY",
        "konto_pln": "DEMO — rachunek PLN",
        "konto_eur": "DEMO — rachunek EUR"
    },
    "klient": {
        "nazwa": "Zleceniodawca DEMO",
        "adres": "Testowa 2",
        "miasto": "00-000 Miasto demonstracyjne",
        "NIP": "DEMO-NIP-NABYWCY"
    }
}


def load_config():
    # Tworzymy plik tylko przy pierwszym uruchomieniu.
    if not CONFIG_PATH.exists():
        with CONFIG_PATH.open("x", encoding="utf-8") as file:
            json.dump(DEFAULT_CONFIG, file, ensure_ascii=False, indent=4)

    try:
        with CONFIG_PATH.open(encoding="utf-8-sig") as file:
            config = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Niepoprawny config.json: wiersz {error.lineno}, "
            f"kolumna {error.colno}. Sprawdź przecinki i cudzysłowy."
        ) from error

    if not isinstance(config, dict):
        raise ValueError("config.json musi zawierać obiekt JSON.")

    required = {
        "sprzedawca": ("nazwa", "adres", "miasto", "nip", "konto_pln", "konto_eur"),
        "klient": ("nazwa", "adres", "miasto", "NIP")
    }
    for section, fields in required.items():
        if not isinstance(config.get(section), dict):
            raise ValueError(f"Brak sekcji {section} w config.json.")
        for field in fields:
            value = config[section].get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Uzupełnij {section}.{field} w config.json.")

    place = config.get("miejsce_wystawienia")
    if not isinstance(place, str) or not place.strip():
        raise ValueError("Uzupełnij miejsce_wystawienia w config.json.")

    days = config.get("termin_platnosci_dni")
    if type(days) is not int or days < 0:
        raise ValueError("termin_platnosci_dni musi być liczbą całkowitą >= 0.")
    return config


class InvoiceGeneratorApp:
    def __init__(self, master, config):
        self.config = config
        self.master = master
        self.master.title("Generator faktur")

        # Ramka do przechowywania widżetów
        self.frame = tk.Frame(master, padx=10, pady=10)
        self.frame.pack()

        # Etykieta i pole tekstowe dla ścieżki pliku PDF
        self.label_pdf_path = tk.Label(self.frame, text="Ścieżka do pliku PDF:")
        self.label_pdf_path.grid(row=0, column=0, sticky=tk.E)

        self.entry_pdf_path = tk.Entry(self.frame, width=50)
        self.entry_pdf_path.grid(row=0, column=1)

        self.button_browse = tk.Button(self.frame, text="Wybierz", command=self.select_pdf_file)
        self.button_browse.grid(row=0, column=2, padx=5)

        # Etykieta i suwak do wyboru stawki VAT
        self.label_vat = tk.Label(self.frame, text="Stawka VAT (%):")
        self.label_vat.grid(row=1, column=0, sticky=tk.E)

        self.slider_vat = tk.Scale(self.frame, from_=0, to=23, resolution=1, orient=tk.HORIZONTAL)
        self.slider_vat.set(23)  # Ustawienie domyślnej wartości na 23%
        self.slider_vat.grid(row=1, column=1, padx=5)

        # Etykieta i pole tekstowe do ustawiania numeru faktury
        self.label_invoice_number = tk.Label(self.frame, text="Numer faktury (DD/MM/YYYY):")
        self.label_invoice_number.grid(row=2, column=0, sticky=tk.E)

        self.entry_invoice_number = tk.Entry(self.frame, width=10)
        self.entry_invoice_number.grid(row=2, column=1, padx=5)

        # Etykieta i pole tekstowe do ustawiania daty wystawienia faktury
        self.label_invoice_date = tk.Label(self.frame, text="Data wystawienia (DD-MM-YYYY):")
        self.label_invoice_date.grid(row=3, column=0, sticky=tk.E)

        self.entry_invoice_date = tk.Entry(self.frame, width=15)
        self.entry_invoice_date.grid(row=3, column=1, padx=5)
        self.entry_invoice_date.insert(0, datetime.now().strftime('%d-%m-%Y'))  # domyślnie dzisiejsza data

        # Przycisk do generowania faktury
        self.button_generate = tk.Button(self.frame, text="Generuj fakturę", command=self.generate_invoice)
        self.button_generate.grid(row=4, column=1, pady=10)

    def select_pdf_file(self):
        pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if pdf_path:
            self.entry_pdf_path.delete(0, tk.END)
            self.entry_pdf_path.insert(tk.END, pdf_path)

    def extract_invoice_data(self, pdf_path):
        order_number = None
        vehicle_number = None
        amount_netto = None
        currency = None
        element1 = None
        element2 = None
        date_of_sale = None
        formatted_date = None

        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PdfReader(pdf_file)
            first_page = pdf_reader.pages[0]
            text = first_page.extract_text() or ""

            if "Zlecenie przewozowe" in text:
                start = text.index("Zlecenie przewozowe") + len("Zlecenie przewozowe")
                order_number = text[start:].strip().split('\n')[0].strip()

            lines = text.split('\n')
            vehicle_number_found = False
            for line in lines:
                if "Nr rejestracyjny" in line:
                    vehicle_number_found = True
                elif vehicle_number_found:
                    match = re.search(r"\b\w{7}\b", line)
                    if match:
                        vehicle_number = match.group()
                        break

            if "Usługa transportowa" in text:
                start = text.index("Usługa transportowa") + len("Usługa transportowa")
                lines_after_usluga = text[start:].split('\n')
                for line in lines_after_usluga:
                    if line.strip():
                        match = re.match(r"(\d+[\.,]?\d*)\s*([A-Za-z]+)", line.strip())
                        if match:
                            amount_netto = float(match.group(1).replace(',', '.'))
                            currency = match.group(2)
                        break

            european_country_codes = {
                "AL", "AD", "AM", "AT", "AZ", "BY", "BE", "BA", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
                "GE", "DE", "GR", "HU", "IS", "IE", "IT", "KZ", "XK", "LV", "LI", "LT", "LU", "MT", "MD", "MC",
                "ME", "NL", "NO", "PL", "PT", "RO", "RU", "SM", "RS", "SK", "SI", "ES", "SE", "CH", "TR", "UA", "GB",
                "VA", "D-"
            }
            if "Komentarze" in lines:
                index_of_komentarze = lines.index("Komentarze")
                i = 1
                while index_of_komentarze - i >= 0:
                    line = lines[index_of_komentarze - i].strip()
                    if any(code in line for code in european_country_codes):
                        if not element2:
                            element2 = line
                        elif not element1:
                            element1 = line
                            break
                    i += 1

            if "Data" in lines:
                index_of_data = lines.index("Data")
                if index_of_data + 2 < len(lines):
                    date_str = lines[index_of_data + 2].strip()
                    date_formats = ['%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y']
                    for fmt in date_formats:
                        try:
                            date_of_sale = datetime.strptime(date_str, fmt)
                            formatted_date = date_of_sale.strftime('%d-%m-%Y')
                            break
                        except ValueError:
                            continue

        return order_number, vehicle_number, amount_netto, currency, element1, element2, date_of_sale, formatted_date

    def fetch_exchange_rates(self, date_of_sale):
        url = f'https://api.nbp.pl/api/exchangerates/tables/A/{date_of_sale}/'
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f'Error fetching data. Status code: {response.status_code}')
            return None

    def find_previous_business_day(self, date_of_sale):
        previous_day = date_of_sale - timedelta(days=1)
        while previous_day.weekday() in [5, 6]:
            previous_day -= timedelta(days=1)
        return previous_day

    def get_exchange_rate(self, currency_code, date_of_sale):
        if isinstance(date_of_sale, str):
            date_of_sale = datetime.strptime(date_of_sale, '%Y-%m-%d')
        previous_day = self.find_previous_business_day(date_of_sale)
        formatted_date = previous_day.strftime('%Y-%m-%d')
        url = f'https://api.nbp.pl/api/exchangerates/rates/A/{currency_code}/{formatted_date}/'
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            table_number = data['rates'][0]['no']
            exchange_rate = data['rates'][0]['mid']
            return currency_code, exchange_rate, table_number, formatted_date
        else:
            return None

    def generuj_fakture(self, numer_faktury, data_wystawienia, klient, pozycje, miejsce_wystawienia, data_sprzedazy,
                        exchange_rate_message, vat_rate, currency):
        env = Environment(
            loader=FileSystemLoader(str(BASE_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
            undefined=StrictUndefined
        )
        template = env.get_template('szablon_faktury.html')
        calkowita_czesc = int(pozycje[0]["wartosc_brutto"])
        ulamkowa_czesc = round(pozycje[0]["wartosc_brutto"] - calkowita_czesc, 2) * 100
        if ulamkowa_czesc == 0:
            wartosc_brutto_slownie = num2words(calkowita_czesc,
                                               lang='pl').capitalize() + f' {pozycje[0]["waluta"].upper()}'
        else:
            wartosc_brutto_slownie = f"{num2words(calkowita_czesc, lang='pl')} {pozycje[0]['waluta'].upper()} {int(ulamkowa_czesc)}/100 "
        rendered_faktura = template.render(
            numer_faktury=numer_faktury,
            data_wystawienia=data_wystawienia,
            klient=klient,
            pozycje=pozycje,
            miejsce_wystawienia=miejsce_wystawienia,
            data_sprzedazy=data_sprzedazy,
            exchange_rate_message=exchange_rate_message,
            vat_rate=vat_rate,
            wartosc_brutto_slownie=wartosc_brutto_slownie,
            waluta=currency,
            sprzedawca=self.config["sprzedawca"],
            termin_platnosci_dni=self.config["termin_platnosci_dni"],
        )
        output_dir = BASE_DIR / "output"
        output_dir.mkdir(exist_ok=True)
        safe_number = re.sub(r"[^A-Za-z0-9_-]+", "_", numer_faktury)
        html_path = output_dir / f"faktura_{safe_number}.html"
        pdf_path = output_dir / f"faktura_{safe_number}.pdf"
        if html_path.exists() or pdf_path.exists():
            raise ValueError("Plik o tym numerze już istnieje. Wybierz inny numer faktury.")
        html_path.write_text(rendered_faktura, encoding="utf-8")
        HTML(string=rendered_faktura, base_url=str(BASE_DIR)).write_pdf(str(pdf_path))
        return pdf_path

    def generate_invoice(self):
        pdf_path = self.entry_pdf_path.get()
        if not pdf_path:
            messagebox.showerror("Błąd", "Proszę wybrać plik PDF.")
            return
        try:
            order_number, vehicle_number, amount_netto, currency, element1, element2, date_of_sale, formatted_date = self.extract_invoice_data(
                pdf_path)
            if not order_number or amount_netto is None or not currency or date_of_sale is None:
                raise ValueError("Nie odczytano numeru zlecenia, kwoty, waluty lub daty sprzedaży.")
            currency = currency.upper()
            exchange_rate_message = None
            if currency != "PLN":
                exchange_rate_message = self.get_exchange_rate(currency, date_of_sale)
                if exchange_rate_message is None:
                    raise ValueError("Nie udało się pobrać kursu NBP dla wybranej daty.")
            klient = self.config["klient"]
            numer_faktury = self.entry_invoice_number.get()
            if not numer_faktury:
                messagebox.showerror("Błąd", "Proszę wprowadzić numer faktury.")
                return

            # Pobranie daty wystawienia z GUI i walidacja
            data_wystawienia = self.entry_invoice_date.get()
            try:
                datetime.strptime(data_wystawienia, '%d-%m-%Y')
            except ValueError:
                messagebox.showerror("Błąd", "Niepoprawny format daty. Użyj DD-MM-YYYY.")
                return

            miejsce_wystawienia = self.config["miejsce_wystawienia"]
            data_sprzedazy = formatted_date
            service_name = f"Usługa transportowa, {order_number}, {element1} - {element2}, {vehicle_number}"
            stawka_vat_procent = self.slider_vat.get()
            amount_brutto = amount_netto * (1 + stawka_vat_procent / 100)
            pozycje = [
                {
                    "lp": "1",
                    "nazwa": service_name,
                    "jm": "usł.",
                    "ilosc": 1,
                    "cena_netto": amount_netto,
                    "wartosc_netto": amount_netto,
                    "stawka_vat": f"{stawka_vat_procent}%",
                    "kwota_vat": amount_brutto - amount_netto,
                    "wartosc_brutto": amount_brutto,
                    "waluta": currency
                }
            ]
            pdf_path = self.generuj_fakture(numer_faktury, data_wystawienia, klient, pozycje, miejsce_wystawienia, data_sprzedazy,
                                 exchange_rate_message, stawka_vat_procent, currency)
            messagebox.showinfo("Sukces", f"Zapisano dokument:\n{pdf_path}")
        except Exception as e:
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas przetwarzania pliku PDF: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    try:
        config = load_config()
    except (OSError, ValueError) as error:
        messagebox.showerror("Błąd konfiguracji", str(error), parent=root)
        root.destroy()
    else:
        app = InvoiceGeneratorApp(root, config)
        root.deiconify()
        root.mainloop()

