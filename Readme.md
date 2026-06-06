# Pipeline Tariff Extraction Automation Framework (Work In Progress - 50% Completed)

## Project Overview

This project is a **Python-based web automation framework** developed to automate the extraction of tariff-related documents from a web portal for multiple oil pipelines.

The automation process uses **Selenium with Page Object Model (POM)** architecture to navigate through a tariff website, search for pipeline-specific tariff information, and download the latest available files into structured folders.

The project is currently **50% completed**.

### Current Completion Status: 50%

✅ **Completed**
- Website automation using Selenium
- Page Object Model (POM) implementation
- Modular framework design
- Pipeline input handling from files
- Dropdown selection automation
- Search and navigation flow
- Dynamic handling of unavailable pipelines
- Multi-tab navigation
- Latest tariff file selection
- Automated file download
- Pipeline-wise folder organization
- Logging implementation
- Excel tracker/report generation
- Environment variable configuration using `.env`

🚧 **In Progress**
- PDF table extraction using `pdfplumber`
- Data transformation and cleaning
- CSV generation from extracted tables
- Validation and error recovery enhancements
- End-to-end reporting

---

## Business Problem

Manually downloading tariff files for multiple pipelines is repetitive and time-consuming.

This framework automates:

1. Opening the tariff website
2. Selecting the **Oil** category
3. Reading pipeline names from input files
4. Searching pipeline tariffs
5. Handling unavailable pipelines
6. Navigating tariff pages
7. Selecting the latest tariff document
8. Downloading files automatically
9. Storing files in pipeline-specific folders

Future enhancement includes:

10. Extracting tabular data from downloaded PDFs  
11. Converting extracted data into CSV format for analytics

---

## Workflow

```text
Open URL
   ↓
Select "OIL" from dropdown
   ↓
Read pipeline names from input folder
   ↓
Search pipeline
   ↓
Check result
   ├── No tariff available → Skip pipeline
   └── Tariff exists
            ↓
       Open tariff page
            ↓
       Select latest tariff link
            ↓
       Download PDF
            ↓
       Save to output folder
            ↓
     (Upcoming)
       Extract PDF tables
            ↓
         Convert to CSV
```

---

## Project Architecture

This project follows a **Modular + Page Object Model (POM)** framework design.

### Folder Structure

```text
project/
│
├── data/
│   ├── input/
│   │   └── pipelines/
│   │
│   ├── output/
│   │   └── downloaded_files/
│   │
│   └── reports/
│
├── logs/
│   └── automation.log
│
├── pages/
│   ├── tariff_list_page.py
│   └── tariff_browser_page.py
│
├── src/
│   ├── selenium_operations/
│   │   ├── base_page.py
│   │   └── driver_setup.py
│   │
│   └── pdf_operations/
│
├── utils/
|   ├── helpers.py
│   ├── tracker.py
│   ├── pandas_operations.py
│   └── logfiles.py
│
├── .env
├── main.py
├── requirements.txt
└── README.md
```

---

## Tech Stack

- **Python**
- **Selenium**
- **Pandas**
- **OpenPyXL**
- **Python-dotenv**
- **Logging**
- **Page Object Model (POM)**

### Upcoming Tech

- **pdfplumber**
- **Regex**
- **CSV Processing**

---

## Features Implemented

### 1. Automated Pipeline Search
Reads pipeline names dynamically from input files and processes them one by one.

### 2. Smart Skip Logic
If the website shows:

> "Currently no pipelines available"

the framework skips the pipeline and moves to the next one instead of failing.

### 3. Latest File Selection
Automatically selects the latest tariff file available from the portal.

### 4. Automated File Download
Downloads tariff PDFs directly into pipeline-specific folders.

### 5. Logging System
Tracks execution flow, errors, and pipeline processing.

### 6. Tracker Generation
Creates execution tracking reports for processed pipelines.

---

## Environment Variables

The project uses a `.env` file to securely manage:

- URL
- XPath locators
- File paths
- Configuration settings

Example:

```env
URL=
TARIFF_PROGRAM_DROPDOWN_XPATH=
SEARCH_BUTTON_XPATH=
COMPANY_NAME_INPUT_XPATH=
```

---

## How to Run

### 1. Clone Repository

```bash
git clone <repository-url>
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create `.env` file.

### 6. Run Project

```bash
python main.py
```

---

## Current Challenges Being Solved

- Handling unavailable pipelines dynamically
- Reliable multi-tab browser automation
- Stable file downloads
- Dynamic XPath handling
- PDF table extraction challenges

---

## Planned Enhancements (Remaining 50%)

- Extract tables from downloaded PDFs using `pdfplumber`
- Clean and standardize extracted data
- Export structured CSV files
- Improve exception handling
- Add retry mechanisms
- Generate final consolidated reports
- Add automated validation checks

---

## Learning Outcome

This project demonstrates practical experience in:

- Python Automation
- Selenium Framework Development
- Page Object Model (POM)
- Browser Automation
- Dynamic Element Handling
- Logging and Reporting
- File Automation
- PDF Processing (In Progress)

---

## Author

**Kishore Kumar**

Python Automation | Data Engineering Aspirant | ETL & Automation Projects