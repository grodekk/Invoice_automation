from datetime import datetime, timedelta
import requests


class FakturowniaClient:
    def __init__(self, domain, api_token, buyer):
        self.url = f"https://{domain}.fakturownia.pl/invoices.json"
        self.api_token = api_token
        self.buyer = buyer

    def create_invoice(self, invoice):
        payload = {
            "api_token": self.api_token,
            "invoice": {
                "kind": "vat",
                "number": invoice.number,
                "sell_date": invoice.sale_date,
                "issue_date": invoice.issue_date,
                "payment_to": (datetime.strptime(invoice.issue_date, "%Y-%m-%d") + timedelta(days=45)).strftime(
                    "%Y-%m-%d"
                ),
                "currency": "EUR",
                "exchange_currency": "PLN",
                "exchange_kind": "nbp",
                "buyer_name": self.buyer["name"],
                "buyer_tax_no": self.buyer["nip"],
                "buyer_street": self.buyer["address"],
                "buyer_city": self.buyer["city"],
                "buyer_country": self.buyer["country"],
                "positions": [
                    {
                        "name": invoice.service_name,
                        "quantity": 1,
                        "tax": invoice.vat,
                        "price_net": round(invoice.order.net_amount, 2),
                        "total_price_gross": round(invoice.gross_amount, 2),
                    }
                ],
            },
        }
        response = requests.post(self.url, json=payload, timeout=30)
        if not response.ok:
            raise ValueError(f"Fakturownia odrzuciła fakturę ({response.status_code}): {response.text}")

        return response.json()
