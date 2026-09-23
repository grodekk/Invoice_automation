# Invoice Automation

[Wersja polska](README.md)

Application for automating invoice creation based on transport order PDF files. It was developed for use in my transport company to reduce manual data entry and streamline the invoicing process.

The project handles orders from one contractor using a fixed document template. For this reason, the application reads the PDF text layer directly and parses the required data without using OCR.

The first version generated invoices locally as HTML/PDF files. When KSeF support became necessary, a second version was created to generate invoices through the Fakturownia API. Fakturownia then handles further KSeF processing.

The GUI is in Polish because the application was developed for use in a Polish transport company.

## Versions and technologies

| Directory          | Purpose                                                                                                                                                                            |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `invoice_local/`   | Processes a single order, generates HTML/PDF invoices locally, performs calculations and retrieves NBP exchange rates. Can be tested with demo data without a Fakturownia account. |
| `fakturownia_bot/` | Processes a folder of transport orders, creates invoices through the Fakturownia API, handles invoice numbering and stores a local history of processed orders.                    |
| `examples/`        | Example transport order containing fictional data.                                                                                                                                 |

**Technologies:** Python, Tkinter, PyPDF2, Requests, Jinja2, WeasyPrint, num2words, NBP API and Fakturownia API.

The code is divided into separate modules responsible for the GUI, data parsing, configuration, calculations and invoice handling.

## Installation — Windows / PowerShell

Requires **Python 3.10+ 64-bit with Tkinter**.

### 1. Clone the repository

Using Git:

```powershell
git clone https://github.com/grodekk/Invoice_automation.git
cd Invoice_automation
```

Alternatively, select **Code → Download ZIP** on GitHub, extract the archive and open PowerShell in the project root directory, next to `requirements.txt`.

### 2. Create a virtual environment and install dependencies

Check the Python installation:

```powershell
py --version
```

Create a virtual environment:

```powershell
py -m venv .venv
```

Install the dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The commands below use the Python interpreter located directly inside `.venv`, so activating the virtual environment is not required.

Run all commands from the project root directory.

## WeasyPrint — local version only

The local version uses WeasyPrint to generate PDF files from an HTML/CSS template.

On Windows, WeasyPrint requires additional Pango system libraries that are not installed through `pip`.

Install MSYS2 and then run the following command in the **MSYS2 UCRT64** terminal:

```bash
pacman -S mingw-w64-ucrt-x86_64-pango
```

Then return to PowerShell and configure the directory containing the required libraries. For the default MSYS2 installation:

```powershell
$env:WEASYPRINT_DLL_DIR = "C:\msys64\ucrt64\bin"
$env:WEASYPRINT_DLL_DIRECTORIES = $env:WEASYPRINT_DLL_DIR
```

Verify the installation:

```powershell
.\.venv\Scripts\python.exe -m weasyprint --info
```

The first environment variable is used by the application and the second one by WeasyPrint. If MSYS2 was installed in a different location, adjust the path accordingly.

Run the application from the same PowerShell session in which the environment variables were set.

## Running the local version

The repository includes an example transport order with fictional data, so the local version can be tested without a Fakturownia account.

`invoice_local/config.json` contains seller and buyer details, bank accounts, place of issue and payment terms. The included fictional values can be used for demonstration purposes.

Run the application:

```powershell
.\.venv\Scripts\python.exe -m invoice_local.main
```

Then:

1. Select `examples/zlecenie_demo.pdf`.
2. Enter an invoice number, for example `01/01/2026`.
3. Enter the VAT rate (%), for example `23`.
4. Enter the issue date in `DD-MM-YYYY` format.
5. Click **Generuj fakturę**.

Generated HTML and PDF files will be saved in:

```text
invoice_local/output/
```

Retrieving the NBP exchange rate requires an internet connection.

## Running the Fakturownia version

A Fakturownia account with API access and an internet connection are required.

### 1. Configuration

Edit:

```text
fakturownia_bot/config.json
```

The `domain` field contains the Fakturownia account name without `https://` and `.fakturownia.pl`.

The `buyer` section contains buyer details. Seller information and bank accounts are configured directly in Fakturownia.

### 2. API token

The API token can be obtained in Fakturownia:

**Ustawienia → Ustawienia konta → Integracja → Kod autoryzacyjny API**

Set the token as an environment variable in PowerShell:

```powershell
$env:FAKTUROWNIA_API_TOKEN = "YOUR_API_TOKEN"
```

Then, in the same terminal, run the application:

```powershell
.\.venv\Scripts\python.exe -m fakturownia_bot.main
```

### 3. Processing transport orders

In the application:

1. select the folder containing the PDF transport orders,
2. select the month used for invoice numbering,
3. enter the starting invoice number,
4. click **START**.

The application processes all PDF files located directly in the selected folder and assigns invoice numbers in the following format:

```text
NN/MM/YYYY
```

The selected month is used only for invoice numbering — it does not filter transport orders.

The year and invoice issue date are taken from the current date.

The local file:

```text
invoice_index.json
```

stores the history of processed orders and helps detect attempts to process the same document again.

The GUI displays the result of each operation and any errors.

> **Warning:** clicking **START** creates real invoices in the configured Fakturownia account.

The application creates invoices through the Fakturownia API. Further processing and submission to KSeF are handled by Fakturownia — the application does not communicate with KSeF directly.

## Assumptions and limitations

* The parsers are designed for a specific PDF template containing a text layer. Other document layouts require adjustments to the parser.
* The Fakturownia version supports invoices in EUR with conversion to PLN and a 45-day payment term.
* The rule in `tax.py` returns VAT `0` for EU → non-EU routes. In all other cases, including situations where the country cannot be identified, the value `23` is used.
* NBP exchange rates are retrieved by the local version. In the Fakturownia version, currency conversion is handled by Fakturownia.
* Published configuration files and example documents contain fictional data only.
