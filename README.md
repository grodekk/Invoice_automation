# Invoice Automation

Program automatyzujący wystawianie faktur na podstawie zleceń transportowych PDF. Powstał na potrzeby mojej firmy transportowej, aby ograniczyć ręczne przepisywanie danych i usprawnić fakturowanie.

Projekt obsługuje zlecenia jednego kontrahenta korzystającego ze stałego szablonu. Dlatego zastosowałem bezpośredni odczyt warstwy tekstowej PDF i parsowanie danych, bez OCR.

Pierwsza wersja programu generowała faktury lokalnie jako HTML/PDF. Wraz z potrzebą obsługi KSeF powstała druga wersja, tworząca faktury przez API Fakturowni. Fakturownia odpowiada następnie za obsługę KSeF.

## Wersje i technologie

| Katalog            | Przeznaczenie                                                                                                                                            |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `invoice_local/`   | Pojedyncze zlecenie, lokalne generowanie HTML/PDF, obliczenia i pobieranie kursu NBP. Można uruchomić na danych demonstracyjnych bez konta w Fakturowni. |
| `fakturownia_bot/` | Przetwarzanie folderu zleceń, tworzenie faktur przez API Fakturowni, numeracja oraz lokalna historia przetworzonych zleceń.                              |
| `examples/`        | Przykładowe zlecenie z fikcyjnymi danymi.                                                                                                                |

**Technologie:** Python, Tkinter, PyPDF2, Requests, Jinja2, WeasyPrint, num2words, API NBP oraz API Fakturowni.

Kod został podzielony na osobne moduły odpowiedzialne m.in. za GUI, parsowanie danych, konfigurację, obliczenia i obsługę faktur.

## Instalacja — Windows / PowerShell

Wymagany jest **Python 3.10+ w wersji 64-bit z Tkinter**.

### 1. Pobranie repozytorium

Przez Git:

```powershell
git clone https://github.com/grodekk/Invoice_automation.git
cd Invoice_automation
```

Alternatywnie wybierz na GitHubie **Code → Download ZIP**, rozpakuj archiwum i otwórz PowerShell w głównym katalogu projektu — obok `requirements.txt`.

### 2. Utworzenie środowiska i instalacja zależności

Sprawdź instalację Pythona:

```powershell
py --version
```

Utwórz środowisko wirtualne:

```powershell
py -m venv .venv
```

Zainstaluj zależności:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Poniższe polecenia korzystają bezpośrednio z interpretera znajdującego się w `.venv`, dlatego aktywacja środowiska nie jest wymagana.

Wszystkie polecenia uruchamiaj z głównego katalogu projektu.

## WeasyPrint — tylko dla wersji lokalnej

Wersja lokalna wykorzystuje WeasyPrint do generowania PDF na podstawie szablonu HTML/CSS.

Na Windowsie WeasyPrint wymaga dodatkowych bibliotek systemowych Pango, których nie instaluje `pip`.

Zainstaluj MSYS2, a następnie w terminalu **MSYS2 UCRT64** wykonaj:

```bash
pacman -S mingw-w64-ucrt-x86_64-pango
```

Następnie wróć do PowerShell i ustaw katalog zawierający wymagane biblioteki. Dla domyślnej instalacji MSYS2:

```powershell
$env:WEASYPRINT_DLL_DIR = "C:\msys64\ucrt64\bin"
$env:WEASYPRINT_DLL_DIRECTORIES = $env:WEASYPRINT_DLL_DIR
```

Sprawdź instalację:

```powershell
.\.venv\Scripts\python.exe -m weasyprint --info
```

Pierwszą zmienną wykorzystuje aplikacja, drugą WeasyPrint. Jeśli MSYS2 został zainstalowany w innym miejscu, dostosuj ścieżkę.

Program uruchamiaj w tym samym terminalu PowerShell, w którym ustawiono zmienne środowiskowe.

## Uruchomienie wersji lokalnej

Do repozytorium dołączono przykładowe zlecenie z fikcyjnymi danymi, dzięki czemu wersję lokalną można przetestować bez konta w Fakturowni.

`invoice_local/config.json` zawiera dane sprzedawcy, nabywcy, rachunki bankowe, miejsce wystawienia oraz termin płatności. Do demonstracji można pozostawić dołączone fikcyjne wartości.

Uruchom aplikację:

```powershell
.\.venv\Scripts\python.exe -m invoice_local.main
```

Następnie:

1. Wskaż plik `examples/zlecenie_demo.pdf`.
2. Wpisz numer faktury, np. `01/01/2026`.
3. Wpisz stawkę VAT(%) np. `23`.
4. Podaj datę wystawienia w formacie `DD-MM-YYYY`.
5. Kliknij **Generuj fakturę**.

Wygenerowane pliki HTML i PDF znajdziesz w:

```text
invoice_local/output/
```

Pobranie kursu NBP wymaga połączenia z internetem.

## Uruchomienie wersji z Fakturownią

Wymagane jest konto w Fakturowni z dostępem do API oraz połączenie z internetem.

### 1. Konfiguracja

Uzupełnij:

```text
fakturownia_bot/config.json
```

Pole `domain` zawiera nazwę konta Fakturowni bez `https://` i `.fakturownia.pl`.

Sekcja `buyer` zawiera dane nabywcy. Dane sprzedawcy oraz rachunki bankowe są konfigurowane bezpośrednio w Fakturowni.

### 2. Token API

Token API można pobrać w Fakturowni:

**Ustawienia → Ustawienia konta → Integracja → Kod autoryzacyjny API**

Ustaw token jako zmienną środowiskową w PowerShell:

```powershell
$env:FAKTUROWNIA_API_TOKEN = "TU_WKLEJ_SWOJ_TOKEN"
```

Następnie, w tym samym terminalu, uruchom aplikację:

```powershell
.\.venv\Scripts\python.exe -m fakturownia_bot.main
```

### 3. Przetwarzanie zleceń

W aplikacji:

1. wybierz folder zawierający zlecenia PDF,
2. wybierz miesiąc numeracji,
3. podaj numer początkowy faktury,
4. kliknij **START**.

Program przetwarza wszystkie PDF-y bezpośrednio w wybranym folderze i nadaje fakturom numery w formacie:

```text
NN/MM/RRRR
```

Wybrany miesiąc służy do numeracji faktur — nie filtruje zleceń.

Rok oraz data wystawienia są bieżące.

Lokalny plik:

```text
invoice_index.json
```

Przechowuje historię przetworzonych zleceń i pomaga wykrywać próby ponownego przetworzenia tego samego dokumentu.

GUI pokazuje wynik operacji oraz ewentualne błędy.

> **Uwaga:** przycisk **START** tworzy rzeczywiste faktury na wskazanym koncie Fakturowni.

Program tworzy faktury przez API Fakturowni. Dalszą obsługę oraz wysyłkę dokumentów do KSeF realizuje Fakturownia — aplikacja nie komunikuje się bezpośrednio z KSeF.

## Założenia i ograniczenia

* Parsery są dopasowane do konkretnego szablonu PDF zawierającego warstwę tekstową. Inne układy dokumentów wymagają dostosowania parsera.
* Wersja z Fakturownią obsługuje faktury w EUR z przeliczeniem na PLN oraz terminem płatności 45 dni.
* Reguła w `tax.py` zwraca VAT `0` dla trasy UE → poza UE. W pozostałych przypadkach, również przy braku rozpoznanego kraju, stosowana jest wartość `23`.
* Pobieranie kursu NBP jest realizowane przez wersję lokalną. W wersji z Fakturownią przeliczenie kursu powierzono Fakturowni.
* Publikowane konfiguracje oraz przykładowe dokumenty zawierają wyłącznie fikcyjne dane.
