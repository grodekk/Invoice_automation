import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"

def load_config():
    if not CONFIG_PATH.is_file():
        raise ValueError(
            "Brak config.json. Przywróć plik z repozytorium."
        )

    try:
        config = json.loads(
            CONFIG_PATH.read_text(encoding="utf-8-sig")
        )

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Niepoprawny config.json: wiersz {error.lineno}, "
            f"kolumna {error.colno}. Sprawdź przecinki i cudzysłowy."
        ) from error

    if not isinstance(config, dict):
        raise ValueError("config.json musi zawierać obiekt JSON.")

    required = {
        "sprzedawca": (
            "nazwa",
            "adres",
            "miasto",
            "nip",
            "konto_pln",
            "konto_eur",
        ),
        "klient": (
            "nazwa",
            "adres",
            "miasto",
            "NIP",
        ),
    }

    for section, fields in required.items():
        if not isinstance(config.get(section), dict):
            raise ValueError(f"Brak sekcji {section} w config.json.")

        for field in fields:
            value = config[section].get(field)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Uzupełnij {section}.{field} w config.json."
                )

    place = config.get("miejsce_wystawienia")

    if not isinstance(place, str) or not place.strip():
        raise ValueError(
            "Uzupełnij miejsce_wystawienia w config.json."
        )

    days = config.get("termin_platnosci_dni")

    if type(days) is not int or days < 0:
        raise ValueError(
            "termin_platnosci_dni musi być liczbą całkowitą >= 0."
        )

    return config