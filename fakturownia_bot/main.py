import os
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

from .fakturownia_client import FakturowniaClient
from .config import load_config
from .history import InvoiceHistory
from .models import InvoiceData
from .parser import extract_order_data
from .tax import get_vat


BASE_DIR = Path(__file__).resolve().parent
HISTORY_PATH = BASE_DIR / "invoice_index.json"


def create_invoice(order, number, issue_date):
    if not order.order_number or order.net_amount is None or order.net_amount <= 0:
        raise ValueError("Nieprawidłowe dane zlecenia: brak numeru lub kwoty netto.")

    vat = get_vat(order.route_from, order.route_to)
    gross_amount = order.net_amount * (1 + vat / 100)

    return InvoiceData(
        number=number,
        issue_date=issue_date,
        sale_date=order.sale_date.strftime("%Y-%m-%d"),
        order=order,
        vat=vat,
        gross_amount=gross_amount,
        service_name=f"Usługa transportowa, {order.order_number}",
    )


def process_pdf(path, invoice_number, client, history):
    order = extract_order_data(path)

    if history.contains_order(order.order_number):
        raise ValueError("Zlecenie jest już zapisane w historii.")

    issue_date = datetime.now().strftime("%Y-%m-%d")
    invoice = create_invoice(order, invoice_number, issue_date)

    client.create_invoice(invoice)
    history.add(
        order=order.order_number,
        invoice=invoice.number,
        sale_date=order.sale_date,
        route_from=order.route_from,
        route_to=order.route_to,
        file_name=path.name,
        vehicle=order.vehicle,
    )


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Faktury BOT")
        self._build_form()

    def _build_form(self):
        tk.Label(self.root, text="Folder PDF:").grid(
            row=0,
            column=0,
        )

        self.folder_entry = tk.Entry(self.root, width=40)
        self.folder_entry.grid(row=0, column=1)

        tk.Button(
            self.root,
            text="Wybierz",
            command=self.select_folder,
        ).grid(row=0, column=2)

        tk.Label(self.root, text="Miesiąc (MM):").grid(
            row=1,
            column=0,
        )

        self.month_entry = tk.Entry(self.root)
        self.month_entry.insert(0, datetime.now().strftime("%m"))
        self.month_entry.grid(row=1, column=1)

        tk.Label(self.root, text="Numer początkowy:").grid(
            row=2,
            column=0,
        )

        self.start_number_entry = tk.Entry(self.root)
        self.start_number_entry.insert(0, "1")
        self.start_number_entry.grid(row=2, column=1)

        tk.Button(
            self.root,
            text="START",
            command=self.run,
        ).grid(row=3, column=1)

    def select_folder(self):
        folder = filedialog.askdirectory()

        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)

    def read_form(self):
        folder = Path(self.folder_entry.get())
        token = os.getenv("FAKTUROWNIA_API_TOKEN")

        if not folder.is_dir():
            raise ValueError("Wybierz prawidłowy folder PDF.")

        if not token:
            raise ValueError("Ustaw zmienną FAKTUROWNIA_API_TOKEN.")

        try:
            start_number = int(self.start_number_entry.get())

        except ValueError as error:
            raise ValueError("Podaj prawidłowy numer początkowy.") from error

        month = self.month_entry.get().strip()

        if not month.isdigit() or not 1 <= int(month) <= 12:
            raise ValueError("Miesiąc musi mieć wartość od 01 do 12.")

        return folder, token, int(month), start_number

    def run(self):
        try:
            config = load_config()
            folder, token, month, invoice_number = self.read_form()

            domain = config.get("domain", "").strip()

            if not domain:
                raise ValueError("Brak pola domain w config.json.")

        except (OSError, ValueError) as error:
            messagebox.showerror("Błąd konfiguracji", str(error))
            return

        try:
            history = InvoiceHistory(HISTORY_PATH)
            client = FakturowniaClient(domain, token, config["buyer"])

        except (OSError, ValueError, KeyError) as error:
            messagebox.showerror("Błąd uruchomienia", str(error))
            return

        year = datetime.now().year
        successes = []
        errors = []

        pdf_files = sorted(folder.glob("*.pdf"))

        if not pdf_files:
            messagebox.showwarning(
                "Brak plików",
                "Wybrany folder nie zawiera żadnych plików PDF.",
            )
            return

        for path in pdf_files:
            number = f"{invoice_number:02d}/{month:02d}/{year}"

            try:
                process_pdf(path, number, client, history)
                successes.append(f"{path.name} → {number}")
                invoice_number += 1

            except Exception as error:
                errors.append(f"{path.name}: {error}")

        self.show_result(successes, errors)

    @staticmethod
    def show_result(successes, errors):
        if errors:
            title = "Zakończono z błędami"
            message = f"Wystawiono poprawnie: {len(successes)}\nPominięte lub błędne: {len(errors)}\n\n"

            if successes:
                message += "Wystawione faktury:\n"
                message += "\n".join(f"  ✓ {item}" for item in successes)
                message += "\n\n"

            message += "Błędy:\n"
            message += "\n".join(f"  ✗ {item}" for item in errors)

            messagebox.showwarning(title, message)

        else:
            title = "Zakończono poprawnie"
            message = f"Wystawiono poprawnie: {len(successes)}\n\n" + "\n".join(f"  ✓ {item}" for item in successes)

            messagebox.showinfo(title, message)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
