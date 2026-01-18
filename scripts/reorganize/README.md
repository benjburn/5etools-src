# Модуль реорганизации данных 5etools

Этот модуль предназначен для преобразования структуры данных 5etools из **контентно-ориентированной** (по типам файлов) в **источник-ориентированную** (по книгам/источникам).

## Обзор

Модуль реорганизует данные из плоской структуры:
```
data/
├── backgrounds.json
├── items.json
├── monsters.json
├── races.json
├── spells.json
└── ...
```

В структуру по источникам:
```
data_rework/
├── PHB/
│   ├── data/
│   │   ├── backgrounds.json
│   │   ├── classes.json
│   │   └── ...
│   ├── img/
│   │   ├── covers/
│   │   ├── bestiary/
│   │   └── ...
│   └── pdf/
├── XPHB/
├── DMG/
└── ...
```

При этом оригинальные директории `data/` и `img/` сохраняются без изменений.

## Требования

- **Python 3.7+**
- Отсутствие внешних зависимостей (используется только стандартная библиотека)
- Необходимые директории проекта: `data/`, `img/`, `img/pdf/`
- Файл `data/books.json` с мета-данными источников

## Установка

### Настройка виртуального окружения

Рекомендуется использовать `uv` для управления виртуальными окружениями:

```bash
# Создание виртуального окружения (если ещё не создано)
uv venv

# Активация окружения
source .venv/bin/activate  # Linux/macOS
# или
.venv\Scripts\activate  # Windows

# Установка зависимостей
# Внешние зависимости отсутствуют, используется только стандартная библиотека
```

## Использование

### Базовый запуск

```bash
python scripts/reorganize/reorganize_data.py
```

### Параметры командной строки

| Параметр | Описание |
|----------|----------|
| `--data-dir PATH` | Путь к директории данных (по умолчанию: `data/`) |
| `--img-dir PATH` | Путь к директории изображений (по умолчанию: `img/`) |
| `--output-dir PATH` | Путь к выходной директории (по умолчанию: `data_rework/`) |
| `--sources PHB XPHB` | Обработка только указанных источников |
| `--create-baseline PATH` | Создать бэкап (baseline snapshot) перед реорганизацией |
| `--skip-validation` | Пропустить валидацию после реорганизации |
| `--quick-check-only` | Только быстрая проверка целостности |
| `-v, --verbose` | Подробный вывод (DEBUG level) |
| `-q, --quiet` | Только предупреждения и ошибки |
| `--version` | Показать версию скрипта |

### Примеры использования

```bash
# Обработка всех источников с валидацией
python scripts/reorganize/reorganize_data.py

# Обработка только Player's Handbook и Tasha's Cauldron
python scripts/reorganize/reorganize_data.py --sources PHB TCE

# Обработка без валидации (быстрее)
python scripts/reorganize/reorganize_data.py --skip-validation

# Подробный вывод с созданием бэкапа
python scripts/reorganize/reorganize_data.py --verbose --create-baseline backup.json

# Только быстрая проверка целостности (без полной валидации)
python scripts/reorganize/reorganize_data.py --quick-check-only

# Тихий режим (только ошибки и предупреждения)
python scripts/reorganize/reorganize_data.py --quiet

# Обработка с пользовательскими путями
python scripts/reorganize/reorganize_data.py \
    --data-dir /path/to/data \
    --img-dir /path/to/img \
    --output-dir /path/to/output
```

## Архитектура модуля

### Структура файлов

| Файл | Назначение |
|------|------------|
| `reorganize_data.py` | Главный скрипт с функцией `main()`, управляющий всем процессом |
| `config.py` | Конфигурационные параметры и константы |
| `json_processor.py` | Обработка JSON файлов: извлечение, группировка, сохранение |
| `image_copier.py` | Копирование изображений из `/img/` в `/data_rework/{SOURCE}/img/` |
| `pdf_copier.py` | Копирование PDF файлов из `/img/pdf/` |
| `validation.py` | Валидация данных после реорганизации |
| `utils.py` | Вспомогательные функции: логирование, работа с JSON, статистика |

### Workflow реорганизации

Процесс состоит из 5 основных этапов:

#### 1. Создание структуры директорий

```
data_rework/
├── {SOURCE}/
│   ├── data/      # для JSON файлов
│   ├── img/       # для изображений
│   └── pdf/       # для PDF файлов
```

#### 2. Обработка JSON файлов

- Основные файлы: `backgrounds.json`, `items.json`, `monsters.json` и т.д.
- Специальные под-директории:
  - `bestiary/` - данные существ
  - `class/` - данные классов
  - `book/` - данные книг
  - `spells/` - данные заклинаний
- Извлечение сущностей по полю `source`
- Группировка по источникам
- Сохранение в `data_rework/{SOURCE}/data/`

#### 3. Копирование изображений

- Обложки: `img/covers/{SOURCE}.webp`
- Категории: `img/{category}/{SOURCE}/**/*`
  - bestiary, book, items, backgrounds, classes, races, spells, deities и др.
- Токены существ: `img/bestiary/tokens/{SOURCE}/**/*`
- Сохранение в `data_rework/{SOURCE}/img/`

#### 4. Копирование PDF файлов

- Копирование из `img/pdf/{SOURCE}/`
- Сохранение в `data_rework/{SOURCE}/pdf/`

#### 5. Валидация и отчётность

- Быстрая проверка целостности (всегда)
- Полная валидация (если не отключена):
  - Проверка целостности данных
  - Проверка изображений
  - Проверка кросс-источниковых ссылок
- Создание отчётов:
  - `reorganization-report.json` - отчёт о реорганизации
  - `validation-report.json` - отчёт о валидации

## Выходные данные

### Структура выходной директории

```
data_rework/
├── PHB/
│   ├── data/
│   │   ├── backgrounds.json
│   │   ├── classes.json
│   │   ├── items.json
│   │   └── ...
│   ├── img/
│   │   ├── covers/
│   │   ├── bestiary/
│   │   ├── items/
│   │   └── ...
│   └── pdf/
├── XPHB/
├── DMG/
└── reorganization-report.json
```

### Отчёты

#### reorganization-report.json

```json
{
  "timestamp": "2025-01-18T12:34:56Z",
  "version": "1.0.0",
  "sources_processed": 3,
  "statistics": {
    "json_files": {...},
    "images": {...},
    "pdfs": {...},
    "cross_source_references": {...}
  },
  "errors": [],
  "warnings": [],
  "success": true
}
```

#### validation-report.json

```json
{
  "overall_status": "passed",
  "checks": {
    "data_integrity": {...},
    "images": {...},
    "cross_source": {...}
  },
  "errors": [],
  "warnings": []
}
```

## Конфигурация

### Ключевые параметры в config.py

```python
# Форматирование JSON
JSON_INDENT = "\t"              # Табуляция (как в оригинальных файлах)
JSON_ENSURE_ASCII = False       # Сохранять Unicode символы
JSON_SORT_KEYS = False          # Сохранять исходный порядок ключей

# Валидация
RUN_VALIDATION_BY_DEFAULT = True  # Запускать валидацию по умолчанию

# Производительность
MAX_WORKERS = 4                  # Количество параллельных процессов
SHOW_PROGRESS = True             # Показывать прогресс-бары (требует tqdm)

# Логирование
DEFAULT_LOG_LEVEL = "INFO"       # Уровень логирования по умолчанию
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Пути (по умолчанию)
DEFAULT_DATA_DIR = Path("data")
DEFAULT_IMG_DIR = Path("img")
DEFAULT_OUTPUT_DIR = Path("data_rework")
```

### Паттерны для пропуска

```python
# Директории для пропуска
SKIP_DIRS = {"generated", "__pycache__", ".git", "node_modules"}

# Файлы для пропуска
SKIP_FILES = {"books.json", "changelog.json", "converter.json"}

# Паттерны файлов для пропуска (fnmatch)
SKIP_PATTERNS = {"foundry-*.json"}
```

### Специальные маппинги изображений

Некоторые источники используют специальные сокращения в путях изображений:

```python
IMAGE_PATH_SPECIAL_MAPPINGS = {
    "PS-A": "PSA",  # Plane Shift: Amonkhet
    "PS-I": "PSI",  # Plane Shift: Innistrad
    "PS-D": "PSD",  # Plane Shift: Dominaria
    "PS-K": "PSK",  # Plane Shift: Kaladesh
    "PS-X": "PSX",  # Plane Shift: Ixalan
    "PS-Z": "PSZ",  # Plane Shift: Zendikar
    "HAT-TG": "TG", # Homerule Tax塔: Guide (историческое название)
}
```

## Отладка и troubleshooting

### Уровни логирования

| Уровень | Описание |
|---------|----------|
| `DEBUG` | Подробная информация о каждом шаге (включая `--verbose`) |
| `INFO` | Общая информация о прогрессе (по умолчанию) |
| `WARNING` | Предупреждения о возможных проблемах |
| `ERROR` | Критические ошибки, которые не удалось исправить |

### Типичные проблемы и решения

#### 1. Ошибка: "Data directory not found"

**Проблема**: Директория `data/` не существует или указан неверный путь.

**Решение**:
```bash
# Проверьте существование директории
ls -la data/

# Укажите правильный путь
python scripts/reorganize/reorganize_data.py --data-dir /path/to/data
```

#### 2. Ошибка: "No sources loaded from books.json"

**Проблема**: Файл `data/books.json` отсутствует или имеет неверный формат.

**Решение**:
```bash
# Проверьте существование и формат файла
cat data/books.json | head -20

# Убедитесь, что файл содержит ключ "book"
cat data/books.json | jq '.book'
```

#### 3. Предупреждение: "Found X entities without source field"

**Проблема**: Некоторые сущности не имеют поля `source`.

**Решение**:
- Используйте `--verbose` для просмотра списка проблемных сущностей
- Проверьте и добавьте поле `source` в JSON данные
- Сущности без `source` будут пропущены при группировке

#### 4. Кросс-источниковые ссылки

**Проблема**: В отчёте указаны кросс-источниковые ссылки на изображения.

**Решение**:
- Это нормально для некоторых источников (например, HFFotM)
- Проверьте файл `config.py` для списка `CROSS_SOURCE_IMAGE_SOURCES`
- Добавьте источник в список, если ссылки намеренные

### Интерпретация отчётов

#### Статус валидации

| Статус | Описание |
|--------|----------|
| `passed` | Все проверки пройдены успешно |
| `warning` | Есть предупреждения, но критических ошибок нет |
| `failed` | Обнаружены критические ошибки, требующие исправления |

#### Статистика в отчёте

```json
{
  "json_files": {
    "backgrounds.json": {"PHB": 10, "TCE": 5},
    "items.json": {"PHB": 50, "DMG": 30}
  },
  "images": {
    "PHB": {"covers": 1, "bestiary": 10, "items": 20},
    "DMG": {"covers": 1, "items": 15}
  },
  "pdfs": {
    "PHB": 1,
    "DMG": 1
  },
  "cross_source_references": {
    "total": 5,
    "examples": [...]
  }
}
```

## Группы источников

Sources организованы в следующие группы (из `config.py`):

| Группа | Источники |
|--------|-----------|
| **core** | PHB, XPHB, DMG, XDMG, MM, XMM |
| **supplement** | VGM, XGE, MTF, AI, TCE, FTD, MPMM, BGG, BMT, DMTCRG |
| **supplement-alt** | OGA, AWM, RMR, MGELFT, DoD, MaBJoV, TD, MCV4EC, HAT-TG, ABH, EFA |
| **setting** | SCAG, GGR, ERLW, EGW, MOT, VRGR, SCC, AAG, BAM, MPP, SatO, FRAiF, FRHoF, CoS |
| **setting-alt** | PS-Z, PS-I, PS-K, PS-A, PS-X, PS-D, NF, LFL |
| **screen** | Screen, ScreenDungeonKit, ScreenWildernessKit, ScreenSpelljammer, XScreen |
| **recipe** | HF, HFFotM, PaF |
| **other** | SAC, XSAC |
| **organized-play** | AL |

## Версионирование

Текущая версия модуля: **1.0.0**

История версий доступна в git репозитории:
```bash
git log -- scripts/reorganize/
```

## Поддержка и разработка

### Добавление новых категорий изображений

Для добавления новой категории изображений отредактируйте `config.py`:

```python
IMAGE_CATEGORIES = {
    # ... существующие категории ...
    "new_category",  # Добавьте новую категорию
}
```

### Добавление новых типов сущностей

Для обработки новых типов JSON сущностей:

```python
ENTITY_TYPES = {
    # ... существующие типы ...
    "new_entity_type",  # Добавьте новый тип
}
```

### Запуск тестов

```bash
# Запуск всех тестов
npm run test

# Валидация только JSON
npm run test:json

# Валидация тегов
npm run test:tags
```

## Лицензия

Этот модуль является частью проекта 5etools и распространяется под той же лицензией.

---

**Документация обновлена**: 2025-01-18
