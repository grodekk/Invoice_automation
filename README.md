# Invoice Automation

Program automatyzujący wystawianie faktur na podstawie zleceń transportowych PDF. Powstał na potrzeby mojej firmy transportowej, aby ograniczyć ręczne przepisywanie danych i usprawnić fakturowanie.

Projekt obsługuje zlecenia jednego kontrahenta, korzystającego ze stałego szablonu. Dlatego zastosowałem bezpośredni odczyt warstwy tekstowej PDF i parsowanie danych, bez OCR.

Pierwsza wersja generowała lokalnie faktury HTML/PDF po wskazaniu zlecenia oraz podaniu numeru faktury, VAT i daty wystawienia. Odczytywała dane transportu, wykonywała obliczenia i pobierała kurs NBP na podstawie daty sprzedaży.

Przez potrzebę obsługi KSeF zdecydowałem się na integrację z Fakturownią. Program tworzy faktury przez API, pozostawiając serwisowi obsługę uwierzytelniania, certyfikatów i wysyłki do KSeF. Dodałem przetwarzanie całego folderu zleceń, numerację oraz dobór VAT według krajów transportu. Pobieranie kursu NBP w tej wersji powierzono Fakturowni.

## Wersje i technologie

| Katalog | Przeznaczenie |
| --- | --- |
| `invoice_local/` | Pojedyncze zlecenie, lokalny HTML/PDF, obliczenia i kurs NBP. Można uruchomić na danych demonstracyjnych bez konta w Fakturowni. |
| `fakturownia_bot/` | Folder zleceń, tworzenie faktur przez API, numeracja i lokalna historia przetworzonych zleceń. |
| `examples/` | Przykładowe zlecenie z fikcyjnymi danymi. |

**Technologie:** Python, Tkinter, PyPDF2, Requests, Jinja2, WeasyPrint, num2words; API NBP i Fakturowni. Kod podzielono na moduły GUI, parsera, konfiguracji i obsługi faktur.

## Instalacja (Windows / PowerShell)

Zainstaluj Python 3.10+ w wersji 64-bit z Tkinter. Pobierz repozytorium i otwórz PowerShell w jego głównym katalogu, obok `requirements.txt`:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Poniższe polecenia korzystają bezpośrednio z `.venv`, więc nie trzeba aktywować środowiska. Uruchamiaj je z głównego katalogu projektu.

### WeasyPrint - tylko dla wersji lokalnej

WeasyPrint wymaga bibliotek systemowych Pango, których nie instaluje `pip`. Zainstaluj [MSYS2](https://www.msys2.org/), a następnie w terminalu **MSYS2 UCRT64** wykonaj:

```bash
pacman -S mingw-w64-ucrt-x86_64-pango
```

Wróć do PowerShell i ustaw katalog bibliotek. Dla domyślnej instalacji MSYS2:

```powershell
$env:WEASYPRINT_DLL_DIR = "C:\msys64\ucrt64\bin"
$env:WEASYPRINT_DLL_DIRECTORIES = $env:WEASYPRINT_DLL_DIR
.\.venv\Scripts\python.exe -m weasyprint --info
```

Pierwszą zmienną odczytuje aplikacja, drugą WeasyPrint. Dostosuj ścieżkę do swojej instalacji i uruchom program w tym samym terminalu. Instrukcje dla innych systemów i rozwiązywanie problemów: [dokumentacja WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation).

## Uruchomienie lokalne i przykład demonstracyjny

`invoice_local/config.json` zawiera dane sprzedawcy, nabywcy, rachunki bankowe, miejsce wystawienia i termin płatności. Do demonstracji pozostaw dołączone fikcyjne wartości.

```powershell
.\.venv\Scripts\python.exe -m invoice_local.main
```

1. Wskaż `examples/zlecenie_demo.pdf`.
2. Wpisz numer, np. `DEMO/01/2026`, VAT `23` i datę wystawienia w formacie `DD-MM-YYYY`. VAT jest tu wartością do demonstracji.
3. Kliknij **Generuj fakturę**. Wyniki znajdziesz w `invoice_local/output/` jako HTML i PDF.

Przykład: zlecenie `ZL26/08/0001`, kwota netto `950 EUR`, data sprzedaży `20-08-2026`. Przy ponownym generowaniu użyj innego numeru faktury. Pobranie kursu NBP wymaga internetu.

## Uruchomienie integracji z Fakturownią

Wymagane jest konto z dostępem do API oraz połączenie z internetem.

1. Uzupełnij `fakturownia_bot/config.json`: `domain` to nazwa konta bez `https://` i `.fakturownia.pl`, a `buyer` zawiera dane nabywcy. Dane sprzedawcy i rachunki ustaw w Fakturowni.
2. Pobierz token z **Ustawienia → Ustawienia konta → Integracja → Kod autoryzacyjny API** ([dokumentacja API](https://github.com/fakturownia/API#api-token)). Ustaw go w PowerShell i uruchom program w tym samym oknie:

```powershell
$env:FAKTUROWNIA_API_TOKEN = "TU_WKLEJ_SWOJ_TOKEN"
.\.venv\Scripts\python.exe -m fakturownia_bot.main
```

3. Wybierz folder ze zleceniami PDF, miesiąc numeracji i numer początkowy, następnie kliknij **START**.

Program przetwarza PDF-y bezpośrednio w wybranym folderze i nadaje numery w formacie `NN/MM/RRRR`. Miesiąc służy do numeracji, nie filtruje zleceń. Rok i data wystawienia są bieżące. Historia `invoice_index.json` pomaga wykrywać ponownie przetwarzane zlecenia, a GUI pokazuje wynik operacji i błędy.

**START tworzy rzeczywiste faktury na wskazanym koncie.** Dalszą wysyłkę do KSeF obsługujesz w Fakturowni; program nie wysyła faktur bezpośrednio do KSeF.

## Zakres działania

- Parsery są dopasowane do konkretnego szablonu PDF z warstwą tekstową. Inne układy oraz skany wymagają dostosowania odczytu.
- Wersja API używa EUR, przeliczenia na PLN i terminu płatności 45 dni. Nabywca z konfiguracji jest wspólny dla przetwarzanej partii.
- Reguła w `tax.py` zwraca `0` dla trasy UE → poza UE, a w pozostałych przypadkach, także przy braku rozpoznanego kraju, `23`.
- Publikowane konfiguracje i przykład zawierają fikcyjne dane. Tokenów, rzeczywistych danych wpisanych do konfiguracji, zleceń, wygenerowanych faktur ani historii nie należy dodawać do commitów.
