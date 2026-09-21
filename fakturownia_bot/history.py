import json
from pathlib import Path


class InvoiceHistory:
    def __init__(self, path):
        self.path = Path(path)

    def entries(self):
        if not self.path.exists():
            return []
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Nie można odczytać historii {self.path}: {error}") from error

    def contains_order(self, order):
        return any(row.get("order") == order for row in self.entries())

    def add(self, order, invoice, sale_date, route_from, route_to, file_name, vehicle):
        data = self.entries()
        data.append(
            {
                "order": order,
                "invoice": invoice,
                "route": f"{route_from} → {route_to}" if route_from or route_to else None,
                "sale_date": sale_date.strftime("%Y-%m-%d"),
                "file": file_name,
                "vehicle": vehicle,
            }
        )
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
