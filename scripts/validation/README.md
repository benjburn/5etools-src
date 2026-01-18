# PDF Validation Scripts

This directory contains Python scripts for validating PDF files and references in the 5etools project.

## check_pdf.py

### Overview

`check_pdf.py` validates PDF files and their references in JSON data. It ensures that:

- All PDF files in `img/pdf/` are accessible and readable
- PDF references in JSON data point to existing files
- There are no broken or missing PDF files
- Unreferenced PDF files are identified

### Usage

#### Basic Usage

```bash
# From project root
python scripts/validation/check_pdf.py

# From scripts/validation directory
cd scripts/validation && python check_pdf.py
```

#### With uv (Recommended)

```bash
# Run with uv (no installation required)
uv run scripts/validation/check_pdf.py

# Or create a virtual environment first
uv venv
source .venv/bin/activate  # On Linux/macOS
# or .venv\Scripts\activate on Windows
python scripts/validation/check_pdf.py
```

### Output

The script produces two types of output:

#### 1. Human-Readable Report

A detailed report printed to stdout with emoji indicators:

```
🚀 Начинаю проверку PDF файлов...

🔍 Проверка 108 PDF файлов...
  ✓ Все файлы доступны

🔍 Поиск ссылок на PDF в JSON данных...
  ✓ Найдено 50 уникальных ссылок

🔍 Проверка ссылок на PDF...
  ✓ Все ссылки валидны

============================================================
📊 ОТЧЁТ О ПРОВЕРКЕ PDF
============================================================

✅ Статус: SUCCESS

📁 PDF файлы:
  Всего: 108
  Доступно: 108
  Недоступно: 0
  Повреждено: 0

🔗 Ссылки в JSON данных:
  Всего ссылок: 100
  Валидных: 100
  Отсутствует файлов: 0

📋 Неиспользуемые PDF файлы: 58
  ⚠️  Неиспользуемые файлы:
    - AWM/File1.pdf
    - AZfyT/File2.pdf
    ...

📈 Итог:
  Ошибок: 0
  Предупреждений: 58
============================================================
```

#### 2. JSON Report

A JSON report printed at the end for machine processing:

```json
{
  "status": "success",
  "pdf_files": {
    "total": 108,
    "accessible": 108,
    "inaccessible": [],
    "broken": []
  },
  "json_references": {
    "total_references": 100,
    "unique_references": 50,
    "valid_files": 50,
    "missing_files": []
  },
  "unreferenced_pdfs": [
    "AWM/File1.pdf",
    "AZfyT/File2.pdf"
  ],
  "summary": {
    "errors": 0,
    "warnings": 58
  }
}
```

### Exit Codes

- `0` - All checks passed (no errors)
- `1` - One or more errors found

### What Gets Checked

1. **PDF File Accessibility**
   - File exists
   - File is readable
   - Valid PDF format (starts with `%PDF`)

2. **JSON References**
   - Finds all `{@5etoolsImg ...|pdf/...}` references in JSON data
   - Checks if referenced files exist
   - Reports missing files

3. **Unreferenced Files**
   - Identifies PDF files that are not referenced in any JSON data
   - These are warnings, not errors (may be intentional)

### Error Types

#### Errors (❌)

- **Inaccessible files**: PDF files that cannot be read
- **Broken files**: PDF files with invalid format
- **Missing files**: Referenced files that don't exist

#### Warnings (⚠️)

- **Unreferenced files**: PDF files that exist but are not referenced in JSON data

### Integration with CI/CD

The script can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Validate PDF files
  run: |
    uv run scripts/validation/check_pdf.py
```

```bash
# Example package.json script
"validate:pdf": "python scripts/validation/check_pdf.py"
```

### Requirements

- Python 3.7+
- No external dependencies (uses only standard library)

### Project Structure

```
scripts/validation/
├── README.md           # This file
└── check_pdf.py        # PDF validation script
```

### Related Documentation

- [Project TODO](../../../TODO.MD) - Section 4.5: Проверка PDF
- [Images Documentation](../../../docs/images.md) - Image reference system
- [CLAUDE.md](../../../CLAUDE.md) - Project overview and conventions

### Troubleshooting

#### Script not found
Make sure you're running from the project root directory:
```bash
cd /path/to/5etools-src
python scripts/validation/check_pdf.py
```

#### Permission denied
Make the script executable:
```bash
chmod +x scripts/validation/check_pdf.py
```

#### Python not found
Use `uv` to run without installing:
```bash
uv run scripts/validation/check_pdf.py
```

### Contributing

When adding new validation scripts:

1. Follow the same structure as `check_pdf.py`
2. Use the `Validator` class pattern
3. Provide both human-readable and JSON output
4. Return appropriate exit codes
5. Update this README with usage instructions

### License

Same as the 5etools project.
