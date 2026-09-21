import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox

from .calculator import build_position
from .config import load_config
from .html_generator import generate_invoice
from .nbp_client import get_exchange_rate
from .parser import extract_order_data



class InvoiceGeneratorApp:
    def __init__(self, root, config):
        self.root = root
        self.config = config

        self.root.title("Generator faktur")
        self.root.resizable(False, False)

        self._build_form()

    def _build_form(self):
        frame = tk.Frame(self.root, padx=10, pady=10)
        frame.pack()

        tk.Label(frame, text="Plik PDF:").grid(
            row=0,
            column=0,
            sticky=tk.E,
            pady=4,
        )

        self.pdf_entry = tk.Entry(frame, width=55)
        self.pdf_entry.grid(row=0, column=1, pady=4)

        tk.Button(
            frame,
            text="Wybierz",
            command=self.select_pdf,
        ).grid(row=0, column=2, padx=5, pady=4)

        tk.Label(frame, text="Stawka VAT (%):").grid(
            row=1,
            column=0,
            sticky=tk.E,
            pady=4,
        )

        self.vat_entry = tk.Entry(frame, width=10)
        self.vat_entry.insert(0, "23")
        self.vat_entry.grid(row=1, column=1, sticky=tk.W, pady=4)

        tk.Label(frame, text="Numer faktury:").grid(
            row=2,
            column=0,
            sticky=tk.E,
            pady=4,
        )

        self.invoice_number_entry = tk.Entry(frame, width=20)
        self.invoice_number_entry.grid(
            row=2,
            column=1,
            sticky=tk.W,
            pady=4,
        )

        tk.Label(frame, text="Data wystawienia:").grid(
            row=3,
            column=0,
            sticky=tk.E,
            pady=4,
        )

        self.issue_date_entry = tk.Entry(frame, width=15)
        self.issue_date_entry.insert(
            0,
            datetime.now().strftime("%d-%m-%Y"),
        )
        self.issue_date_entry.grid(
            row=3,
            column=1,
            sticky=tk.W,
            pady=4,
        )

        tk.Button(
            frame,
            text="Generuj fakturę",
            command=self.generate,
        ).grid(
            row=4,
            column=1,
            pady=15,
        )

    def select_pdf(self):
        pdf_path = filedialog.askopenfilename(
            filetypes=[("Pliki PDF", "*.pdf")],
        )

        if pdf_path:
            self.pdf_entry.delete(0, tk.END)
            self.pdf_entry.insert(0, pdf_path)

    def generate(self):
        pdf_path = self.pdf_entry.get().strip()
        invoice_number = self.invoice_number_entry.get().strip()
        issue_date = self.issue_date_entry.get().strip()

        if not pdf_path:
            messagebox.showerror(
                "Błąd",
                "Wybierz plik PDF.",
            )
            return

        if not invoice_number:
            messagebox.showerror(
                "Błąd",
                "Podaj numer faktury.",
            )
            return

        try:
            vat_rate = int(self.vat_entry.get())

        except ValueError:
            messagebox.showerror(
                "Błąd",
                "Stawka VAT musi być liczbą całkowitą.",
            )
            return

        if not 0 <= vat_rate <= 100:
            messagebox.showerror(
                "Błąd",
                "Stawka VAT musi być między 0 a 100.",
            )
            return

        try:
            datetime.strptime(issue_date, "%d-%m-%Y")

        except ValueError:
            messagebox.showerror(
                "Błąd",
                "Niepoprawna data. Użyj formatu DD-MM-YYYY.",
            )
            return

        try:
            order_data = extract_order_data(pdf_path)

            missing_fields = []

            if not order_data["order_number"]:
                missing_fields.append("numer zlecenia")

            if order_data["amount_netto"] is None:
                missing_fields.append("kwota netto")

            if not order_data["currency"]:
                missing_fields.append("waluta")

            if order_data["sale_date"] is None:
                missing_fields.append("data sprzedaży")

            if missing_fields:
                raise ValueError(
                    "Nie odczytano następujących danych ze zlecenia:\n"
                    + "\n".join(f"• {field}" for field in missing_fields)
                )

            currency = order_data["currency"].upper()
            exchange_rate = None

            if currency != "PLN":
                exchange_rate = get_exchange_rate(
                    currency,
                    order_data["sale_date"],
                )

                if exchange_rate is None:
                    raise ValueError(
                        "Nie udało się pobrać kursu NBP "
                        "dla daty sprzedaży."
                    )

            position = build_position(
                order_data,
                vat_rate,
            )

            pdf_output_path = generate_invoice(
                invoice_number=invoice_number,
                issue_date=issue_date,
                buyer=self.config["klient"],
                positions=[position],
                place_of_issue=self.config["miejsce_wystawienia"],
                sale_date=order_data["formatted_date"],
                exchange_rate=exchange_rate,
                vat_rate=vat_rate,
                currency=currency,
                seller=self.config["sprzedawca"],
                payment_days=self.config["termin_platnosci_dni"],
            )

            messagebox.showinfo(
                "Sukces",
                f"Zapisano fakturę:\n{pdf_output_path}",
            )

        except Exception as error:
            messagebox.showerror(
                "Błąd",
                f"Wystąpił błąd podczas generowania faktury:\n\n{error}",
            )


def main():
    root = tk.Tk()

    try:
        config = load_config()

    except (OSError, ValueError) as error:
        messagebox.showerror(
            "Błąd konfiguracji",
            str(error),
            parent=root,
        )
        root.destroy()
        return

    InvoiceGeneratorApp(root, config)
    root.mainloop()


if __name__ == "__main__":
    main()