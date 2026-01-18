# Структура /data_rework

## Обзор

Данный документ описывает планируемую структуру директории `/data_rework` после реструктуризации данных 5etools по источникам (sources).

**Цель реструктуризации:** Организовать все данные (JSON, изображения, PDF) по источникам вместо текущей структуры, организованной по типам контента.

**Текущая структура:**
```
/data/
├── actions.json          # Все действия всех источников
├── backgrounds.json      # Все предыстории всех источников
├── items.json            # Все предметы всех источников
├── adventure/            # Приключения по ID
├── bestiary/             # Существа по ID
└── ...

/img/
├── adventure/{SOURCE}/   # Изображения приключений
├── bestiary/{SOURCE}/    # Изображения существ
├── book/{SOURCE}/        # Изображения из книг
└── ...
```

**Планируемая структура:**
```
/data_rework/
├── [SOURCE]/             # Папка для каждого источника
│   ├── data/            # JSON данные источника
│   ├── img/             # Изображения источника
│   └── pdf/             # PDF файлы (если есть)
└── ...
```

## Структура папок

### Общая схема

```
/data_rework/
├── PHB/                  # Player's Handbook (2014)
│   ├── data/
│   │   ├── actions.json
│   │   ├── backgrounds.json
│   │   ├── classes.json
│   │   ├── feats.json
│   │   ├── items.json
│   │   ├── races.json
│   │   ├── spells.json
│   │   └── ...
│   ├── img/
│   │   ├── backgrounds/
│   │   ├── classes/
│   │   ├── items/
│   │   ├── races/
│   │   └── covers/PHB.webp
│   └── pdf/              (отсутствует)
│
├── XPHB/                 # Player's Handbook (2024)
│   ├── data/
│   ├── img/
│   └── pdf/              (отсутствует)
│
├── DMG/                  # Dungeon Master's Guide (2014)
│   ├── data/
│   ├── img/
│   └── pdf/              (отсутствует)
│
├── XDMG/                 # Dungeon Master's Guide (2024)
│   ├── data/
│   ├── img/
│   └── pdf/              (отсутствует)
│
├── MM/                   # Monster Manual (2014)
│   ├── data/
│   │   ├── bestiary.json
│   │   └── ...
│   ├── img/
│   │   ├── bestiary/
│   │   └── covers/MM.webp
│   └── pdf/              (отсутствует)
│
├── XMM/                  # Monster Manual (2025)
│   ├── data/
│   ├── img/
│   └── pdf/              (отсутствует)
│
├── TCE/                  # Tasha's Cauldron of Everything
│   ├── data/
│   ├── img/
│   └── pdf/              (отсутствует)
│
├── VGM/                  # Volo's Guide to Monsters
│   ├── data/
│   ├── img/
│   └── pdf/              (отсутствует)
│
├── XGE/                  # Xanathar's Guide to Everything
│   ├── data/
│   ├── img/
│   └── pdf/              (отсутствует)
│
└── ...                   # Остальные источники
```

## Список источников

Все источники определены в `data/books.json`. Всего **60 источников** в **9 группах**:

### Core (6 источников)

Основные книги правил D&D 5e:

| ID | Название | Дата публикации |
|----|----------|-----------------|
| PHB | Player's Handbook (2014) | 2014-08-19 |
| XPHB | Player's Handbook (2024) | 2024-09-17 |
| DMG | Dungeon Master's Guide (2014) | 2014-12-09 |
| XDMG | Dungeon Master's Guide (2024) | 2024-11-12 |
| MM | Monster Manual (2014) | 2014-09-30 |
| XMM | Monster Manual (2025) | 2025-02-18 |

### Supplement (10 источников)

Дополнения к правилам:

| ID | Название |
|----|----------|
| VGM | Volo's Guide to Monsters |
| XGE | Xanathar's Guide to Everything |
| MTF | Mordenkainen's Tome of Foes |
| AI | Acquisitions Incorporated |
| TCE | Tasha's Cauldron of Everything |
| FTD | Fizban's Treasury of Dragons |
| MPMM | Mordenkainen Presents: Monsters of the Multiverse |
| BGG | Bigby Presents: Glory of the Giants |
| BMT | The Book of Many Things |
| DMTCRG | The Deck of Many Things: Card Reference Guide |

### Supplement-alt (11 источников)

Альтернативные дополнения:

| ID | Название |
|----|----------|
| OGA | One Grung Above |
| AWM | Adventure with Muk |
| RMR | D&D vs. Rick and Morty: Basic Rules |
| MGELFT | Muk's Guide to Everything He Learned From Tasha |
| DoD | Domains of Delight |
| MaBJoV | Minsc and Boo's Journal of Villainy |
| TD | Tarot Deck |
| MCV4EC | Monstrous Compendium Volume 4: Eldraine Creatures |
| HAT-TG | Thieves' Gallery |
| ABH | Astarion's Book of Hungers |
| EFA | Eberron: Forge of the Artificer |

### Setting (14 источников)

Книги сеттингов:

| ID | Название |
|----|----------|
| SCAG | Sword Coast Adventurer's Guide |
| GGR | Guildmasters' Guide to Ravnica |
| ERLW | Eberron: Rising from the Last War |
| EGW | Explorer's Guide to Wildemount |
| MOT | Mythic Odysseys of Theros |
| VRGR | Van Richten's Guide to Ravenloft |
| SCC | Strixhaven: A Curriculum of Chaos |
| AAG | Astral Adventurer's Guide |
| BAM | Boo's Astral Menagerie |
| MPP | Morte's Planar Parade |
| SatO | Sigil and the Outlands |
| FRAiF | Forgotten Realms: Adventures in Faerûn |
| FRHoF | Forgotten Realms: Heroes of Faerûn |
| CoS | Curse of Strahd (2016) |

### Setting-alt (8 источников)

Альтернативные сеттинги:

| ID | Название |
|----|----------|
| PS-Z | Plane Shift: Zendikar |
| PS-I | Plane Shift: Innistrad |
| PS-K | Plane Shift: Kaladesh |
| PS-A | Plane Shift: Amonkhet |
| PS-X | Plane Shift: Ixalan |
| PS-D | Plane Shift: Dominaria |
| NF | Netheril's Fall |
| LFL | Lorwyn: First Light |

### Screen (5 источников)

Dungeon Master's Screen:

| ID | Название |
|----|----------|
| Screen | Dungeon Master's Screen |
| ScreenDungeonKit | Dungeon Master's Screen: Dungeon Kit |
| ScreenWildernessKit | Dungeon Master's Screen: Wilderness Kit |
| ScreenSpelljammer | Dungeon Master's Screen: Spelljammer |
| XScreen | Dungeon Master's Screen (2024) |

### Recipe (3 источника)

Кулинарные книги:

| ID | Название |
|----|----------|
| HF | Heroes' Feast |
| HFFotM | Heroes' Feast: Flavors of the Multiverse |
| PaF | Puncheons and Flagons |

### Other (2 источника)

Прочие материалы:

| ID | Название |
|----|----------|
| SAC | Sage Advice Compendium (2014) |
| XSAC | Sage Advice Compendium (2025) |

### Organized Play (1 источник)

| ID | Название |
|----|----------|
| AL | Adventurers League |

## Формат файлов

### JSON файлы

#### Правила именования

Файлы в `/data_rework/[SOURCE]/data/` сохраняют имена из текущей структуры:

**Текущее:** `/data/backgrounds.json`
**Новое:** `/data_rework/PHB/data/backgrounds.json` (только предыстории из PHB)

#### Структура JSON

JSON структура **НЕ изменяется**, за исключением:

1. **Фильтрация по source:** Каждый файл содержит только entities с соответствующим `source` полем
2. **Сохранение всех полей:** Все оригинальные поля сохраняются
3. **Tab indentation:** Используется tab indentation для читаемости
4. **Pretty-print:** Файлы форматированы для чтения (не минифицированы)

**Пример:** `/data/backgrounds.json` (сейчас)

```json
{
  "background": [
    {"name": "Acolyte", "source": "PHB", ...},
    {"name": "Acolyte", "source": "XPHB", ...},
    {"name": "Aberrant Heir", "source": "EFA", ...},
    ...
  ]
}
```

**Пример:** `/data_rework/PHB/data/backgrounds.json` (после)

```json
{
  "background": [
    {"name": "Acolyte", "source": "PHB", ...},
    {"name": "Anthropologist", "source": "PHB", ...},
    {"name": "Arcana Clerk", "source": "PHB", ...},
    ...  // только PHB backgrounds
  ]
}
```

#### Fluff файлы

Fluff файлы обрабатываются аналогично, но с учетом особенностей (см. `docs/fluff.md`):

**Текущее:** `/data/fluff-backgrounds.json`
**Новое:** `/data_rework/PHB/data/fluff-backgrounds.json` (только PHB fluff)

#### Типы файлов

Примерное распределение файлов по источникам (на основе анализа 1.2):

**Основные JSON файлы:**
- `actions.json` - Действия (боевая система)
- `backgrounds.json` - Предыстории персонажей
- `bastions.json` - Укрепления
- `bestiary/*.json` - Существа (в подпапках по ID)
- `charcreationoptions.json` - Опции создания персонажа
- `classes.json` - Классы и subclasses
- `conditionsdiseases.json` - Состояния и болезни
- `cultsboons.json` - Культы и благословения
- `deities.json` - Божества
- `feats.json` - Черты характера (feats)
- `items.json` - Предметы
- `languages.json` - Языки
- `objects.json` - Объекты
- `optionalfeatures.json` - Опциональные особенности
- `races.json` - Расы
- `recipes.json` - Рецепты (из кулинарных книг)
- `rewards.json` - Награды
- `spells/*.json` - Заклинания (в подпапках по ID)
- `trapshazards.json` - Ловушки и опасности
- `vehicles.json` - Транспортные средства

### Изображения

#### Правила именования

Структура папок изображений **сохраняется**, но копируется только в соответствующий источник:

**Текущее:** `/img/book/DMG/c1-1.webp`
**Новое:** `/data_rework/DMG/img/book/DMG/c1-1.webp`

**Текущее:** `/img/bestiary/MM/Goblin.webp`
**Новое:** `/data_rework/MM/img/bestiary/MM/Goblin.webp`

#### Типы изображений

1. **Covers:** Обложки книг (`/img/covers/[SOURCE].webp`)
2. **Bestiary:** Изображения существ (`/img/bestiary/[SOURCE]/...`)
3. **Items:** Изображения предметов (`/img/items/[SOURCE]/...`)
4. **Adventure:** Изображения из приключений (`/img/adventure/[SOURCE]/...`)
5. **Backgrounds:** Изображения предысторий (`/img/backgrounds/[SOURCE]/...`)
6. **Classes:** Изображения классов (`/img/classes/[SOURCE]/...`)
7. **Races:** Изображения рас (`/img/races/[SOURCE]/...`)
8. **Spells:** Изображения заклинаний (`/img/spells/[SOURCE]/...`)
9. **Deities:** Изображения божеств (`/img/deities/[SOURCE]/...`)
10. **Tokens:** Токены для VTT (`/img/bestiary/[SOURCE]/token/...`)
11. **Portraits:** Портреты существ (`/img/bestiary/[SOURCE]/portrait/...`)
12. **PDF:** PDF-файлы (`/img/pdf/[SOURCE]/...`)

#### Cross-source изображения

**Важно:** Cross-source ссылки на изображения **НЕ модифицируются** и **НЕ копируются** (см. `docs/cross-source.md` и `docs/images.md`):

**Пример cross-source ссылки:**
```json
{
  "name": "Amphisbaena",
  "source": "GoS",
  "fluff": {
    "entries": [
      {
        "type": "image",
        "href": {
          "type": "internal",
          "path": "bestiary/MOT/Amphisbaena.webp"
        }
      }
    ]
  }
}
```

В этом случае:
- Entity находится в `GoS`
- Изображение находится в `MOT`
- **НЕ копируем** `bestiary/MOT/Amphisbaena.webp` в `/data_rework/GoS/img/`
- **Оставляем** путь `bestiary/MOT/Amphisbaena.webp` без изменений

### PDF файлы

#### Расположение

PDF файлы находятся в `/img/pdf/[SOURCE]/`:

**Текущее:** `/img/pdf/ScoEE/ScoEE.pdf`
**Новое:** `/data_rework/ScoEE/pdf/ScoEE.pdf`

#### Источники с PDF

На основе анализа 1.3, PDF файлы есть у следующих источников:

| Source | Описание |
|--------|----------|
| ScoEE | Storm Lord's Wrath |
| WttHC | Sleeping Dragon's Wake |
| DitLCoT | Divine Contention |
| AWM | Adventure with Muk |
| IMR | Infernal Machinery Rebuilt |
| RMBRE | Rick and Morty vs. Dungeons & Dragons |
| PiP | Phandelver and Below: The Shattered Obelisk |
| HBTD | The Lost Mine of Phandelver (2017) |
| LRDT | Lost Mine of Phandelver (2014) |
| DoSI | Dragon of Icespire Peak |
| DSotDQ | Drift toward the Tomb |
| BGDIA | Black Dragon's Gate |
| VEoR | Vault of the Dracolich |
| XMtS | The Starless Cage |
| XDMG | Dungeon Master's Guide (2024) |
| UtHftLH | Unsung Heroes of the Hellish Heights |

## Отличия от текущей структуры

### Текущая архитектура

```
/                           # Корень проекта
├── data/                   # ВСЕ данные всех источников
│   ├── backgrounds.json    # Смешанные данные из PHB, XPHB, EFA, ...
│   ├── bestiary/           # Существа по ID (без сортировки по source)
│   │   ├── 001.json
│   │   ├── 002.json
│   │   └── ...
│   ├── items.json         # Смешанные данные из всех источников
│   └── ...
├── img/                    # ВСЕ изображения всех источников
│   ├── bestiary/          # Изображения по source
│   │   ├── MM/
│   │   ├── VGM/
│   │   ├── MPMM/
│   │   └── ...
│   ├── book/              # Изображения по source
│   └── ...
└── ...
```

**Проблемы текущей архитектуры:**

1. **Смешанные данные:** Каждый JSON файл содержит entities из всех источников
2. **Сложность навигации:** Не понятно, какие данные относятся к какому источнику
3. **Сложность внесения изменений:** Требуется загружать и фильтровать огромные файлы
4. **Избыточность:** Foundry-variant файлы (`foundry-*.json`) дублируют данные
5. **Generated файлы:** Папка `/data/generated/` смешана с ручными данными

### Планируемая архитектура

```
/                           # Корень проекта
├── data/                   # Сохраняется для обратной совместимости
├── data_rework/            # Новая структура по источникам
│   ├── PHB/               # Данные PHB отдельно
│   │   ├── data/
│   │   │   ├── backgrounds.json     # Только PHB backgrounds
│   │   │   ├── classes.json         # Только PHB classes
│   │   │   ├── feats.json           # Только PHB feats
│   │   │   ├── items.json           # Только PHB items
│   │   │   ├── races.json           # Только PHB races
│   │   │   └── ...
│   │   ├── img/
│   │   │   ├── backgrounds/         # PHB background images
│   │   │   ├── classes/             # PHB class images
│   │   │   ├── items/               # PHB item images
│   │   │   ├── races/               # PHB race images
│   │   │   └── covers/PHB.webp
│   │   └── pdf/                      (отсутствует)
│   │
│   ├── XPHB/              # Данные XPHB отдельно
│   │   ├── data/
│   │   ├── img/
│   │   └── pdf/
│   │
│   ├── DMG/               # Данные DMG отдельно
│   ├── MM/                # Данные MM отдельно
│   ├── TCE/               # Данные TCE отдельно
│   ├── VGM/               # Данные VGM отдельно
│   └── ...                # Остальные источники
├── img/                   # Сохраняется для обратной совместимости
└── ...
```

**Преимущества новой архитектуры:**

1. **Изоляция данных:** Каждый источник полностью независим
2. **Простота навигации:** Все данные одного источника в одной папке
3. **Простота внесения изменений:** Работаем только с нужным источником
4. **Удаление дубликатов:** Foundry-variant файлы исключены
5. **Четкая структура:** Понятно, где находятся данные каждого источника

## Примеры структуры

### Пример 1: PHB (Player's Handbook 2014)

```
/data_rework/PHB/
├── data/
│   ├── actions.json              # Боевые действия из PHB
│   ├── backgrounds.json          # 13 предысторий из PHB
│   ├── classes.json              # 12 классов из PHB
│   ├── feats.json                # Feats из PHB (Multiclassing, т.д.)
│   ├── items.json                # Предметы из PHB (equipment, chapter 6)
│   ├── races.json                # Расы из PHB (chapter 2)
│   ├── spells.json               # Заклинания из PHB (chapter 10)
│   ├── variantrules.json         # Вариантные правила из PHB
│   └── ...
├── img/
│   ├── backgrounds/              # Изображения предысторий
│   ├── classes/                  # Изображения классов
│   ├── items/                    # Изображения предметов
│   ├── races/                    # Изображения рас
│   ├── spells/                   # Изображения заклинаний
│   └── covers/PHB.webp           # Обложка
└── pdf/                          (отсутствует)
```

### Пример 2: MM (Monster Manual 2014)

```
/data_rework/MM/
├── data/
│   ├── bestiary/
│   │   ├── 001.json             # Aboleth (MM)
│   │   ├── 002.json             # Acolyte (MM)
│   │   ├── 003.json             # Adult Black Dragon (MM)
│   │   └── ...                  # ~444 существа из MM
│   ├── monsterfeatures.json     # Особенности существ
│   └── ...
├── img/
│   ├── bestiary/
│   │   ├── MM/
│   │   │   ├── Aboleth.webp
│   │   │   ├── Acolyte.webp
│   │   │   ├── token/
│   │   │   │   ├── Aboleth.png
│   │   │   │   └── ...
│   │   │   └── portrait/
│   │   │       ├── Aboleth.png
│   │   │       └── ...
│   └── covers/MM.webp           # Обложка
└── pdf/                          (отсутствует)
```

### Пример 3: TCE (Tasha's Cauldron of Everything)

```
/data_rework/TCE/
├── data/
│   ├── backgrounds.json          # Новые предыстории из TCE
│   ├── feats.json                # Новые feats из TCE
│   ├── items.json                # Новые предметы из TCE
│   ├── optionalfeatures.json     # Optional features из TCE
│   ├── puzzles.json              # Головоломки из TCE
│   └── ...
├── img/
│   ├── backgrounds/
│   ├── items/
│   ├── classes/                  # Изображения subclass features
│   └── covers/TCE.webp           # Обложка
└── pdf/                          (отсутствует)
```

### Пример 4: VGM (Volo's Guide to Monsters)

```
/data_rework/VGM/
├── data/
│   ├── bestiary/
│   │   ├── 001.json             # Изображенные существа из VGM
│   │   └── ...                  # ~120+ существ
│   ├── backgrounds.json          # Новые предыстории из VGM
│   ├── feats.json                # Feats из VGM
│   ├── items.json                # Предметы из VGM
│   ├── races.json                # Новые расы из VGM
│   └── ...
├── img/
│   ├── bestiary/
│   │   └── VGM/
│   │       ├── Aarakocra.webp
│   │       ├── Bugbear.webp
│   │       ├── token/
│   │       └── portrait/
│   ├── backgrounds/
│   ├── races/
│   └── covers/VGM.webp
└── pdf/                          (отсутствует)
```

### Пример 5: XPHB (Player's Handbook 2024)

```
/data_rework/XPHB/
├── data/
│   ├── actions.json              # Боевые действия из 2024 PHB
│   ├── backgrounds.json          # Предыстории из 2024 PHB
│   ├── bastions.json             # Bastions из 2024 PHB
│   ├── charcreationoptions.json  # Опции создания персонажа
│   ├── classes.json              # Классы из 2024 PHB
│   ├── feats.json                # Feats из 2024 PHB
│   ├── items.json                # Предметы из 2024 PHB
│   ├── races.json                # Расы из 2024 PHB (species)
│   ├── spells.json               # Заклинания из 2024 PHB
│   └── ...
├── img/
│   ├── backgrounds/
│   ├── classes/
│   ├── items/
│   ├── races/
│   ├── spells/
│   ├── bastions/
│   └── covers/XPHB.webp          # Обложка 2024
└── pdf/
    └── XPHB.pdf                  # PDF 2024 PHB (если есть)
```

### Пример 6: ScoEE (Storm Lord's Wrath - приключение с PDF)

```
/data_rework/ScoEE/
├── data/
│   ├── adventures.json           # Данные приключения
│   └── ...
├── img/
│   ├── adventure/
│   │   └── ScoEE/
│   │       ├── chapter1/
│   │       ├── maps/
│   │       └── ...
│   └── covers/ScoEE.webp
└── pdf/
    └── ScoEE.pdf                 # PDF приключения
```

## Ограничения и исключения

### Что НЕ обрабатывается (из TODO.MD секция 6)

#### Данные

- **Аудиофайлы** - не переносятся
- **Foundry-variant файлы** (`foundry-*.json`) - игнорируются
- **Generated файлы** (`/data/generated/`) - это build output

#### Frontend/Backend

- **HTML/CSS/JS файлы** - только как референс для понимания структуры данных
- **Service worker** - не обновляется
- **URL routing** - не обрабатывается
- **Кеширование** - не обрабатывается

#### Build/Testing

- **Build pipeline** скрипты в `/node/` - не обновляются
- **Thumbnail images** - не переносятся
- **Тестовая система** - не обновляется
- **Image metadata tagging** (width/height) - это build step

### Cross-source ссылки

**Критически важно:** Cross-source ссылки **НЕ модифицируются** (см. `docs/cross-source.md`):

1. **Теги:** `{@spell fireball}` всегда ссылается на оригинальный источник (PHB)
2. **Изображения:** Пути к cross-source изображениям не изменяются
3. **Entities:** `reprintedAs` поля сохраняются
4. **Валидация:** Скрипт должен логировать все cross-source dependencies

### Source версии

**Важно:** Различать source версии (2014 vs 2024):

- **PHB (2014):** Оригинальный Player's Handbook
- **XPHB (2024):** Обновленный Player's Handbook 2024
- **MM (2014):** Оригинальный Monster Manual
- **XMM (2025):** Обновленный Monster Manual 2025

Это **РАЗНЫЕ источники** с разными данными!

### Fluff обработка

Fluff файлы обрабатываются отдельно с учетом особенностей:

- **Именование:** `fluff-{category}-{source}.json`
- **Image references:** Cross-source изображения во fluff не копируются
- **Source distribution:** Fluff entities могут быть распределены по нескольким sources
- **Валидация:** Проверка image references во fluff (см. `docs/fluff.md`)

## Валидация

После реструктуризации должны быть выполнены следующие проверки (план из TODO.MD секция 4):

### 4.1. Проверка целостности данных

- [ ] Сравнить количество entities до и после обработки
- [ ] Проверить, что все объекты распределены по папкам
- [ ] Убедиться, что нет дублирования данных
- [ ] Проверить, что все source fields корректны

### 4.2. Проверка cross-source тегов

- [ ] Убедиться, что все cross-source теги на месте
- [ ] Проверить, что теги не модифицированы после обработки
- [ ] Вывести список всех cross-source dependencies
- [ ] Проверить `reprintedAs` fields

### 4.3. Проверка image references

- [ ] Проверить, что все internal images скопированы в соответствующие папки
- [ ] Проверить, что external image references не изменены
- [ ] Проверить cover images для всех books
- [ ] Проверить token/portrait references в bestiary
- [ ] Убедиться, что все image paths корректны

### 4.4. Проверка fluff

- [ ] Убедиться, что весь fluff распределён по source
- [ ] Проверить image references во fluff entries
- [ ] Сравнить структуру fluff до и после обработки

### 4.5. Проверка PDF

- [ ] Проверить, что все PDF файлы на месте
- [ ] Проверить корректность ссылок на PDF

### 4.6. Проверка ссылок

- [ ] Внутренние ссылки в JSON корректны
- [ ] Cross-source ссылки работают корректно
- [ ] Отсутствие битых ссылок

## Статистика

### Текущее состояние (на основе анализа 1.2-1.6)

- **Всего источников:** 60
- **Всего JSON файлов:** 494 (484 без generated/)
- **Уникальных source значений:** 179
- **Изображений:** ~15000+ файлов
- **PDF файлов:** 108

### Распределение sources по группам

| Группа | Количество | Процент |
|--------|------------|---------|
| setting | 14 | 23.3% |
| supplement-alt | 11 | 18.3% |
| supplement | 10 | 16.7% |
| setting-alt | 8 | 13.3% |
| core | 6 | 10.0% |
| screen | 5 | 8.3% |
| recipe | 3 | 5.0% |
| other | 2 | 3.3% |
| organized-play | 1 | 1.7% |

### Планируемое состояние

- **Папок источников:** 60
- **Средний размер папки:** ~250 JSON entities
- **Максимальный размер:** MM (~444 entities)
- **Минимальный размер:** Зависит от источника

## Совместимость

### Обратная совместимость

**Критически:** Текущая структура (`/data/`, `/img/`) **сохраняется** для обратной совместимости:

1. **Старые данные:** `/data/` не удаляется
2. **Старые изображения:** `/img/` не удаляется
3. **Новые данные:** `/data_rework/` создается параллельно
4. **Постепенный переход:** Frontend обновляется для поддержки обеих структур

### Migration path

1. **Этап 1:** Создание `/data_rework/` структуры
2. **Этап 2:** Валидация новой структуры
3. **Этап 3:** Обновление DataLoader для поддержки обеих структур
4. **Этап 4:** Тестирование с `/data_rework/`
5. **Этап 5:** Деплой новой структуры
6. **Этап 6:** Удаление старой структуры (опционально)

## Связанные документы

- **[docs/coordination.md](coordination.md)** - Главная координация
- **[docs/cross-source.md](cross-source.md)** - Cross-source references (431 строка)
- **[docs/images.md](images.md)** - Image reference system (807 строк)
- **[docs/fluff.md](fluff.md)** - Fluff контент (743 строки)
- **[docs/data-validation.md](data-validation.md)** - Data integrity validation
- **[docs/tags.md](tags.md)** - Tag system

## Изменения

### v1.0 (2025-01-18)

- Первоначальная версия документации
- Определена структура папок
- Описан формат файлов
- Созданы примеры для основных источников
- Документированы ограничения

---

**Документ статус:** Planning (ПЛАНИРОВАНИЕ)

**Следующие шаги:**
1. Создание Python скриптов реструктуризации (TODO.MD секция 3)
2. Валидация новой структуры (TODO.MD секция 4)
3. Создание инструкции по запуску (TODO.MD секция 5)
