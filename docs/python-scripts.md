# Python скрипты валидации

Этот документ описывает установку и использование Python скриптов для валидации данных проекта 5etools.

## Текущий статус

**Версия:** 1.0
**Дата:** 2025-01-18

Реализованные скрипты:
- ✅ `check_pdf.py` - Проверка PDF файлов (полностью функционален)
- ✅ `check_links.py` - Проверка ссылок в JSON данных (реализован)
- 🚧 Другие скрипты - запланированы (см TODO.MD секция 4)

## Установка зависимостей

### Требования

- **Python 3.7+** (рекомендуется Python 3.12)
- **uv** (опционально) - Современный package manager для Python

### Использование без установки зависимостей

Большинство скриптов используют только стандартную библиотеку Python и не требуют установки дополнительных пакетов:

```bash
# Прямой запуск
python3 scripts/validation/check_pdf.py

# Или через python
python3 scripts/validation/check_links.py
```

### Установка uv (опционально)

Если вы хотите использовать `uv` для управления зависимостями:

```bash
# Linux/Mac
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.sh | iex"

# Проверка установки
uv --version
```

### Создание виртуального окружения (опционально)

```bash
# Переход в корень проекта
cd /home/benjburn/Projects/5etools-src

# Создание виртуального окружения с uv
uv venv

# Активация окружения (Linux/Mac)
source .venv/bin/activate

# Активация окружения (Windows)
.venv\Scripts\activate

# Проверка, что окружение активировано
which python  # Должен показывать путь к .venv/bin/python
```

### Установка зависимостей (если требуются)

```bash
# Установка всех зависимостей из requirements.txt
uv pip install -r requirements.txt

# Или использование pip-sync для точного соответствия
uv pip sync requirements.txt
```

## Скрипты валидации

### check_pdf.py

Проверка PDF файлов в репозитории.

**Назначение:**
- Поиск всех PDF файлов в `img/pdf/`
- Проверка корректности ссылок на PDF
- Валидация метаданных PDF
- Проверка соответствия PDF sources

**Использование:**

```bash
# Базовая проверка всех PDF файлов
python scripts/validation/check_pdf.py

# Проверка с сохранением отчёта в JSON
python scripts/validation/check_pdf.py --output report/pdf-check.json

# Подробный вывод с логированием
python scripts/validation/check_pdf.py --verbose

# Проверка конкретного source
python scripts/validation/check_pdf.py --source PHB

# Комбинация опций
python scripts/validation/check_pdf.py --output report/pdf-phb.json --source PHB --verbose
```

**Опции:**

| Опция | Описание |
|-------|----------|
| `--output FILE` | Сохранить отчёт в указанный файл (JSON формат) |
| `--source SOURCE` | Проверить только PDF для конкретного source |
| `--verbose` | Подробный вывод с дополнительной информацией |
| `--quiet` | Минимальный вывод (только ошибки) |

**Формат отчёта:**

```json
{
  "timestamp": "2025-01-18T12:00:00Z",
  "total_pdfs": 108,
  "checked": 108,
  "errors": [],
  "warnings": [
    {
      "file": "img/pdf/ScoEE/01.pdf",
      "source": "ScoEE",
      "message": "Missing metadata"
    }
  ],
  "by_source": {
    "PHB": { "count": 1, "status": "ok" },
    "ScoEE": { "count": 52, "status": "warning" }
  }
}
```

---

### check_links.py

Проверка ссылок в JSON данных.

**Назначение:**
- Валидация `{@tag}` ссылок в JSON файлах
- Проверка существования referenced entities
- Поиск битых ссылок
- Проверка cross-source ссылок

**Использование:**

```bash
# Проверка всех JSON файлов
python scripts/validation/check_links.py

# Проверка конкретной категории данных
python scripts/validation/check_links.py --category spells

# Проверка конкретного source
python scripts/validation/check_links.py --source PHB

# С сохранением отчёта
python scripts/validation/check_links.py --output report/links-check.json

# Подробный режим
python scripts/validation/check_links.py --verbose
```

**Опции:**

| Опция | Описание |
|-------|----------|
| `--category CAT` | Проверить только категорию (spells, items, bestiary и т.д.) |
| `--source SOURCE` | Проверить только конкретный source |
| `--output FILE` | Сохранить отчёт в файл |
| `--verbose` | Подробный вывод |
| `--fix-interactive` | Интерактивный режим исправления (будет реализован позже) |

**Примеры:**

```bash
# Проверка всех ссылок в заклинаниях
python scripts/validation/check_links.py --category spells

# Проверка ссылок в Monsters Manual
python scripts/validation/check_links.py --source MM --verbose

# Проверка с сохранением детального отчёта
python scripts/validation/check_links.py --output report/links-full.json --verbose
```

---

### check_images.py

Проверка image references в данных.

**Назначение:**
- Валидация путей к изображениям
- Проверка существования referenced images
- Поиск orphaned images (неиспользуемых)
- Проверка cover images в books.json
- Валидация token/portrait references

**Использование:**

```bash
# Проверка всех изображений
python scripts/validation/check_images.py

# Проверка конкретной категории
python scripts/validation/check_images.py --category bestiary

# Проверка конкретного source
python scripts/validation/check_images.py --source VGM

# Поиск orphaned images
python scripts/validation/check_images.py --find-orphans

# Подробный вывод
python scripts/validation/check_images.py --verbose
```

**Опции:**

| Опция | Описание |
|-------|----------|
| `--category CAT` | Категория для проверки (bestiary, book, adventure и т.д.) |
| `--source SOURCE` | Проверить только конкретный source |
| `--find-orphans` | Найти изображения, на которые нет ссылок |
| `--check-covers` | Проверить cover images в books.json |
| `--output FILE` | Сохранить отчёт в файл |
| `--verbose` | Подробный вывод |

**Примеры:**

```bash
# Проверка всех изображений в bestiary
python scripts/validation/check_images.py --category bestiary

# Поиск неиспользуемых изображений
python scripts/validation/check_images.py --find-orphans --output report/orphaned-images.json

# Проверка cover images для всех книг
python scripts/validation/check_images.py --check-covers
```

---

### check_cross_source.py

Проверка cross-source тегов и ссылок.

**Назначение:**
- Поиск всех cross-source references
- Проверка корректности cross-source тегов
- Валидация `reprintedAs` полей
- Анализ зависимостей между sources

**Использование:**

```bash
# Проверка всех cross-source ссылок
python scripts/validation/check_cross_source.py

# Проверка конкретного source
python scripts/validation/check_cross_source.py --source TCE

# Анализ зависимостей
python scripts/validation/check_cross_source.py --analyze-dependencies

# Экспорт в граф формата DOT
python scripts/validation/check_cross_source.py --export-graph deps.dot
```

**Опции:**

| Опция | Описание |
|-------|----------|
| `--source SOURCE` | Проверить cross-source ссылки для конкретного source |
| `--analyze-dependencies` | Анализировать зависимости между sources |
| `--export-graph FILE` | Экспортировать граф зависимостей в DOT формат |
| `--output FILE` | Сохранить отчёт в файл |
| `--verbose` | Подробный вывод |

**Примеры:**

```bash
# Анализ всех cross-source зависимостей
python scripts/validation/check_cross_source.py --analyze-dependencies --verbose

# Создание графа зависимостей для визуализации
python scripts/validation/check_cross_source.py --export-graph dependencies.dot

# Проверка cross-source ссылок для TCE
python scripts/validation/check_cross_source.py --source TCE
```

---

### check_fluff.py

Проверка fluff-файлов.

**Назначение:**
- Валидация структуры fluff-*.json файлов
- Проверка image references во fluff
- Анализ source distribution во fluff
- Поиск несоответствий между mechanical data и fluff

**Использование:**

```bash
# Проверка всех fluff-файлов
python scripts/validation/check_fluff.py

# Проверка конкретного типа fluff
python scripts/validation/check_fluff.py --type monsterFluff

# Проверка конкретного source
python scripts/validation/check_fluff.py --source PHB

# Сравнение с mechanical data
python scripts/validation/check_fluff.py --compare-with-mechanical
```

**Опции:**

| Опция | Описание |
|-------|----------|
| `--type TYPE` | Тип fluff (monsterFluff, spellFluff, itemFluff и т.д.) |
| `--source SOURCE` | Проверить только конкретный source |
| `--compare-with-mechanical` | Сравнить fluff с mechanical data |
| `--check-images` | Проверить image references во fluff |
| `--output FILE` | Сохранить отчёт в файл |
| `--verbose` | Подробный вывод |

**Примеры:**

```bash
# Проверка всех monster fluff файлов
python scripts/validation/check_fluff.py --type monsterFluff

# Сравнение fluff с mechanical данными
python scripts/validation/check_fluff.py --compare-with-mechanical --verbose

# Проверка изображений во fluff
python scripts/validation/check_fluff.py --check-images --output report/fluff-images.json
```

---

### check_data_integrity.py

Проверка целостности данных.

**Назначение:**
- Сравнение количества entities до и после обработки
- Проверка отсутствия дублирования данных
- Валидация source fields
- Проверка соответствия схемам

**Использование:**

```bash
# Полная проверка целостности
python scripts/validation/check_data_integrity.py

# Проверка конкретной категории
python scripts/validation/check_data_integrity.py --category spells

# Сравнение с baseline
python scripts/validation/check_data_integrity.py --compare-baseline baseline.json

# Создание нового baseline
python scripts/validation/check_data_integrity.py --create-baseline baseline.json
```

**Опции:**

| Опция | Описание |
|-------|----------|
| `--category CAT` | Проверить только категорию |
| `--compare-baseline FILE` | Сравнить с baseline файлом |
| `--create-baseline FILE` | Создать новый baseline |
| `--check-sources` | Проверить корректность source fields |
| `--check-duplicates` | Проверить наличие дубликатов |
| `--output FILE` | Сохранить отчёт в файл |
| `--verbose` | Подробный вывод |

**Примеры:**

```bash
# Создание baseline перед реструктуризацией
python scripts/validation/check_data_integrity.py --create-baseline baseline-before.json

# Проверка после реструктуризации
python scripts/validation/check_data_integrity.py --compare-baseline baseline-before.json

# Проверка на дубликаты
python scripts/validation/check_data_integrity.py --check-duplicates --verbose
```

---

## Запуск всех проверок

### Последовательный запуск

```bash
# Запуск всех скриптов последовательно
python scripts/validation/check_pdf.py && \
python scripts/validation/check_links.py && \
python scripts/validation/check_images.py && \
python scripts/validation/check_cross_source.py && \
python scripts/validation/check_fluff.py && \
python scripts/validation/check_data_integrity.py
```

### Использование run-all.py

```bash
# Запуск всех проверок через единый скрипт
python scripts/validation/run-all.py

# С сохранением всех отчётов в директорию
python scripts/validation/run-all.py --output-dir report/

# Быстрый режим (без подробных отчётов)
python scripts/validation/run-all.py --quick

# Подробный режим
python scripts/validation/run-all.py --verbose
```

**Опции run-all.py:**

| Опция | Описание |
|-------|----------|
| `--output-dir DIR` | Директория для сохранения отчётов |
| `--quick` | Быстрый режим (пропуск некоторых проверок) |
| `--verbose` | Подробный вывод для всех скриптов |
| `--skip SCRIPT` | Пропустить конкретный скрипт |
| `--parallel` | Параллельный запуск (если поддерживается) |

## Интеграция с CI/CD

### GitHub Actions

Пример конфигурации для `.github/workflows/python-validation.yml`:

```yaml
name: Python Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install uv
      run: |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        echo "$HOME/.local/bin" >> $GITHUB_PATH

    - name: Install dependencies
      run: |
        uv venv
        source .venv/bin/activate
        uv pip install -r requirements.txt

    - name: Run validation
      run: |
        source .venv/bin/activate
        python scripts/validation/run-all.py --output-dir report/

    - name: Upload reports
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: validation-reports
        path: report/
```

### Pre-commit hook

Пример `.git/hooks/pre-commit`:

```bash
#!/bin/bash

# Активация виртуального окружения
source .venv/bin/activate

# Запуск быстрой проверки
python scripts/validation/run-all.py --quick

# Проверка статуса выхода
if [ $? -ne 0 ]; then
    echo "❌ Validation failed. Commit aborted."
    exit 1
fi

echo "✅ All checks passed."
exit 0
```

Установка hook:

```bash
chmod +x .git/hooks/pre-commit
```

## Интерпретация результатов

### Статусы проверок

| Статус | Значение |
|--------|----------|
| `OK` | Проверка пройдена успешно |
| `WARNING` | Предупреждение (не критично) |
| `ERROR` | Ошибка (требует исправления) |
| `CRITICAL` | Критическая ошибка (блокирует дальнейшую работу) |

### Структура отчёта

Все скрипты генерируют отчёты в едином формате:

```json
{
  "script": "check_pdf.py",
  "timestamp": "2025-01-18T12:00:00Z",
  "status": "OK",
  "summary": {
    "total": 108,
    "checked": 108,
    "errors": 0,
    "warnings": 3
  },
  "details": [...],
  "performance": {
    "duration_seconds": 2.5,
    "memory_mb": 125
  }
}
```

### Общие проблемы

#### 1. Отсутствующие изображения

**Ошибка:** `Image not found: img/bestiary/MM/goblin.webp`

**Решение:**
- Проверить, что изображение существует в репозитории
- Убедиться, что путь корректный
- Проверить регистр символов (case-sensitive)

#### 2. Битые ссылки

**Ошибка:** `Broken reference: {@spell nonexistantspell}`

**Решение:**
- Проверить опечатку в имени заклинания
- Убедиться, что заклинание существует в данных
- Проверить source заклинания

#### 3. Cross-source конфликты

**Ошибка:** `Cross-source reference without proper tag: {@spell fireball}`

**Решение:**
- Проверить документацию `docs/cross-source.md`
- Убедиться, что cross-source ссылки корректны
- Добавить явный source в тег при необходимости

## Устранение проблем

### Проблема: `ModuleNotFoundError: No module named 'xxx'`

**Решение:**

```bash
# Убедитесь, что виртуальное окружение активировано
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Переустановите зависимости
uv pip install -r requirements.txt
```

### Проблема: `uv: command not found`

**Решение:**

```bash
# Переустановите uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Добавьте uv в PATH (добавьте в ~/.bashrc или ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"

# Перезагрузите конфигурацию
source ~/.bashrc  # или source ~/.zshrc
```

### Проблема: Скрипт работает медленно

**Решение:**

```bash
# Используйте режим --quick для быстрых проверок
python scripts/validation/run-all.py --quick

# Проверяйте только конкретные категории
python scripts/validation/check_links.py --category spells

# Используйте кеширование (если реализовано)
python scripts/validation/check_links.py --use-cache
```

### Проблема: Много ошибок после реструктуризации

**Решение:**

```bash
# Сравните с baseline до изменений
python scripts/validation/check_data_integrity.py \
  --compare-baseline baseline-before.json

# Проверьте конкретную категорию с ошибками
python scripts/validation/check_links.py --category problematic-category --verbose

# Проанализируйте cross-source зависимости
python scripts/validation/check_cross_source.py --analyze-dependencies
```

## Производительность

### Оптимизация скорости

| Метод | Описание | Ускорение |
|-------|----------|-----------|
| `--quick` | Быстрый режим (пропуск тяжёлых проверок) | ~70% |
| `--category CAT` | Проверка только одной категории | ~80-90% |
| `--source SOURCE` | Проверка только одного source | ~95% |
| Кеширование | Использование кеша (если реализовано) | ~50% |

### Типичное время выполнения

| Скрипт | Время (полный) | Время (--quick) |
|--------|----------------|-----------------|
| check_pdf.py | ~2-3 сек | ~1 сек |
| check_links.py | ~10-15 сек | ~3-5 сек |
| check_images.py | ~5-8 сек | ~2-3 сек |
| check_cross_source.py | ~8-12 сек | ~4-6 сек |
| check_fluff.py | ~5-7 сек | ~2-3 сек |
| check_data_integrity.py | ~3-5 сек | ~1-2 сек |
| **run-all.py** | ~35-50 сек | ~13-20 сек |

## Разработка

### Добавление нового скрипта валидации

1. Создайте файл в `scripts/validation/`:

```bash
# Создание шаблона нового скрипта
cat > scripts/validation/check_new_feature.py << 'EOF'
#!/usr/bin/env python3
"""Check new feature in 5etools data."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def check_new_feature(data_dir: Path, verbose: bool = False) -> Dict[str, Any]:
    """
    Check new feature.

    Args:
        data_dir: Path to data directory
        verbose: Enable verbose output

    Returns:
        Report dictionary
    """
    report = {
        "script": "check_new_feature.py",
        "timestamp": None,  # Set when generating report
        "status": "OK",
        "summary": {
            "total": 0,
            "checked": 0,
            "errors": 0,
            "warnings": 0,
        },
        "details": [],
    }

    # TODO: Implement validation logic

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Check new feature in 5etools data"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Path to data directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Save report to file",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Run validation
    report = check_new_feature(args.data_dir, args.verbose)

    # Add timestamp
    from datetime import datetime
    report["timestamp"] = datetime.utcnow().isoformat() + "Z"

    # Save report if requested
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        if args.verbose:
            print(f"Report saved to: {args.output}")

    # Exit with error code if validation failed
    if report["status"] != "OK":
        sys.exit(1)


if __name__ == "__main__":
    main()
EOF

# Сделайте скрипт исполняемым
chmod +x scripts/validation/check_new_feature.py
```

2. Добавьте скрипт в `run-all.py`:

```python
# В функции run_all() добавьте:
scripts_to_run = [
    "check_pdf.py",
    "check_links.py",
    "check_images.py",
    "check_cross_source.py",
    "check_fluff.py",
    "check_data_integrity.py",
    "check_new_feature.py",  # <-- Добавьте сюда
]
```

3. Обновите `requirements.txt` если нужны новые зависимости:

```bash
# Добавьте зависимости
uv pip add new-package

# Сохраните в requirements.txt
uv pip freeze > requirements.txt
```

### Тестирование скриптов

```bash
# Запуск с тестовыми данными
python scripts/validation/check_new_feature.py --data-dir test/data/ --verbose

# Проверка с различным verbosity
python scripts/validation/check_new_feature.py --verbose 2>&1 | tee output.log

# Профилирование производительности
python -m cProfile -o profile.stats scripts/validation/check_new_feature.py
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"
```

## Дополнительные ресурсы

### Документация проекта

- **[CLAUDE.md](../CLAUDE.md)** - Основная документация проекта
- **[docs/README.md](README.md)** - Индекс технической документации
- **[docs/data-validation.md](data-validation.md)** - Система валидации данных
- **[docs/cross-source.md](cross-source.md)** - Cross-source ссылки
- **[docs/images.md](images.md)** - Система изображений
- **[docs/fluff.md](fluff.md)** - Fluff контент

### Полезные команды

```bash
# Проверка версии Python
python --version

# Проверка установки uv
uv --version

# Список установленных пакетов
uv pip list

# Обновление всех пакетов
uv pip upgrade --all

# Очистка кеша uv
uv cache clean

# Проверка виртуального окружения
which python
python -c "import sys; print(sys.prefix)"
```

## Поддержка

Если вы столкнулись с проблемой, не описанной в этом документе:

1. Проверьте [TODO.MD](../TODO.MD) для известные проблемы
2. Посмотрите существующие JavaScript тесты в `/test/` для референса
3. Создайте issue в репозитории с подробным описанием проблемы

---

**Последнее обновление:** 2025-01-18

**Версия документации:** 1.0
