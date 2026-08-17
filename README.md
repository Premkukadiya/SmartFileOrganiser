# 📁 Smart File Organizer & Data Processor CLI

A powerful Python command-line tool that scans directories, automatically organizes files by type and date, detects duplicate files, extracts metadata, and generates beautiful summary reports.

Built as a **Summer Internship Project (May–July 2026)**.

---

## ✨ Features

- 🔍 **Smart File Scanning** — Recursively scan directories and classify files into categories (Documents, Images, Code, Archives, Media, Data)
- 📂 **Automated Organization** — Move/copy files into a structured folder layout (`Organized/Category/Year/`)
- 🔄 **Duplicate Detection** — SHA-256 content hashing to find and remove duplicate files
- 📊 **Data Extraction** — Parse CSV files for statistics, extract image EXIF metadata, analyze text files
- 📋 **Report Generation** — Beautiful HTML, JSON, and CSV reports with charts and breakdowns
- 🛡️ **Dry-Run Mode** — Preview all changes safely before executing
- ↩️ **Undo/Rollback** — Reverse the last organize operation with a single command
- ⚙️ **Configurable** — YAML config file for custom rules, categories, and patterns

---

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/SmartFileOrganizer.git
cd SmartFileOrganizer

# Install dependencies
pip install -r requirements.txt

# (Optional) Install as a package
pip install -e .
```

### Requirements
- Python 3.10+
- click, pandas, Pillow, PyYAML, pytest

---

## 📖 Usage

### Scan a Directory
```bash
python -m smart_organizer scan --path ./sample_data
```
```
══════════════════════════════════════════════════════════
                     SCAN RESULTS
══════════════════════════════════════════════════════════

  📁 Total Files:  6
  💾 Total Size:   2.15 KB
  📅 Oldest File:  notes.txt (2026-08-06)
  📅 Newest File:  data.json (2026-08-06)

  CATEGORY BREAKDOWN
  ──────────────────────────────────────────
  Category     | Count | Size
  📊 Data      | 2     | 856 B
  📄 Documents | 2     | 1.23 KB
  💻 Code      | 1     | 312 B
```

### Organize Files (Dry Run)
```bash
python -m smart_organizer organize --path ./Downloads --dry-run
```
```
📋 DRY RUN MODE — No files will be moved

  [COPY] report.pdf
       → Organized/Documents/2026/2026-08-06_report.pdf
  [COPY] photo.jpg
       → Organized/Images/2026/2026-08-06_photo.jpg

  ⚠️ DRY RUN — No files were actually moved or copied
  💡 Run with --execute to apply these changes.
```

### Organize Files (Execute)
```bash
python -m smart_organizer organize --path ./Downloads --execute --mode copy
```

### Detect Duplicates
```bash
python -m smart_organizer dedupe --path ./sample_data --dry-run
```
```
🔍 DUPLICATE DETECTION RESULTS

  🔍 Duplicate Groups:   1
  📄 Duplicate Files:    1
  💾 Space Recoverable:  856 B

  Group 1 | Size: 856 B | Copies: 2
    ✅ KEEP   notes.txt
    ❌ DUPE   duplicate.txt
```

### Generate Reports
```bash
# JSON report
python -m smart_organizer report --path ./sample_data --format json

# HTML report (with styled charts)
python -m smart_organizer report --path ./sample_data --format html

# CSV report
python -m smart_organizer report --path ./sample_data --format csv
```

### Undo Last Operation
```bash
python -m smart_organizer undo --manifest Organized/manifest.json
```

---

## 📁 Project Structure

```
SmartFileOrganizer/
├── smart_organizer/              # Main package
│   ├── __init__.py               # Package init
│   ├── __main__.py               # Entry point (python -m)
│   ├── cli.py                    # Click CLI interface
│   ├── scanner.py                # File scanning & classification
│   ├── organizer.py              # Organization engine
│   ├── deduplicator.py           # Duplicate detection (SHA-256)
│   ├── extractor.py              # Metadata extraction
│   ├── reporter.py               # Report generation (JSON/CSV/HTML)
│   ├── config.py                 # YAML config loader
│   └── utils.py                  # Shared utilities & logging
├── tests/                        # pytest unit tests
│   ├── test_scanner.py           # Scanner tests
│   ├── test_deduplicator.py      # Deduplicator tests
│   ├── test_organizer.py         # Organizer tests
│   ├── test_extractor.py         # Extractor tests
│   └── test_reporter.py          # Reporter tests
├── sample_data/                  # Demo files
│   ├── report.csv                # Sample CSV data
│   ├── notes.txt                 # Sample text file
│   ├── duplicate.txt             # Duplicate of notes.txt
│   ├── code_sample.py            # Sample Python script
│   └── data.json                 # Sample JSON data
├── config.yaml                   # Default configuration
├── requirements.txt              # Dependencies
├── setup.py                      # Package setup
└── README.md                     # This file
```

---

## ⚙️ Configuration

Edit `config.yaml` to customize behavior:

```yaml
# Custom category mappings
categories:
  Documents:
    - .pdf
    - .doc
    - .txt
  Images:
    - .jpg
    - .png

# Output directory
output_directory: "Organized"

# Rename pattern: {date}, {original}, {counter}
rename_pattern: "{date}_{original}"

# Directories to skip
excluded_dirs:
  - .git
  - __pycache__
  - node_modules

# Hash algorithm: sha256 or md5
hash_algorithm: "sha256"
```

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test module
pytest tests/test_scanner.py -v

# Run with coverage
pytest tests/ -v --tb=short
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|-----------|---------|
| Python 3.10+ | Core language |
| Click | CLI framework |
| Pandas | CSV parsing & statistics |
| Pillow | Image metadata & EXIF |
| PyYAML | Configuration management |
| hashlib | SHA-256 duplicate detection |
| pathlib | Cross-platform file operations |
| pytest | Unit testing |

---

## 📊 Sample HTML Report

The HTML report features:
- Modern dark theme with gradients
- Category breakdown with colored badges
- CSS bar chart visualization
- Duplicate detection summary
- File metadata details

---

## 📝 License

MIT License

## 👤 Author

**Jay** — Summer Internship 2026
