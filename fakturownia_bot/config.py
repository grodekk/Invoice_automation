import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"


def load_config():
    if not CONFIG_PATH.is_file():
        raise ValueError("Brak config.json.")

    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Niepoprawny config.json: wiersz {error.lineno}, kolumna {error.colno}."
        ) from error

    if not isinstance(config, dict):
        raise ValueError("config.json musi zawierać obiekt JSON.")

    domain = config.get("domain")

    if not isinstance(domain, str) or not domain.strip():
        raise ValueError("Uzupełnij domain w config.json.")

    config["domain"] = domain.strip()

    buyer = config.get("buyer")
    required_fields = ("name", "nip", "address", "city", "country")

    if not isinstance(buyer, dict):
        raise ValueError("Brak sekcji buyer w config.json.")

    for field in required_fields:
        value = buyer.get(field)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Uzupełnij buyer.{field} w config.json.")

    return config