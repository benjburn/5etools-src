# Модуль обработки Fluff

## Обзор

Система fluff в 5etools обеспечивает хранение и отображение narrative/descriptive контента, отделенного от механических данных. Fluff включает lore, описания, изображения и другой flavor контент.

## Основные концепции

### 1. Что такое Fluff?

**Fluff** - это narrative контент, отделенный от механики:
- **Lore и описания** существ, предметов, классов и т.д.
- **Изображения** - портреты, карты, иллюстрации
- **Backstory** - предыстории и 背景
- **Flavor text** - описательные тексты

**Contrast с "Stats":**
- **Stats**: механические данные (HP, AC, damage, dice rolls)
- **Fluff**: narrative данные (lore, описания, изображения)

### 2. Структура Fluff-файлов

**Именование файлов:**
```
data/{category}/fluff-{category}-{source}.json
```

**Примеры:**
- `data/bestiary/fluff-bestiary-mm.json` - Monster Manual fluff
- `data/bestiary/fluff-bestiary-xphb.json` - 2024 Monster Manual fluff
- `data/class/fluff-class-phb.json` - Player's Handbook class fluff
- `data/items/fluff-items-phb.json` - Item fluff

### 3. Структура JSON fluff-файла

**Общая структура:**
```javascript
{
  "_meta": {
    "internalCopies": ["monsterFluff"]
  },
  "monsterFluff": [
    {
      "name": "Aarakocra",
      "source": "MM",
      "entries": [
        {
          "type": "entries",
          "entries": [
            "Aarakocra range the Howling Gyre, an endless storm of mighty winds...",
            {
              "type": "entries",
              "name": "Enemies of Elemental Evil",
              "entries": [
                "In service to the Wind Dukes of Aaqa, aarakocra scout the planes...",
                // ...
              ]
            },
            {
              "type": "inset",
              "name": "Summoning Air Elementals",
              "entries": [
                "Five aarakocra within 30 feet of each other can magically summon..."
              ]
            }
          ]
        }
      ],
      "images": [
        {
          "type": "image",
          "href": {
            "type": "internal",
            "path": "bestiary/MM/Aarakocra.webp"
          }
        }
      ]
    }
  ]
}
```

**Fluff entry поля:**
- `name` - Имя entity
- `source` - Source код (MM, PHB, XPHB и т.д.)
- `entries` - Массив narrative entries (поддерживает весь entry syntax)
- `images` - Массив изображений (опционально)

**Типы entries во fluff:**
- `type: "entries"` - Обычный текстовый блок
- `type: "inset"` - Выделенный inset блок
- `type: "image"` - Изображения
- И любые другие типы entries из основной системы

### 4. Fluff Index

**fluff-index.json** - маппинг source на файл:
```javascript
{
  "MM": "fluff-bestiary-mm.json",
  "XPHB": "fluff-bestiary-xphb.json",
  "PHB": "fluff-class-phb.json",
  "DMG": "fluff-class-dmg.json",
  // ...
}
```

**Использование:**
```javascript
// DataLoader использует index для загрузки правильного файла
const fluff = await DataLoader.pCacheAndGet(
  "monsterFluff",
  "MM",
  "aarakocra%MM"
);
```

### 5. DataLoader.pCacheAndGet() (utils-dataloader.js:2085-2107)

**Основная функция загрузки:**

```javascript
static async pCacheAndGet (page, source, hash, {isCopy = false, isRequired = false, isSilent = false, lockToken2} = {}) {
  // 1. Проверка кэша
  const fromCache = this.getFromCache(page, source, hash, {isCopy, _isReturnSentinel: true});
  if (fromCache === _DataLoaderConst.ENTITY_NULL)
    return this._getVerifiedRequiredEntity({pageClean: page, sourceClean: source, hashClean: hash, ent: null, isRequired});
  if (fromCache) return fromCache;

  // 2. Clean inputs
  const {page: pageClean, source: sourceClean, hash: hashClean} =
    _DataLoaderInternalUtil.getCleanPageSourceHash({page, source, hash});

  // 3. Проверка доступности страницы
  if (this._PAGES_NO_CONTENT.has(pageClean))
    return this._getVerifiedRequiredEntity({pageClean, sourceClean, hashClean, ent: null, isRequired});

  // 4. Получение data loader
  const dataLoader = this._pCache_getDataTypeLoader({pageClean, isSilent});
  if (!dataLoader)
    return this._getVerifiedRequiredEntity({pageClean, sourceClean, hashClean, ent: null, isRequired});

  // 5. Preload prerelease/homebrew если необходимо
  const isUnavailablePrerelease = await this._PrereleasePreloader._pPreloadMissing({parent: this, sourceClean});
  if (isUnavailablePrerelease)
    return this._getVerifiedRequiredEntity({pageClean, sourceClean, hashClean, ent: null, isRequired});

  const isUnavailableBrew = await this._BrewPreloader._pPreloadMissing({parent: this, sourceClean});
  if (isUnavailableBrew)
    return this._getVerifiedRequiredEntity({pageClean, sourceClean, hashClean, ent: null, isRequired});

  // 6. Загрузка данных
  const {siteData = null, prereleaseData = null, brewData = null} =
    await this._pCacheAndGet_getCacheMeta({pageClean, sourceClean, dataLoader});

  await this._pCacheAndGet_processCacheMeta({dataLoader, siteData, prereleaseData, brewData, lockToken2});

  // 7. Возврат из кэша
  return this.getFromCache(page, source, hash, {isCopy, isRequired, _isInsertSentinelOnMiss: true});
}
```

**Fluff-specific page:**
```javascript
// fluff страницы имеют префикс "fluff"
_DataLoaderInternalUtil.getCleanPageFluff({page}) {
  return `${this.getCleanPage({page})}fluff`;
}

// Примеры:
// "monster" → "monsterfluff"
// "item" → "itemfluff"
```

### 6. Renderer.utils.pGetFluff() (render.js:3687-3699)

**Главная функция получения fluff:**

```javascript
static async pGetFluff ({entity, pFnPostProcess, fluffProp, lockToken2 = null} = {}) {
  // 1. Проверка predefined fluff (в entity.fluff)
  const predefinedFluff = await Renderer.utils.pGetPredefinedFluff(entity, fluffProp, {lockToken2});
  if (predefinedFluff) {
    if (pFnPostProcess) return pFnPostProcess(predefinedFluff);
    return predefinedFluff;
  }

  // 2. Проверка implicit fluff (hasFluff/hasFluffImages флаги)
  const fluff = await Renderer.utils._pGetImplicitFluff({entity, fluffProp, lockToken2});
  if (!fluff) return null;

  // 3. Post-processing (если указан)
  if (pFnPostProcess) return pFnPostProcess(fluff);
  return fluff;
}
```

**Параметры:**
- `entity` - Entity object (monster, item, и т.д.)
- `pFnPostProcess` - Опциональная функция для post-processing
- `fluffProp` - Fluff property ("monsterFluff", "itemFluff", etc.)
- `lockToken2` - Lock token для конкурентной загрузки

### 7. pGetPredefinedFluff() - Inline Fluff (render.js:3590-3647)

**Fluff, встроенный непосредственно в entity:**

```javascript
static async pGetPredefinedFluff (entry, fluffProp, {lockToken2 = null} = {}) {
  // Если нет inline fluff → return null
  if (!entry.fluff) return null;

  const mappedProp = `_${fluffProp}`;
  const mappedPropAppend = `_append${fluffProp.uppercaseFirst()}`;
  const fluff = {};

  const assignPropsIfExist = (fromObj, ...props) => {
    props.forEach(prop => {
      if (fromObj[prop]) fluff[prop] = fromObj[prop];
    });
  };

  // 1. Копирование базовых полей из entry.fluff
  assignPropsIfExist(entry.fluff, "name", "type", "entries", "images");

  // 2. Загрузка referenced fluff (_monsterFluff)
  if (entry.fluff[mappedProp]) {
    const fromList = await DataLoader.pCacheAndGet(
      fluffProp,
      SourceUtil.getEntitySource(entry),
      UrlUtil.URL_TO_HASH_BUILDER[fluffProp](entry.fluff[mappedProp]),
      {
        lockToken2,
        isCopy: true,
      },
    );
    if (fromList) {
      assignPropsIfExist(fromList, "name", "type", "entries", "images");
    }
  }

  // 3. Загрузка append fluff (_appendMonsterFluff)
  if (entry.fluff[mappedPropAppend]) {
    const fromList = await DataLoader.pCacheAndGet(
      fluffProp,
      SourceUtil.getEntitySource(entry),
      UrlUtil.URL_TO_HASH_BUILDER[fluffProp](entry.fluff[mappedPropAppend]),
      {
        lockToken2,
      },
    );
    if (fromList) {
      // Append entries
      if (fromList.entries) {
        fluff.entries = MiscUtil.copyFast(fluff.entries || []);
        fluff.entries.push(...MiscUtil.copyFast(fromList.entries));
      }
      // Append images
      if (fromList.images) {
        fluff.images = MiscUtil.copyFast(fluff.images || []);
        fluff.images.push(...MiscUtil.copyFast(fromList.images));
      }
    }
  }

  // 4. Установка name/source если есть контент
  if (fluff.entries?.length || fluff.images?.length) {
    fluff.name = entry.name;
    fluff.source = SourceUtil.getEntitySource(entry);
  }

  return fluff;
}
```

**Примеры inline fluff:**

```javascript
// Пример 1: Полностью inline fluff
{
  name: "Custom Monster",
  source: "Homebrew",
  fluff: {
    entries: [
      "This is a custom monster with inline fluff.",
      {
        type: "entries",
        name": "Lore",
        entries: ["More detailed lore here..."]
      }
    ],
    images: [
      {
        type: "image",
        href: {type: "internal", path: "bestiary/homebrew/monster.webp"}
      }
    ]
  }
}

// Пример 2: Reference на другой fluff
{
  name: "Goblin Boss",
  source: "MM",
  fluff: {
    _monsterFluff: {
      name: "Goblin",
      source: "MM"
    }
  }
}
// → Использует fluff из "Goblin" entry

// Пример 3: Append fluff
{
  name: "Variant Goblin",
  source: "Homebrew",
  fluff: {
    _monsterFluff: {
      name: "Goblin",
      source: "MM"
    },
    _appendMonsterFluff: {
      name: "VariantGoblin",
      source: "Homebrew"
    },
    entries: [
      "Additional variant-specific lore..."
    ]
  }
}
// → Базовый goblin fluff + variant-specific additions
```

### 8. _pGetImplicitFluff() - External Fluff (render.js:3649-3671)

**Fluff, загружаемый из внешних файлов:**

```javascript
static async _pGetImplicitFluff ({entity, fluffProp, lockToken2} = {}) {
  // 1. Проверка флагов
  if (
    !entity.hasFluff
    && !entity.hasFluffImages
    && (!entity._versionBase_isVersion ||
        (!entity._versionBase_hasFluff && !entity._versionBase_hasFluffImages))
  ) return null;

  // 2. Загрузка fluff entity
  const fluffEntity = await DataLoader.pCacheAndGet(
    fluffProp,
    SourceUtil.getEntitySource(entity),
    UrlUtil.URL_TO_HASH_BUILDER[fluffProp](entity),
    {lockToken2}
  );

  if (fluffEntity) return fluffEntity;

  // 3. Fallback на base version (для 2024 remasters)
  if (entity._versionBase_isVersion &&
      (entity._versionBase_hasFluff || entity._versionBase_hasFluffImages)) {
    return DataLoader.pCacheAndGet(
      fluffProp,
      SourceUtil.getEntitySource(entity),
      entity._versionBase_hash,
      {
        lockToken2,
      },
    );
  }

  return null;
}
```

**Флаги entity:**
- `hasFluff: true` - Entity имеет fluff с entries
- `hasFluffImages: true` - Entity имеет fluff с images
- `_versionBase_isVersion: true` - Это 2024 версия
- `_versionBase_hasFluff: true` - Base версия имеет fluff
- `_versionBase_hash: "..."` - Hash base версии

### 9. pBuildFluffTab() - Рендеринг Fluff Tab (render.js:3710-3724)

**Создание fluff tab в UI:**

```javascript
static async pBuildFluffTab ({
  isImageTab,
  $content,
  wrpContent,
  entity,
  $headerControls,
  wrpHeaderControls,
  pFnGetFluff,
  page
} = {}) {
  // Validation
  if ($content && wrpContent)
    throw new Error(`Only one of "$content" and "wrpContent" may be specified!`);
  if ($headerControls && wrpHeaderControls)
    throw new Error(`Only one of "$headerControls" and "wrpHeaderControls" may be specified!`);

  // jQuery wrapper
  if (wrpContent) $content = $(wrpContent);
  if (wrpHeaderControls) $headerControls = $(wrpHeaderControls);

  // Header
  $content.append(Renderer.utils.getBorderTr());
  $content.append(Renderer.utils.getNameTr(entity, {controlRhs: $headerControls, asJquery: true, page}));
  const $td = $(`<td colspan="6" class="pb-3"></td>`);
  $$`<tr>${$td}</tr>`.appendTo($content);
  $content.append(Renderer.utils.getBorderTr());

  // Get fluff
  const fluff = MiscUtil.copyFast((await pFnGetFluff(entity)) || {});

  // Text tab
  if (!isImageTab) {
    fluff.entries = fluff.entries || [Renderer.utils.HTML_NO_INFO];

    $td.append(
      fluff.entries.map(ent => Renderer.get().render(ent)).join("")
    );
  }
  // Images tab
  else {
    const images = fluff.images || [];
    if (!images.length) {
      $td.append(Renderer.utils.HTML_NO_IMAGES);
    } else {
      // Render gallery
      const $wrpGallery = $(`<div class="rd__wrp-gallery"></div>`).appendTo($td);

      images.forEach(img => {
        const $wrpImg = $(`<div class="rd__wrp-gallery-image"></div>`).appendTo($wrpGallery);

        $wrpImg.append(Renderer.get().render(img));

        if (img.title) {
          const $title = $(`<div class="rd__image-title"></div>`).appendTo($wrpImg);
          $title.append(`<div class="rd__image-title-inner">${img.title}</div>`);

          if (img.credit) {
            $title.append(`<div class="rd__image-credit ve-muted">
              <span class="glyphicon glyphicon-pencil" title="Art Credit"></span>
              ${img.credit}
            </div>`);
          }
        }
      });
    }
  }
}
```

### 10. Entity-specific Fluff Getters

**Renderer.monster.pGetFluff() (render.js:11279-11285):**
```javascript
static pGetFluff (mon) {
  return Renderer.utils.pGetFluff({
    entity: mon,
    pFnPostProcess: Renderer.monster.postProcessFluff.bind(Renderer.monster, mon),
    fluffProp: "monsterFluff",
  });
}
```

**Renderer.item.pGetFluff() (render.js:13056-13075):**
```javascript
static async pGetFluff (item) {
  const fluffItem = await Renderer.utils.pGetFluff({
    entity: item,
    fluffProp: "itemFluff",
  });
  if (fluffItem) return fluffItem;

  // Fallback для variant items
  if (!item._variantName) return null;

  // Inherit generic variant fluff
  return Renderer.utils.pGetFluff({
    entity: {
      name: item._variantName,
      source: item.source,
      hasFluff: item.hasFluff,
      hasFluffImages: item.hasFluffImages,
    },
    fluffProp: "itemFluff",
  });
}
```

**Renderer.utils.pGetProxyFluff() (render.js:3673-3684):**
```javascript
static async pGetProxyFluff ({entity, prop = null}) {
  prop ||= entity?.__prop;
  switch (prop) {
    case "monster":
      return Renderer.monster.pGetFluff(entity);
    case "item":
    case "magivariant":
    case "baseitem":
      return Renderer.item.pGetFluff(entity);
    default:
      return Renderer.utils.pGetFluff({entity, fluffProp: `${prop}Fluff`});
  }
}
```

### 11. URL_TO_HASH_BUILDER для Fluff

**Определение в utils.js:**
```javascript
UrlUtil.URL_TO_HASH_BUILDER = {};

// Generic hash builder
UrlUtil.URL_TO_HASH_GENERIC = it =>
  UrlUtil.encodeForHash([it.name, SourceUtil.getEntitySource(it)]);

// Page-specific builders
UrlUtil.URL_TO_HASH_BUILDER[UrlUtil.PG_BESTIARY] = UrlUtil.URL_TO_HASH_GENERIC;
UrlUtil.URL_TO_HASH_BUILDER[UrlUtil.PG_SPELLS] = UrlUtil.URL_TO_HASH_GENERIC;
UrlUtil.URL_TO_HASH_BUILDER[UrlUtil.PG_BACKGROUNDS] = UrlUtil.URL_TO_HASH_GENERIC;
UrlUtil.URL_TO_HASH_BUILDER[UrlUtil.PG_ITEMS] = it =>
  UrlUtil.encodeArrayForHash(it.name, SourceUtil.getEntitySource(it));
UrlUtil.URL_TO_HASH_BUILDER[UrlUtil.PG_CLASSES] = UrlUtil.URL_TO_HASH_GENERIC;
// и т.д.
```

**Использование для fluff:**
```javascript
// Monster fluff
const hash = UrlUtil.URL_TO_HASH_BUILDER["monsterFluff"](monster);
// → "aarakocra%MM"

const fluff = await DataLoader.pCacheAndGet(
  "monsterFluff",
  "MM",
  hash  // "aarakocra%MM"
);
```

### 12. Fluff Properties по категориям

**DataUtil properties (utils.js:6442):**
```javascript
static monsterFluff = class extends _DataUtilPropConfigMultiSource { /* ... */ };
static itemFluff = class extends _DataUtilPropConfigMultiSource { /* ... */ };
static classFluff = class extends _DataUtilPropConfigMultiSource { /* ... */ };
static subclassFluff = class extends _DataUtilPropConfigMultiSource { /* ... */ };
static raceFluff = class extends _DataUtilPropConfigMultiSource { /* ... */ };
static subraceFluff = class extends _DataUtilPropConfigMultiSource { /* ... */ };
static backgroundFluff = class extends _DataUtilPropConfigMultiSource { /* ... */ };
static featFluff = class extends _DataUtilPropConfigMultiSource { /* ... */ };
static optionalFeatureFluff = class extends _DataUtilPropConfigMultiSource { /* ... */ };
static psionicFluff = class extends _DataUtilPropConfigMultiSource { /* ... */ };
static boonFluff = class extends _DataUtilPropConfigMultiSource { /* ... */ };
static deckFluff = class extends _DataUtilPropConfigMultiSource { /* ... */ };
static cardFluff = class extends _DataUtilPropConfigMultiSource { /* ... */ };
// и более 40 других типов
```

## Примеры использования

### 1. Простой monster с external fluff

**Bestiary data:**
```javascript
{
  "name": "Goblin",
  "source": "MM",
  "hasFluff": true,
  "hasFluffImages": true,
  // ...stats...
}
```

**Fluff file (fluff-bestiary-mm.json):**
```javascript
{
  "_meta": {"internalCopies": ["monsterFluff"]},
  "monsterFluff": [
    {
      "name": "Goblin",
      "source": "MM",
      "entries": [
        "Goblins are small, black-hearted humanoids that lair in despoiled dungeons and other squalid places...",
        {
          "type": "entries",
          "name": "Dwellers of the Dark",
          "entries": [
            "Goblins are known to dwell in dark, cramped places..."
          ]
        }
      ],
      "images": [
        {
          "type": "image",
          "href": {
            "type": "internal",
            "path": "bestiary/MM/Goblin.webp"
          }
        }
      ]
    }
  ]
}
```

### 2. Monster с inline fluff

```javascript
{
  "name": "Custom Monster",
  "source": "Homebrew",
  "fluff": {
    "entries": [
      "This monster is completely custom with inline fluff.",
      "No separate fluff file required."
    ],
    "images": [
      {
        "type": "image",
        "href": {
          "type": "internal",
          "path": "bestiary/homebrew/custom.webp"
        },
        "title": "Custom Monster",
        "credit": "{@artist Artist Name}"
      }
    ]
  },
  // ...stats...
}
```

### 3. Monster с referenced fluff

```javascript
{
  "name": "Goblin Boss",
  "source": "MM",
  "fluff": {
    "_monsterFluff": {
      "name": "Goblin",
      "source": "MM"
    }
  },
  // ...stats...
}
// → Использует fluff из "Goblin" entry
```

### 4. Monster с append fluff

```javascript
{
  "name": "Variant Goblin",
  "source": "Homebrew",
  "fluff": {
    "_monsterFluff": {
      "name": "Goblin",
      "source": "MM"
    },
    "_appendMonsterFluff": {
      "name": "VariantGoblin",
      "source": "Homebrew"
    },
    "entries": [
      "This variant has additional lore specific to it."
    ]
  },
  // ...stats...
}
// → Goblin fluff + additional entries
```

### 5. Item с variant fluff

```javascript
{
  "name": "+1 Longsword",
  "source": "Homebrew",
  "_variantName": "Longsword",
  "hasFluff": true,
  "fluff": {
    "entries": [
      "This magic weapon is a variant of the generic longsword."
    ]
  }
  // Falls back to "Longsword" fluff if not found
}
```

## Ключевые файлы

- `data/bestiary/fluff-*.json` - Monster fluff (90+ файлов)
- `data/class/fluff-*.json` - Class fluff
- `data/items/fluff-*.json` - Item fluff
- `data/races/fluff-*.json` - Race fluff
- `data/backgrounds/fluff-*.json` - Background fluff
- `js/render.js:3590-3647` - pGetPredefinedFluff()
- `js/render.js:3649-3671` - _pGetImplicitFluff()
- `js/render.js:3673-3684` - pGetProxyFluff()
- `js/render.js:3687-3699` - pGetFluff()
- `js/render.js:3710-3724` - pBuildFluffTab()
- `js/render.js:11279-11285` - Renderer.monster.pGetFluff()
- `js/render.js:13056-13075` - Renderer.item.pGetFluff()
- `js/utils-dataloader.js:2085-2107` - DataLoader.pCacheAndGet()
- `js/utils.js:5048` - PAGE_TO_FLUFF mappings
- `js/utils.js:6442+` - Fluff property classes

## Архитектурные паттерны

1. **Separation of Concerns** - Fluff отделен от mechanical stats
2. **External Files** - Fluff хранится в отдельных JSON файлах
3. **Lazy Loading** - Fluff загружается по требованию через DataLoader
4. **Inline Support** - Fluff может быть встроен непосредственно в entity
5. **Reference System** - `_fluffProp` для referencing других fluff
6. **Append System** - `_appendFluffProp` для расширения base fluff
7. **Dual Mode** - Text tab и Images tab в UI
8. **Cache-First** - DataLoader кэширует загруженный fluff
9. **Version Fallback** - 2024 версии могут использовать 2014 fluff
10. **Post-Processing** - Entity-specific post-processors для модификации fluff
11. **Hash-Based Lookup** - URL hash для идентификации fluff
12. **Generic Builder** - URL_TO_HASH_BUILDER для универсальных hash
13. **Prop-Based Routing** - `__prop` для автоматического выбора fluff type
14. **Flag-Based Detection** - hasFluff/hasFluffImages для оптимизации
15. **Multi-Source Support** - Site, prerelease, homebrew fluff

## Статистика

- **90+ fluff файлов** для bestiary
- **40+ типов fluff** (monsterFluff, itemFluff, и т.д.)
- **2 режима tabs**: Text, Images
- **3 типа fluff**: inline, referenced, implicit
- **2 флага**: hasFluff, hasFluffImages
- **1 fallback**: _versionBase для 2024 remasters
- **3 метода загрузки**: inline, reference, append
- **DataLoader cache** для всех загруженных fluff
- **URL hash based** lookup для каждого fluff entry
