from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ParsedOrder:
    order_number: Optional[str]
    net_amount: Optional[float]
    route_from: Optional[str]
    route_to: Optional[str]
    sale_date: datetime
    vehicle: Optional[str]


@dataclass
class InvoiceData:
    number: str
    issue_date: str
    sale_date: str
    order: ParsedOrder
    vat: int
    gross_amount: float
    service_name: str
