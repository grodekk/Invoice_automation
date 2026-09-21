import re


EU_CODES = {
    "PL", "DE", "FR", "IT", "ES", "NL", "BE", "CZ", "SK",
    "AT", "HU", "SE", "DK", "FI", "IE", "PT", "RO", "BG",
    "HR", "SI", "LT", "LV", "EE", "GR", "CY", "LU", "MT",
}


def get_vat(route_from, route_to):
    first = re.search(r"[A-Z]{2}", route_from or "")
    second = re.search(r"[A-Z]{2}", route_to or "")
    if not first or not second:
        return 23
    return 0 if first.group(0) in EU_CODES and second.group(0) not in EU_CODES else 23
